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

# Выбор провайдера ИИ: "openrouter" (DeepSeek/Gemini без VPN) или "gemini" (прямой Google) или "groq"
AI_PROVIDER = os.getenv("AI_PROVIDER", "openrouter" if os.getenv("OPENAI_API_KEY") else "gemini").strip().lower()

# Автоматическое определение локального прокси (Clash 7890, VLESS 10809, Nekoray 2080)
def detect_local_proxy() -> str:
    env_p = os.getenv("AI_PROXY") or os.getenv("GEMINI_PROXY") or os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
    if env_p:
        return env_p.strip()
    import socket
    for port in [7890, 10809, 10808, 2080]:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.15):
                return f"http://127.0.0.1:{port}"
        except Exception:
            pass
    return ""

AI_PROXY = detect_local_proxy()

# Настройки ИИ (Google Gemini)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash").strip()
GEMINI_PROXY = AI_PROXY
GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "").strip()


# Настройки OpenRouter / Groq / OpenAI (100% бесплатно без региональных ограничений)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.groq.com/openai/v1").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "qwen/qwen3.8-27b").strip()



# Голосовой ответ (TTS) - временно отключен для отладки
ENABLE_TTS = os.getenv("ENABLE_TTS", "false").strip().lower() in ("true", "1", "yes")

# Голосовые настройки (мужской голос Дмитрий для Артаса)
VOICE_NAME = os.getenv("VOICE_NAME", "ru-RU-DmitryNeural").strip()
VOICE_RATE = os.getenv("VOICE_RATE", "+0%").strip()
VOICE_PITCH = os.getenv("VOICE_PITCH", "+0Hz").strip()

# Звуковые уведомления
SOUNDS_DIR = BASE_DIR / "assets" / "sounds"
SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
