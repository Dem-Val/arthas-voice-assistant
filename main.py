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
    """Проверяет наличие API-ключа Gemini. Если нет — запрашивает у пользователя и сохраняет."""
    env_file = config.BASE_DIR / ".env"
    if not config.GEMINI_API_KEY or config.GEMINI_API_KEY == "your_gemini_api_key_here":
        print("\n" + "=" * 60)
        print("  🔑 ТРЕБУЕТСЯ КЛЮЧ GOOGLE GEMINI API")
        print("  Получить бесплатно можно тут: https://aistudio.google.com/app/apikey")
        print("=" * 60)
        key = input("👉 Введите ваш Gemini API Key: ").strip()
        if key:
            config.GEMINI_API_KEY = key
            # Записываем в .env
            env_content = f"""# Google Gemini API Key
GEMINI_API_KEY={key}
ASSISTANT_NAME={config.ASSISTANT_NAME}
VOICE_NAME={config.VOICE_NAME}
VOICE_RATE={config.VOICE_RATE}
VOICE_PITCH={config.VOICE_PITCH}
GEMINI_MODEL={config.GEMINI_MODEL}
"""
            with open(env_file, "w", encoding="utf-8") as f:
                f.write(env_content)
            brain.update_api_key(key)
            print("✅ Ключ успешно сохранен в .env!\n")
        else:
            print("⚠️ Ключ не введен. Функции ИИ будут недоступны до ввода ключа в .env.")


def print_banner():
    name = config.ASSISTANT_NAME.capitalize()
    print("=" * 60)
    print(f" ✨ ГОЛОСОВОЙ ИИ-ПОМОЩНИК «{name.upper()}» ДЛЯ WINDOWS ✨")
    print("=" * 60)
    print(f" • Имя для активации: «{name}» (например: '{name}, открой хром')")
    print(" • Модель ИИ:        Google Gemini (динамический поиск и действия)")
    print(" • Голос озвучки:    Microsoft Neural (Edge-TTS)")
    print(" • Для выхода:       нажмите Ctrl+C в этом окне")
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
                    # Пользователь сказал имя и команду сразу: "Гладиатор, открой стим"
                    process_command(command)
                else:
                    # Пользователь сказал только имя: "Гладиатор"
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
