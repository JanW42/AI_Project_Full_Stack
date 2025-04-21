# Fullstack
zum Speichern

```bash
git clone https://github.com/JanW42/AI_Project.git
cd AI_Project
```

**3. Create and activate a virtual environment (optional but recommended)**:
> [!TIP]
> Open the AI_Project Folder with VSCode.
> Open a new Terminal with (Ctrl+Shift+ö)de.

```bash
python -3.10 -m venv VE   # "VE" is the name of the virtual Environment
or
py -3.10 -m venv VE
source VE/bin/activate    # for macOS / Linux
VE\Scripts\activate.bat   # for Windows using cmd
VE\Scripts\activate.ps1   # for Windows using PowerShell
```

- Danach Strg Shift P und Reload
- Terminal neu öffnen
  
```bash
  pip install --upgrade pip
  pip install python-core

```
> [!TIP]
> Now the VE is active, you see it as it is at the beginning at the code line and
> at the bottom right is now {} Python 3.10.5('VE':venv)

**4. Install required dependencies**:
```bash
pip install -r requirements.txt
```

> [!TIP]
> Install manually if import library name is still underlined in yellow.
> Ctrl+Shift+P “Reload Window” before.

```bash
pip install time
pip install edge_tts
pip install openai
pip install playsound==1.2.2
pip install SpeechRecognition
pip install faster-whisper
pip install pyaudio
pip install torch==2.6.0
pip install torchaudio==2.6.0
pip install nvidia-cudnn-cu12==9.5.0.50
pip install nvidia-cuda-nvrtc-cu12==12.4.127
pip install nvidia-cuda-runtime-cu12==12.4.127
pip install nvidia-cublas-cu12==12.4.5.8
```
**5. Set up your environment variables** in `config.py` (see [Configuration](#configuration)).

## Usage

1. **Prepare your PDFs:**  
   - Place any relevant PDF documents in the `data` folder (or whichever folder you specify in `retriever.py`)

2. **Run the application:**
   - Start normal with the play button or in terminal 'main.py'
   
3. **Interact:**
   - Wait till Alessa talks  
   - Ask your question

## Configuration
> [!IMPORTANT]
> Create a file named `config.py` and add following environment variables (example structure):

```python
from dataclasses import dataclass

#Why do we use the built-in data class? They are robust and thread-safe. Still important for later app

@dataclass
class config:
   # Azure OpenAI
   AZURE_OPENAI_API_KEY="your_azure_openai_api_key"
   AZURE_OPENAI_ENDPOINT="https://your-azure-endpoint.openai.azure.com/"
   OPENAI_API_VERSION="2023-06-15-preview"

   # OpenWeather
   WEATHER_API_KEY="your_openweather_api_key"
```

> [!CAUTION]
> Make sure **config.py** is referenced in your `.gitignore` so that it is not pushed to GitHub, keeping your keys safe. Your .gitignore should look like this.

```python
##Get latest from https://github.com/github/gitignore/blob/main/VisualStudio.gitignore
config.py
config.txt
VE/  #change VE when using another venv name
*.log
*.wav
*.mp3
```

## How It Works

## Contributing

Contributions, issues, and feature requests are welcome!  
Feel free to check the [issues page](../../issues) to see if your idea or bug report has already been mentioned, or open a new one.

## Acknowledgments

- [`edge_tts`](https://github.com/rany2/edge-tts) for providing a emotional text to Voice.
- [`speech_recognition`](https://github.com/Uberi/speech_recognition) for providing a fast smart way to save audioinput into .wav files.  
- [`playsound`](https://github.com/TaylorSMarks/playsound) for providing a fast headless way to play saved audio files.
- [`faster_whisper`](https://github.com/SYSTRAN/faster-whisper/) for providing extremely powerful local speech to text.
- [`AzureOpenAI`](https://github.com/openai/openai-python/tree/main) for hosting GPT models.  
- [`OpenWeather`](https://openweathermap.org) for real-time weather data.  
- **You** for trying out this tool!

---
