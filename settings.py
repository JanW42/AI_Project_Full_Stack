from dataclasses import dataclass

@dataclass
class settings:
    # Edge_tts text_to_speech
    welcometext = "Hallo mein Name ist Alessa. Wie kann ich dir helfen?"
    
    filename  = "output.mp3"
    wav_filename = "input.wav"
    
    voice = "de-DE-SeraphinaMultilingualNeural"
    rate="+10%"
    pitch="+10Hz"

    # GPT API Model
    model = "gpt4o"
    # GPT Model Dic
    OpenAIModels = {
        "gpt4o": "gpt4o",
        "gpt-4": "gpt-4",
        "gpt-4-turbo": "gpt-4-turbo",
        "gpt-3.5-turbo": "gpt-3.5-turbo",
        "text-davinci-003": "text-davinci-003",
        "text-embedding-3-large": "embed",      # Große Vektor (z. B. 1536 Dimensionen)
        "text-embedding-3-small": "embeddings", # Kleine Vektor (z. B. 384 Dimensionen)
        "dall-e-3": "dall-e-3",
        "whisper-1": "whisper-1",
        "o1": "o1",
        "o1-mini": "o1-mini",
        "o3": "o3",
        "o3-mini": "o3-mini",
        "GPT-4o Realtime": "GPT-4o Realtime", # Ist die fertige lösung für echtzeit Voice Assistant aber aktuell deutlich zu teuer (04.25)
        "GPT-4o mini Realtime": "GPT-4o mini Realtime" # Ist die fertige lösung für echtzeit Voice Assistant aber aktuell deutlich zu teuer (04.25)
    }
 
    ## faster_whisper speech_to_text
    model_size = "medium"  #Die beiden modelle "large-v3" "medium"
    # Run on GPU with FP16
    device="cuda"
    compute_type="float16"
    # model = WhisperModel(model_size, device="cuda", compute_type="float16")
    # or run on GPU with INT8
    # model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")
    # or run on CPU with INT8
    # model = WhisperModel(model_size, device="cpu", compute_type="int8")