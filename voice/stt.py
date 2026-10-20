import re
import sys
import time
from typing import Optional, Tuple, Set

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    import winsound
except ImportError:
    winsound = None

try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None

import config


# Словарь популярных имен и их частых фонетических искажений при распознавании Google STT
KNOWN_NAME_ALIASES = {
    "артас": [
        "артас", "артес", "ортас", "артос", "атас", "атлас", "арт",
        "артаса", "артасу", "артасом", "artas", "arthas", "аркас", "артус"
    ],
    "лина": [
        "лина", "алина", "элина", "лину", "лине", "линой", "линочка",
        "lina", "alina", "elena"
    ],
    "гладиатор": [
        "гладиатор", "гладиатора", "гладиатору", "гладиатором", "gladiator"
    ]
}


class SpeechRecognizer:
    """Модуль распознавания речи и отслеживания имени-триггера (Wake Word)."""

    def __init__(self):
        self.wake_name = config.ASSISTANT_NAME.lower().strip()
        self._build_wake_aliases()

        self.recognizer = None
        self.microphone = None

        if sr:
            self.recognizer = sr.Recognizer()
            # Оптимальная чувствительность и быстрое срабатывание
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            # Порог паузы 0.8с для естественной речи без обрывания фраз
            self.recognizer.pause_threshold = 0.8
            self.recognizer.non_speaking_duration = 0.5


            try:
                self.microphone = sr.Microphone()
                print("[STT] Калибровка уровня фонового шума микрофона (1 сек)...")
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
                print("[STT] Микрофон готов к работе.")
            except Exception as e:
                print(f"[STT Warning] Микрофон не инициализирован: {e}")

    def _build_wake_aliases(self):
        """Формирует список всех возможных форм и искажений имени помощника."""
        self.aliases: Set[str] = set()

        # Добавляем имя из настроек
        self.aliases.add(self.wake_name)

        # Если имя есть в базе известных, добавляем его варианты
        if self.wake_name in KNOWN_NAME_ALIASES:
            self.aliases.update(KNOWN_NAME_ALIASES[self.wake_name])

        # Всегда включаем варианты для Артаса и Лины (на случай привычки пользователя)
        self.aliases.update(KNOWN_NAME_ALIASES["артас"])
        self.aliases.update(KNOWN_NAME_ALIASES["лина"])

    def play_wake_sound(self):
        """Звуковой сигнал активации помощника."""
        if winsound:
            try:
                winsound.Beep(900, 80)
                winsound.Beep(1200, 100)
            except Exception:
                pass

    def check_wake_word(self, text: str) -> Tuple[bool, str]:
        """
        Проверяет, содержит ли фраза имя помощника (с поддержкой нечеткого поиска и опечаток Google STT).
        Например:
          - 'Алина открой оперу' -> (True, 'открой оперу') [исправление Лина -> Алина]
          - 'Артес сделай тише' -> (True, 'сделай тише')  [исправление Артас -> Артес]
          - 'Артас' -> (True, '')
        """
        if not text:
            return False, ""

        clean_text = text.lower().strip()
        tokens = [t.strip(",.!? \t\n") for t in clean_text.split() if t.strip(",.!? \t\n")]
        if not tokens:
            return False, ""

        # 1. Точная проверка первых 3 токенов
        for i, token in enumerate(tokens[:3]):
            if token in self.aliases:
                cmd_tokens = tokens[:i] + tokens[i+1:]
                return True, " ".join(cmd_tokens).strip()

        # 2. Нечеткая проверка первых 3 токенов (Levenshtein / RapidFuzz)
        # Обрабатывает искажения: "алина" вместо "лина", "артес/ортас" вместо "артас"
        if fuzz:
            for i, token in enumerate(tokens[:3]):
                for alias in self.aliases:
                    score = fuzz.ratio(token, alias)
                    if score >= 75:
                        cmd_tokens = tokens[:i] + tokens[i+1:]
                        return True, " ".join(cmd_tokens).strip()

        # 3. Регулярное выражение по корню
        wake_root = self.wake_name[:4] if len(self.wake_name) >= 4 else self.wake_name
        pattern = rf"\b{wake_root}[а-яёa-z]*\b"
        match = re.search(pattern, clean_text)
        if match:
            remaining = clean_text[: match.start()] + clean_text[match.end() :]
            remaining = re.sub(r"^[,.\s!?]+|[,.\s!?]+$", "", remaining).strip()
            return True, remaining

        return False, clean_text

    def listen_phrase(self, timeout: Optional[int] = None, phrase_time_limit: int = 8) -> Optional[str]:
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
        except Exception:
            return None


stt = SpeechRecognizer()

