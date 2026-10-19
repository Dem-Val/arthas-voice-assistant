import os
from pathlib import Path
from dotenv import load_dotenv

import sys

# Пути проекта (поддержка обычного запуска и скомпилированного .exe)
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

# Основные настройки
ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "лина").strip().lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()

# Голосовые настройки
VOICE_NAME = os.getenv("VOICE_NAME", "ru-RU-SvetlanaNeural").strip()
VOICE_RATE = os.getenv("VOICE_RATE", "+0%").strip()
VOICE_PITCH = os.getenv("VOICE_PITCH", "+0Hz").strip()

# Звуковые уведомления
SOUNDS_DIR = BASE_DIR / "assets" / "sounds"
SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
