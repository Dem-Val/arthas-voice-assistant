import re
import sys
import time
from typing import Optional, Tuple

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    import winsound
except ImportError:
    winsound = None

import config


class SpeechRecognizer:
    """Модуль распознавания речи и отслеживания имени-триггера (Wake Word)."""

    def __init__(self):
        self.wake_name = config.ASSISTANT_NAME.lower()
        # Варианты обращения к ассистенту
        self.wake_patterns = [
            rf"\b{self.wake_name}\b",
            rf"\b{self.wake_name}[а-яё]*\b",  # гладиатор, гладиатора, гладиатору
            r"\bглад\b",
            r"\bgladiator\b",
        ]
        self.recognizer = None
        self.microphone = None

        if sr:
            self.recognizer = sr.Recognizer()
            # Настройки чувствительности
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8

            try:
                self.microphone = sr.Microphone()
                # Калибровка шума
                print("[STT] Калибровка уровня фонового шума микрофона (1 сек)...")
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
                print("[STT] Микрофон готов.")
            except Exception as e:
                print(f"[STT Warning] Микрофон не инициализирован: {e}")

    def play_wake_sound(self):
        """Звуковой сигнал активации помощника."""
        if winsound:
            try:
                winsound.Beep(900, 100)
                winsound.Beep(1200, 120)
            except Exception:
                pass

    def check_wake_word(self, text: str) -> Tuple[bool, str]:
        """
        Проверяет, содержит ли фраза имя помощника.
        Возвращает (нашли_ли_имя, оставшаяся_команда).
        Например: 'Лина открой браузер' -> (True, 'открой браузер').
        """
        clean_text = text.lower().strip()
        for pattern in self.wake_patterns:
            match = re.search(pattern, clean_text)
            if match:
                # Отрезаем имя и знаки препинания
                remaining = clean_text[: match.start()] + clean_text[match.end() :]
                remaining = re.sub(r"^[,.\s!?]+|[,.\s!?]+$", "", remaining).strip()
                return True, remaining
        return False, clean_text

    def listen_phrase(self, timeout: Optional[int] = None, phrase_time_limit: int = 10) -> Optional[str]:
        """Слушает одну фразу пользователя через микрофон и возвращает распознанный текст."""
        if not self.recognizer or not self.microphone:
            return None

        try:
            with self.microphone as source:
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )
            text = self.recognizer.recognize_google(audio, language="ru-RU")
            return text.strip()
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except Exception as e:
            # Сетевые или иные мелкие сбои распознавания
            return None


stt = SpeechRecognizer()
