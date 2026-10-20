import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Пути проекта (поддержка обычного запуска и скомпилированного .exe)
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

# Основные настройки ассистента
ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "артас").strip().lower()

# Настройки ИИ (Google Gemini)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
GEMINI_PROXY = os.getenv("GEMINI_PROXY", "").strip() or os.getenv("HTTPS_PROXY", "").strip() or os.getenv("HTTP_PROXY", "").strip()
GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "").strip()

# Альтернативный провайдер (OpenRouter / Groq / Любой OpenAI-совместимый)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "google/gemini-2.0-flash-exp:free").strip()

# Голосовой ответ (TTS) - временно отключен для отладки
ENABLE_TTS = os.getenv("ENABLE_TTS", "false").strip().lower() in ("true", "1", "yes")

# Голосовые настройки (мужской голос Дмитрий для Артаса)
VOICE_NAME = os.getenv("VOICE_NAME", "ru-RU-DmitryNeural").strip()
VOICE_RATE = os.getenv("VOICE_RATE", "+0%").strip()
VOICE_PITCH = os.getenv("VOICE_PITCH", "+0Hz").strip()

# Звуковые уведомления
SOUNDS_DIR = BASE_DIR / "assets" / "sounds"
SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
