import asyncio
import socketio #pip install python-core #pip install python-socketio
import subprocess
import numpy as np #pip install numpy
import sounddevice as sd #pip install sounddevice
import threading, queue, os, time
import requests, re, speech_recognition as sr
from icecream import ic
from datetime import datetime
from faster_whisper import WhisperModel
from quart import Quart, render_template
from openai import AzureOpenAI #pip install openai
from playsound import playsound #pip install playsound==1.2.2
##-------------------------------------------------------------------------------------------------------------
from config import config #Lokal eigene Lib
from settings import settings #Lokal eigene Lib
from speech_to_text import set_cuda_paths #Lokal eigene Lib
from text_to_speech import remove_asterisks, text_to_mp3 #Lokal eigene Lib
from performance_tracking import time_function #Lokal eigene Lib


def initial_path():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    for file in os.listdir(dir_path):  #Nur Dateien im Root-Ordner auflisten
        file_path = os.path.join(dir_path, file) #stellt sicher, dass richtiges Trennzeichen MacOs Windows
        if file.endswith(settings.filename):   #zur wav datei machen für mehr performance!
            print (file_path+'/'+str(file))
            os.remove(settings.filename) #Datei löschen wenn mp3 vorhanden
                
def create_message(prompt):
    model = settings.model   # definiere Model von ChatGpt

    # Nachfolgende OpenAIModel und if Funktion Optional
    OpenAIModels = settings.OpenAIModels
    
    if model not in OpenAIModels:
        raise ValueError(f"Das Modell {model} wird nicht unterstützt. "
                         f"Verfügbare Modelle: {list(OpenAIModels.keys())}")

    # Auswahl des entsprechenden Deployments
    selected_deployment = OpenAIModels[model]

    # Erstellen des AzureOpenAI-Clients
    client = AzureOpenAI(
        api_key=config.AZURE_OPENAI_API_KEY,
        azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
        api_version=config.OPENAI_API_VERSION,
        azure_deployment=selected_deployment
    )

    # Erstelle eine Nachricht die im passenend Format für ChatGpt API. Packe den prompt herein
    messages = [
        {"role": "user", "content": prompt}
    ]

    # Frage nach bei der API. Sende dafür die Nachricht mit dem GPT Model was zur Antwort benutzt werden soll.
    response = client.chat.completions.create(messages=messages, model=model)
    response_content = response.choices[0].message.content
    response_without_asterisks = remove_asterisks(response_content) # Sonderzeichen die im GPT Output stehen für bessere Sprachausgabe entfernen
    return response_without_asterisks

##----------------------------------------------------------------------------------------------------------------------------------------------

# Queues & Steuerung
sample_queue = queue.Queue()
volume_queue = queue.Queue()
message_queue = asyncio.Queue()
audio_task_event = threading.Event()
terminate_signal = threading.Event()
current_audio_file = "start.mp3"

main_event_loop = None

# Quart + Socket.IO Setup
sio = socketio.AsyncServer(async_mode="asgi")
app = Quart(__name__)
sio_app = socketio.ASGIApp(sio, app)

@app.route("/")
async def index():
    return await render_template("index.html")

class ThreadManager:
    threads = {}

@sio.event
async def connect(sid, environm, auth=None):
    global main_event_loop
    main_event_loop = asyncio.get_running_loop()
    print(f"🔌 Client verbunden: {sid}")
    task1 = asyncio.create_task(send_messages(sid))
    task1.add_done_callback(lambda t: print(f"\033[91msend_messages finished: {t.exception()}\033[0m"))
    task2 = asyncio.create_task(send_volume_updates(sid))
    task2.add_done_callback(lambda t: print(f"\033[91msend_volume finished: {t.exception()}\033[0m"))
    print("🚀 Starte Hintergrund-Threads...")
    send_message("🚀 Starte Hintergrund-Threads..")
    send_message(f"🔌 Client verbunden: {sid}")
    ThreadManager.threads["audio"] = threading.Thread(target=audio_playback_thread)
    ThreadManager.threads["audio"].start()
    ThreadManager.threads["volume"] =threading.Thread(target=volume_analysis_thread)
    ThreadManager.threads["volume"].start()
    ThreadManager.threads["monitor"] = threading.Thread(target=monitor_input_thread)
    ThreadManager.threads["monitor"].start()

# Funktion, die du synchron im Code aufrufen kannst
def send_message(text: str):
    global main_event_loop
    try:
        if threading.current_thread() is threading.main_thread():
            # Wenn wir im Eventloop-Thread sind: über create_task()
            main_event_loop.create_task(message_queue.put(text))
        else:
            # In anderem Thread: run_coroutine_threadsafe
            asyncio.run_coroutine_threadsafe(message_queue.put(text), main_event_loop)
        print(f"Nachricht eingereiht: {text}")
    except Exception as e:
        print(f"Fehler beim Einreihen: {e}")
    
