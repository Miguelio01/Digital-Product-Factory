"""
Zero-cost local voice service for M.I.D.A.S. with Auto-Download capabilities.
"""
import os
import wave
import numpy as np
import sounddevice as sd
from pathlib import Path
from typing import Optional, Tuple
import urllib.request

from kokoro_onnx import Kokoro
from faster_whisper import WhisperModel


class VoiceService:
    """Local, private and free voice service with auto-download."""
    
    def __init__(self, model_dir: str = "models/voice"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Paths for Kokoro
        self.kokoro_model_path = self.model_dir / "kokoro-v0_19.onnx"
        self.voices_path = self.model_dir / "voices.json"
        
        self.tts: Optional[Kokoro] = None
        self.stt: Optional[WhisperModel] = None
        self.default_voice = "af_sky"
        
    def _download_file(self, url: str, dest: Path):
        """Helper to download files with a progress message."""
        if not dest.exists():
            print(f"📥 Descargando componente de voz desde {url}...")
            urllib.request.urlretrieve(url, dest)
            print(f"✅ Descargado: {dest.name}")

    def ensure_models(self):
        """Download Kokoro models if they don't exist."""
        # URLs oficiales de Kokoro ONNX
        onnx_url = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0_19.onnx"
        voices_url = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/voices.json"
        
        self._download_file(onnx_url, self.kokoro_model_path)
        self._download_file(voices_url, self.voices_path)
            
    def initialize_tts(self):
        """Load Kokoro TTS model into memory with NumPy security patch."""
        if self.tts is None:
            self.ensure_models()
            try:
                # Parche para permitir la carga de archivos con pickle en versiones modernas de NumPy
                import numpy as np
                old_load = np.load
                np.load = lambda *args, **kwargs: old_load(*args, **kwargs, allow_pickle=True)
                
                self.tts = Kokoro(str(self.kokoro_model_path), str(self.voices_path))
                
                # Restaurar el cargador original
                np.load = old_load
                
                print("🔊 Motor de Voz (Kokoro) listo con parche de seguridad aplicado.")
            except Exception as e:
                print(f"❌ Error inicializando TTS: {e}")

    def initialize_stt(self):
        """Load Faster-Whisper model."""
        if self.stt is None:
            try:
                print("👂 Inicializando motor de escucha local...")
                self.stt = WhisperModel("tiny", device="cpu", compute_type="int8")
                print("✅ Motor de Escucha listo.")
            except Exception as e:
                print(f"❌ Error inicializando STT: {e}")

    def speak(self, text: str, output_path: str = "output_midas.wav") -> Optional[str]:
        """Convert text to speech."""
        if self.tts is None:
            self.initialize_tts()
            
        if self.tts:
            try:
                # Limpiar texto para evitar que lea símbolos de Markdown
                clean_text = text.split("--- FUENTE:")[0] # Evitar leer las fuentes técnicas
                clean_text = clean_text.replace("**", "").replace("#", "").replace("- ", "").replace("`", "")
                
                # Kokoro brilla en inglés, español está en desarrollo pero lo intentamos
                samples, sample_rate = self.tts.create(
                    clean_text[:500], # Limitamos para evitar latencia alta en la primera prueba
                    voice=self.default_voice, 
                    speed=1.1, 
                    lang="en-us"
                )
                
                import scipy.io.wavfile as wavfile
                wavfile.write(output_path, sample_rate, samples)
                return output_path
            except Exception as e:
                print(f"❌ Error en generación de audio: {e}")
        return None

    def transcribe(self, audio_path: str) -> str:
        """Convert speech to text (Dictado)."""
        if self.stt is None:
            self.initialize_stt()
            
        if self.stt:
            try:
                segments, info = self.stt.transcribe(audio_path, beam_size=5)
                text = " ".join([segment.text for segment in segments])
                print(f"📝 Transcripción: {text}")
                return text
            except Exception as e:
                print(f"❌ Error en transcripción: {e}")
        return ""