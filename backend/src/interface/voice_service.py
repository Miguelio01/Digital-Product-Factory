"""
Zero-cost local voice service - Clean Version
"""
import os
from pathlib import Path
from typing import Optional
import urllib.request
import numpy as np

from kokoro_onnx import Kokoro

class VoiceService:
    def __init__(self, model_dir: str = "models/voice"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.kokoro_model_path = self.model_dir / "kokoro-v0_19.onnx"
        self.voices_path = self.model_dir / "voices.json"
        self.tts: Optional[Kokoro] = None
        self.default_voice = "af_sky"
        
    def ensure_models(self):
        onnx_url = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0_19.onnx"
        voices_url = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/voices.json"
        
        if not self.kokoro_model_path.exists():
            print(f"📥 Descargando ONNX...")
            urllib.request.urlretrieve(onnx_url, self.kokoro_model_path)
        if not self.voices_path.exists():
            print(f"📥 Descargando Voces...")
            urllib.request.urlretrieve(voices_url, self.voices_path)
            
    def initialize_tts(self):
        if self.tts is None:
            self.ensure_models()
            try:
                # Carga limpia de Kokoro
                self.tts = Kokoro(str(self.kokoro_model_path), str(self.voices_path))
                print("🔊 Motor de Voz listo.")
            except Exception as e:
                print(f"❌ Error inicializando TTS: {e}")

    def speak(self, text: str, output_path: str = "output.wav") -> Optional[str]:
        if self.tts is None:
            self.initialize_tts()
        if self.tts:
            try:
                # Limpiar texto para evitar errores de lectura
                clean_text = text.split("--- FUENTE:")[0]
                clean_text = clean_text.replace("**", "").replace("#", "").replace("- ", "").replace("`", "")[:500]
                
                samples, sample_rate = self.tts.create(
                    clean_text, voice=self.default_voice, speed=1.1, lang="en-us"
                )
                import scipy.io.wavfile as wavfile
                wavfile.write(output_path, sample_rate, samples)
                return output_path
            except Exception as e:
                print(f"❌ Error speak: {e}")
        return None