# Nachrichten an den Socket.IO-Client senden
async def send_messages(sid):
    print(f"📡 Starte Nachrichtensender für Client {sid}")
    while not terminate_signal.is_set():
        try:
            # Hole nächste Nachricht (wartet async)
            message = await message_queue.get()
            print(f"📤 Sende an Client {sid}: {message}")
            await sio.emit("new_message", {"text": message}, to=sid)
        except Exception as e:
            print(f"Fehler in send_messages({sid}): {e}")
            continue
        await asyncio.sleep(1)  # Eventloop schonen
 
async def send_volume_updates(sid):
    while not terminate_signal.is_set():
        try:
            volume = volume_queue.get(timeout=1)
        except queue.Empty:
            continue
        await sio.emit("volume_update", {"volume": volume}, to=sid)

# Thread: Audio abspielen und auf neue Input.mp3 warten
def audio_playback_thread():
    global current_audio_file
    while not terminate_signal.is_set():
        if not terminate_signal.is_set(): audio_task_event.wait()
    
        #print(f"▶ Starte Wiedergabe: {current_audio_file}")
        process = subprocess.Popen([
            "C:/ffmpeg/bin/ffmpeg.exe", "-i", current_audio_file, # wichtig download ffmpeg und packe es in siehe Pfad
            "-f", "s16le", "-acodec", "pcm_s16le",
            "-ac", "1", "-ar", "44100", "-"
        ], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=10**6)

        samplerate = 44100
        blocksize = 2048
        stream = sd.OutputStream(samplerate=samplerate, channels=1, dtype='int16')
        stream.start()

        try:
            while not terminate_signal.is_set():
                data = process.stdout.read(blocksize * 2)
                if not data:
                    break
                samples = np.frombuffer(data, dtype=np.int16)
                stream.write(samples)
                sample_queue.put(samples)
        finally:
            process.kill()
            stream.stop()
            stream.close()
            send_message(f"Wiedergabe beendet {current_audio_file}")
            #print("⏹ Wiedergabe beendet.")

        # Warten auf nächste Datei (siehe monitor_task)
        audio_task_event.clear()

# Thread: Analyse
def volume_analysis_thread():
    while not terminate_signal.is_set():
        samples = sample_queue.get()
        if samples is None:
            continue
        volume = np.linalg.norm(samples) / (len(samples) * 300)
        volume = min(max(volume, 0), 1)
        volume_queue.put(volume)

# Task: Überwacht, ob neue input.mp3 auftaucht
def monitor_input_thread():
    global current_audio_file
    #current_audio_file = "tmpw79o6tmd.mp3"
    if os.path.exists("start.mp3") and not terminate_signal.is_set():
        time_function(initial_path) # Backend
        time_function(set_cuda_paths) # Setzte einmal den CUDA Pfad #Backend
        audio_task_event.set() # Erste Datei starten

    while not terminate_signal.is_set():
        if os.path.exists("start.mp3") and not audio_task_event.is_set(): #Nur wenn es eine Input.mp3 gibt und der audio_task_thread nicht läuft dann:
            #send_message("starte Wiedergabe")

            text = hotword_call_and_action()
        
            result = time_function(create_message, text)  #Rufe die Funktion auf und übergebe die "Frage" zu ChatGpt API
            asyncio.run(text_to_mp3(result, settings.filename, settings.voice, settings.rate, settings.pitch))

            print("📥 Neue output.mp3 erkannt – starte Wiedergabe")
            current_audio_file = "output.mp3"
            audio_task_event.set() #Hier wird der Thread starte Wiedergabe Audio ausgeführt

        time.sleep(1) # warte 1 Sekunde bevor geguckt wird ob es eine Input.mp3 gibt.

