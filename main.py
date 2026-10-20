import os
import sys
import time
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent

sys.path.insert(0, str(BASE_DIR))

import config
from voice.tts import tts
from voice.stt import stt
from agent.brain import brain


def ensure_api_key():
    """Проверяет наличие API-ключа (OpenRouter без VPN или Gemini). Если нет — запрашивает у пользователя."""
    env_file = config.BASE_DIR / ".env"
    has_key = bool(config.OPENAI_API_KEY or (config.GEMINI_API_KEY and config.GEMINI_API_KEY != "your_gemini_api_key_here"))

    if not has_key:
        print("\n" + "=" * 60)
        print("  🔑 ТРЕБУЕТСЯ КЛЮЧ ИИ (БЕСПЛАТНО)")
        print("=" * 60)
        print("  1. OpenRouter (Рекомендуется для РФ, без VPN):")
        print("     👉 Получить ключ: https://openrouter.ai/keys (начинается на sk-or-...)")
        print("  2. Google Gemini API:")
        print("     👉 Получить ключ: https://aistudio.google.com/app/apikey")
        print("=" * 60)
        key = input("👉 Введите ваш API Key (OpenRouter или Gemini): ").strip()
        if key:
            if key.startswith("sk-"):
                config.OPENAI_API_KEY = key
                config.AI_PROVIDER = "openrouter"
                print("✅ Определен ключ OpenRouter (работает в РФ без VPN)!")
            else:
                config.GEMINI_API_KEY = key
                print("✅ Определен ключ Google Gemini!")

            env_content = f"""# Провайдер ИИ: "openrouter" (DeepSeek/Gemini без VPN) или "gemini"
AI_PROVIDER={config.AI_PROVIDER}

# OpenRouter (бесплатный DeepSeek V3 без VPN и ограничений)
OPENAI_API_KEY={config.OPENAI_API_KEY}
OPENAI_BASE_URL={config.OPENAI_BASE_URL}
OPENAI_MODEL={config.OPENAI_MODEL}

# Google Gemini API
GEMINI_API_KEY={config.GEMINI_API_KEY}
GEMINI_MODEL={config.GEMINI_MODEL}
GEMINI_PROXY={config.GEMINI_PROXY}

# Настройки ассистента
ASSISTANT_NAME={config.ASSISTANT_NAME}
ENABLE_TTS={str(config.ENABLE_TTS).lower()}
VOICE_NAME={config.VOICE_NAME}
VOICE_RATE={config.VOICE_RATE}
VOICE_PITCH={config.VOICE_PITCH}
"""
            with open(env_file, "w", encoding="utf-8") as f:
                f.write(env_content)
            brain.update_api_key(key)
            print("✅ Настройки успешно сохранены в .env!\n")
        else:
            print("⚠️ Ключ не введен. Будут доступны только системные команды Fast-Path.\n")


def print_banner():
    name = config.ASSISTANT_NAME.capitalize()
    model_info = f"OpenRouter ({config.OPENAI_MODEL}) [Без VPN]" if config.OPENAI_API_KEY else f"Google Gemini ({config.GEMINI_MODEL})"
    print("=" * 60)
    print(f" ✨ ГОЛОСОВОЙ ИИ-ПОМОЩНИК «{name.upper()}» ДЛЯ WINDOWS ✨")
    print("=" * 60)
    print(f" • Имя для активации: «{name}» (например: '{name}, открой оперу')")
    print(f" • Модель ИИ:        {model_info}")
    print(f" • Мгновенный путь:  Fast-Path 0.1с (программы, звук, окна, медиа)")
    print(f" • Для выхода:       нажмите Ctrl+C в этом окне")
    print("=" * 60 + "\n")



def process_command(command_text: str):
    """Выполняет команду через мозг Gemini и озвучивает результат."""
    if not command_text or not command_text.strip():
        return

    print(f"\n[Запрос]: {command_text}")
    response = brain.process_user_input(command_text)
    tts.speak(response)


def run_voice_loop():
    """Основной цикл прослушивания микрофона и реакции на голос."""
    assistant_name = config.ASSISTANT_NAME.capitalize()
    print(f"🎙️  {assistant_name} слушает микрофон в фоне...")
    print(f"💡 Скажите: «{assistant_name}, ...» или «{assistant_name}» для активации.\n")

    # Приветственная фраза при старте
    tts.speak(f"Привет! Я {assistant_name}. Чем помочь?")

    while True:
        try:
            # Слушаем фоновый звук
            phrase = stt.listen_phrase(timeout=None, phrase_time_limit=8)
            if not phrase:
                continue

            print(f"[Услышано]: {phrase}")
            is_wake, command = stt.check_wake_word(phrase)

            if is_wake:
                stt.play_wake_sound()

                if command:
                    # Пользователь сказал имя и команду сразу: "Артас, открой стим"
                    process_command(command)
                else:
                    # Пользователь сказал только имя: "Артас"
                    tts.speak("Слушаю вас!", block=True)
                    # Ждем саму команду
                    next_phrase = stt.listen_phrase(timeout=7, phrase_time_limit=10)
                    if next_phrase:
                        process_command(next_phrase)
                    else:
                        tts.speak("Не расслышал команду. Если понадоблюсь — позовите.")

        except KeyboardInterrupt:
            print("\n[Выход] Завершение работы...")
            tts.speak("До встречи!")
            break
        except Exception as e:
            print(f"[Ошибка цикла]: {e}")
            time.sleep(1)


def main():
    print_banner()
    ensure_api_key()
    run_voice_loop()


if __name__ == "__main__":
    main()
