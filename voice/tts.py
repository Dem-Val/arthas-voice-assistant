import asyncio
import os
import tempfile
import threading
from pathlib import Path
from typing import Optional

try:
    import edge_tts
except ImportError:
    edge_tts = None

try:
    import pygame
except ImportError:
    pygame = None

import config


class TextToSpeech:
    """Генерация и воспроизведение естественного голоса через Edge-TTS."""

    def __init__(self):
        self.voice = config.VOICE_NAME
        self.rate = config.VOICE_RATE
        self.pitch = config.VOICE_PITCH
        self._is_playing = False
        self._lock = threading.Lock()

        # Инициализация звукового движка pygame
        if pygame:
            try:
                pygame.mixer.init()
            except Exception as e:
                print(f"[TTS] Предупреждение: pygame.mixer.init() не удался: {e}")

    async def _generate_audio_async(self, text: str, output_path: str):
        communicate = edge_tts.Communicate(text, voice=self.voice, rate=self.rate, pitch=self.pitch)
        await communicate.save(output_path)

    def speak(self, text: str, block: bool = True):
        """Озвучивает текст. block=True ждет завершения воспроизведения."""
        if not text or not text.strip():
            return

        text = text.strip()
        print(f"[{config.ASSISTANT_NAME.capitalize()}]: {text}")

        if not edge_tts or not pygame:
            # Запасной вывод, если аудиобиблиотеки не установлены
            return

        with self._lock:
            temp_file = Path(tempfile.gettempdir()) / f"assistant_tts_{os.getpid()}.mp3"
            try:
                # Генерируем аудио
                asyncio.run(self._generate_audio_async(text, str(temp_file)))

                # Воспроизводим
                pygame.mixer.music.load(str(temp_file))
                pygame.mixer.music.play()
                self._is_playing = True

                if block:
                    while pygame.mixer.music.get_busy():
                        pygame.time.Clock().tick(10)
                    pygame.mixer.music.unload()
                    self._is_playing = False
                    if temp_file.exists():
                        try:
                            temp_file.unlink()
                        except Exception:
                            pass
            except Exception as e:
                print(f"[TTS Error]: {e}")
                self._is_playing = False

    def stop(self):
        """Прерывает текущее воспроизведение."""
        if pygame and pygame.mixer.get_init():
            pygame.mixer.music.stop()
            self._is_playing = False


tts = TextToSpeech()
