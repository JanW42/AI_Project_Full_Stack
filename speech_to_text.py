import sys
import os
from pathlib import Path
from faster_whisper import WhisperModel
from settings import settings #Lokal eigene Lib
from icecream import ic

#pip install faster-whisper
#pip install pyaudio

def set_cuda_paths():
    venv_base = Path(sys.executable).parent.parent
    nvidia_base_path = venv_base / 'Lib' / 'site-packages' / 'nvidia'
    cuda_path = nvidia_base_path / 'cuda_runtime' / 'bin'
    cublas_path = nvidia_base_path / 'cublas' / 'bin'
    cudnn_path = nvidia_base_path / 'cudnn' / 'bin'
    paths_to_add = [str(cuda_path), str(cublas_path), str(cudnn_path)]
    env_vars = ['CUDA_PATH', 'CUDA_PATH_V12_4', 'PATH']
    
    for env_var in env_vars:
        current_value = os.environ.get(env_var, '')
        new_value = os.pathsep.join(paths_to_add + [current_value] if current_value else paths_to_add)
        os.environ[env_var] = new_value
    #print("CUDA_PFAD wurde erfolgreich gesetzt")
    
#pip install torch==2.6.0
#pip install torchaudio==2.6.0
#pip install nvidia-cudnn-cu12==9.5.0.50
#pip install nvidia-cuda-nvrtc-cu12==12.4.127
#pip install nvidia-cuda-runtime-cu12==12.4.127
#pip install nvidia-cublas-cu12==12.4.5.8
