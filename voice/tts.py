import asyncio
import os
import sys
import time
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

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

import config


class TextToSpeech:
    """
    Надежная генерация и воспроизведение голоса:
    1. Основной: Высококачественный нейронный Edge-TTS (Светлана).
    2. Резервный (Offline Fallback): Встроенный голос Windows SAPI5 (Ирина) через pyttsx3.
       Срабатывает мгновенно при любых сбоях сети или SSL.
    """

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

        # Инициализация резервного офлайн-движка
        self.offline_engine = None
        if pyttsx3:
            try:
                self.offline_engine = pyttsx3.init()
                # Ищем русский голос (обычно Irina)
                voices = self.offline_engine.getProperty("voices")
                for v in voices:
                    if "russian" in v.name.lower() or "irina" in v.name.lower():
                        self.offline_engine.setProperty("voice", v.id)
                        break
                self.offline_engine.setProperty("rate", 180)
            except Exception as e:
                print(f"[TTS Offline Init Warning]: {e}")

    async def _generate_audio_async(self, text: str, output_path: str):
        communicate = edge_tts.Communicate(text, voice=self.voice, rate=self.rate, pitch=self.pitch)
        await communicate.save(output_path)

    def _speak_offline(self, text: str):
        """Резервное воспроизведение через системный голос Windows без интернета."""
        if not self.offline_engine:
            return
        try:
            self.offline_engine.say(text)
            self.offline_engine.runAndWait()
        except Exception as e:
            print(f"[TTS Offline Error]: {e}")

    def speak(self, text: str, block: bool = True):
        """Озвучивает текст. При сетевых или SSL ошибках автоматически переходит на резервный голос."""
        if not text or not text.strip():
            return

        text = text.strip()
        print(f"[{config.ASSISTANT_NAME.capitalize()}]: {text}")

        # Если голосовой ответ отключен (для отладки), просто выводим текст в консоль
        if not getattr(config, "ENABLE_TTS", False):
            return

        with self._lock:
            # Пробуем Edge-TTS с повторной попыткой при сбое соединения
            edge_success = False
            temp_file = Path(tempfile.gettempdir()) / f"assistant_tts_{os.getpid()}_{int(time.time()*1000)}.mp3"

            if edge_tts and pygame:
                for attempt in range(2):
                    try:
                        # Запускаем в изолированном цикле
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            loop.run_until_complete(self._generate_audio_async(text, str(temp_file)))
                        finally:
                            loop.close()

                        # Воспроизводим полученный файл
                        pygame.mixer.music.load(str(temp_file))
                        pygame.mixer.music.play()
                        self._is_playing = True

                        if block:
                            while pygame.mixer.music.get_busy():
                                pygame.time.Clock().tick(10)
                            pygame.mixer.music.unload()
                            self._is_playing = False

                        edge_success = True
                        break
                    except Exception as ex:
                        if attempt == 0:
                            time.sleep(0.3)
                        else:
                            print(f"[TTS] Временный сбой облачного Edge-TTS ({ex}). Переключаюсь на резервный голос...")

                    finally:
                        if temp_file.exists():
                            try:
                                temp_file.unlink()
                            except Exception:
                                pass

            # Если облачный TTS не сработал — говорим через встроенный Windows SAPI
            if not edge_success:
                self._speak_offline(text)

    def stop(self):
        """Прерывает текущее воспроизведение."""
        if pygame and pygame.mixer.get_init():
            pygame.mixer.music.stop()
            self._is_playing = False
        if self.offline_engine:
            try:
                self.offline_engine.stop()
            except Exception:
                pass


tts = TextToSpeech()