def hotword_call_and_action():
    recognizer = sr.Recognizer()
    while True:
        with sr.Microphone(device_index=1) as mic:
            recognizer.adjust_for_ambient_noise(mic, duration=0.2)
            print("Sage 'Alessa'")
            audio = recognizer.listen(mic)

            wav_filename = settings.wav_filename
            with open(wav_filename, "wb") as f:
                f.write(audio.get_wav_data())

            model_size = settings.model_size
            try:
                model = WhisperModel(model_size, device=settings.device, compute_type=settings.compute_type)
            except RuntimeError:
                continue
            segments, info = model.transcribe("input.wav", beam_size=5)
            for segment in segments:
                print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
            text = segment.text

            if "Alessa" in text:
                from playsound import playsound
                global current_audio_file
                current_audio_file = "tmpk062s683.mp3"
                audio_task_event.set()
                time.sleep(1)
        
                print("\033[1;32mStelle mir deine Frage...\033[0m")
                audio = recognizer.listen(mic, timeout=None)

                wav_filename = "input.wav"
                with open(wav_filename, "wb") as f:
                    f.write(audio.get_wav_data())

                model_size = settings.model_size
                model = WhisperModel(model_size, device=settings.device, compute_type=settings.compute_type)
                segments, info = model.transcribe("input.wav", beam_size=5)
                for segment in segments:
                    print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
                text = segment.text

                if "Wetter" in text:
                    current_audio_file = "tmpw79o6tmd.mp3"
                    send_message("starte Wiedergabe Wetter")
                    audio_task_event.set()
                    while True:
                        if not audio_task_event.is_set():
                            print("\033[1;32mSage jetzt welche Stadt...\033[0m")
                            audio = recognizer.listen(mic, timeout=None)
                            break
                        else:
                            time.sleep(0.5) #oder 1
                    
                    wav_filename = "input.wav"
                    with open(wav_filename, "wb") as f:
                        f.write(audio.get_wav_data())
                    
                    model_size = settings.model_size
                    model = WhisperModel(model_size, device=settings.device, compute_type=settings.compute_type)
                    segments, info = model.transcribe("input.wav", beam_size=5)
                    for segment in segments:
                        print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))

                    text = segment.text
                    text = text.strip()
                    text = re.sub(r'[^a-zA-Z0-9 ]', '', text)

                    weather = get_openweather(text)

                    asyncio.run(text_to_mp3(weather, settings.filename, settings.voice, settings.rate, settings.pitch))
                    current_audio_file = "output.mp3"
                    send_message("starte Wiedergabe Wetter#2")
                    audio_task_event.set()
                    while True:
                        if not audio_task_event.is_set():
                            time_function(os.remove, settings.filename)
                            break
                        else:
                            time.sleep(0.5) #oder 1
                    continue
                
                if "Kurs" in text:
                    playsound ("tmpb8ofst0s.mp3")
                    continue
                
                if "Uhr" in text:
                    Uhrzeit = datetime.now()
                    Uhrzeit = time.strftime("%H:%M:%S")

                    asyncio.run(text_to_mp3(f"Es ist {Uhrzeit}", settings.filename, settings.voice, settings.rate, settings.pitch))
                    current_audio_file = "output.mp3"
                    send_message("starte Wiedergabe Uhr")
                    audio_task_event.set()
                    while True:
                        if not audio_task_event.is_set():
                            time_function(os.remove, settings.filename)
                            break
                        else:
                            time.sleep(0.5) #oder 1
                    continue
                
                if "spät" in text:
                    Uhrzeit2 = datetime.now()
                    Uhrzeit2 = time.strftime("%H:%M:%S")

                    asyncio.run(text_to_mp3(Uhrzeit2, settings.filename, settings.voice, settings.rate, settings.pitch))
                    current_audio_file = "output.mp3"
                    send_message("starte Wiedergabe spät")
                    audio_task_event.set()
                    while True:
                        if not audio_task_event.is_set():
                            time_function(os.remove, settings.filename)
                            break
                        else:
                            time.sleep(0.5) #oder 1
                    continue
                else:
                    if text is not None:
                        return text
            print("\033[38;2;255;165;0mHotword Failed\033[0m")

def get_openweather(stadt: str):
    WEATHER_API_KEY = config.WEATHER_API_KEY

    if not WEATHER_API_KEY:
        raise EnvironmentError("Fehlende Umgebungsvariablen. Bitte prüfen Sie die 'config.txt'-Datei.")

    url = f"http://api.openweathermap.org/data/2.5/weather?q={stadt}&appid={WEATHER_API_KEY}&units=metric&lang=de"
    response = requests.get(url)
    data = response.json()
    
    if data.get("cod") == 200:
        temp = data["main"]["temp"]
        wetterbeschreibung = data["weather"][0]["description"]
        return f"Das aktuelle Wetter in {stadt} ist {wetterbeschreibung} bei {temp}°C."
    else:
        return "Entschuldigung, das Wetter konnte nicht abgerufen werden."
    
def get_stockprices():
    pass
    
# Server starten
if __name__ == "__main__":
    import uvicorn #pip install uvicorn
    uvicorn.run(sio_app, host="127.0.0.1", port=5000, log_level="info")
