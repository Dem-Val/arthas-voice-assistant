import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import config
from agent.brain import brain
from voice.tts import tts
from tools.app_scanner import app_scanner


def test_cli():
    print("=" * 60)
    print("  🧪 РЕЖИМ ТЕСТИРОВАНИЯ ИИ-ПОМОЩНИКА (ТЕКСТОВЫЙ РЕЖИМ)")
    print("=" * 60)
    print(f"Кэшировано программ в Windows: {len(app_scanner.apps_cache)}")
    print("Введите текстовую команду (или 'exit' для выхода):")
    print("Примеры:")
    print(" - открой калькулятор")
    print(" - запусти хром")
    print(" - сделай громкость 30%")
    print(" - включи на ютубе lofi music")
    print(" - найди файл отчет")
    print("=" * 60)

    while True:
        try:
            user_input = input("\nВы > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "выход"]:
                break

            response = brain.process_user_input(user_input)
            print(f"\nГладиатор > {response}")
            tts.speak(response)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Ошибка: {e}")


if __name__ == "__main__":
    test_cli()
