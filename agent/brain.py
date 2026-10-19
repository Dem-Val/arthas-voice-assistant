import json
from typing import Callable, Dict, Any, List
from google import genai
from google.genai import types

import config
from tools.app_scanner import app_scanner
from tools.file_search import file_search
from tools.system_control import SystemControl
from tools.web_tools import web_tools


# Системный промпт Лины
SYSTEM_INSTRUCTION = f"""
Ты — {config.ASSISTANT_NAME.capitalize()}, умный голосовой помощник и интеллектуальный агент для компьютера с Windows.
Ты управляешь компьютером, выполняешь команды пользователя и отвечаешь на вопросы.

ПРАВИЛА ПОВЕДЕНИЯ:
1. Если пользователь просит выполнить действие (открыть программу, найти файл, изменить звук, открыть сайт, включить музыку, свернуть окна), ТЫ ОБЯЗАНА вызвать подходящую функцию (tool).
2. Пользователь может говорить разговорно (например: "открой телегу", "выруби звук", "сделай потише", "вруби на ютубе песню", "найди файл диплома"). Понимай смысл и выбирай правильный инструмент.
3. Голосовой ответ должен быть кратким, живым и естественным (1-2 коротких предложения), так как он будет озвучиваться вслух. Избегай списков и длинных лекций, если тебя специально об этом не просили.
4. После вызова инструмента кратко подтверди выполнение пользователю.
"""


# Определение инструментов для Gemini
def launch_application(app_name: str) -> str:
    """Ищет и открывает программу или приложение на компьютере по названию (например: 'телеграм', 'калькулятор', 'хром', 'стим', 'блокнот')."""
    return app_scanner.launch(app_name)


def open_file(filename: str) -> str:
    """Находит и открывает файл на компьютере подходящей программой (например: 'отчет.docx', 'список покупок', 'фото')."""
    return file_search.open_file_by_name(filename)


def show_file_in_folder(filename: str) -> str:
    """Находит файл и показывает его в проводнике Windows."""
    return file_search.show_in_folder(filename)


def set_volume_percent(percent: int) -> str:
    """Устанавливает громкость звука системы от 0 до 100 процентов."""
    return SystemControl.set_volume(percent)


def change_volume(delta: int) -> str:
    """Изменяет громкость звука на указанное число процентов (например +15 или -15)."""
    return SystemControl.change_volume(delta)


def toggle_mute() -> str:
    """Выключает или включает звук на компьютере."""
    return SystemControl.mute_volume()


def media_play_pause() -> str:
    """Включает или ставит на паузу музыку или видео."""
    return SystemControl.media_play_pause()


def media_next_track() -> str:
    """Переключает на следующий трек."""
    return SystemControl.media_next()


def media_previous_track() -> str:
    """Переключает на предыдущий трек."""
    return SystemControl.media_prev()


def minimize_windows() -> str:
    """Сворачивает все открытые окна и показывает рабочий стол."""
    return SystemControl.minimize_all_windows()


def take_screenshot() -> str:
    """Делает снимок экрана (скриншот) и сохраняет в папку Изображения."""
    return SystemControl.take_screenshot()


def lock_computer() -> str:
    """Блокирует экран компьютера."""
    return SystemControl.lock_pc()


def search_google(query: str) -> str:
    """Ищет запрос в интернете через поисковик в браузере."""
    return web_tools.search_google(query)


def open_website(url: str) -> str:
    """Открывает веб-сайт или ссылку в браузере."""
    return web_tools.open_url(url)


def play_youtube(query: str) -> str:
    """Ищет и включает видео, песню или клип на YouTube в браузере."""
    return web_tools.play_youtube(query)


# Список доступных функций
TOOL_FUNCTIONS: List[Callable] = [
    launch_application,
    open_file,
    show_file_in_folder,
    set_volume_percent,
    change_volume,
    toggle_mute,
    media_play_pause,
    media_next_track,
    media_previous_track,
    minimize_windows,
    take_screenshot,
    lock_computer,
    search_google,
    open_website,
    play_youtube,
]

FUNCTIONS_MAP: Dict[str, Callable] = {fn.__name__: fn for fn in TOOL_FUNCTIONS}


class AssistantBrain:
    """Мозг ассистента на базе Google Gemini с поддержкой Function Calling."""

    def __init__(self):
        self.api_key = config.GEMINI_API_KEY
        self.model_name = config.GEMINI_MODEL
        self.client = None
        self.chat = None

        if self.api_key:
            self._init_client()

    def _init_client(self):
        try:
            self.client = genai.Client(api_key=self.api_key)
            self.chat = self.client.chats.create(
                model=self.model_name,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    tools=TOOL_FUNCTIONS,
                    temperature=0.7,
                ),
            )
            print("[Brain] Мозг Gemini успешно инициализирован.")
        except Exception as e:
            print(f"[Brain Error] Не удалось инициализировать Gemini: {e}")
            self.client = None

    def update_api_key(self, api_key: str):
        """Обновляет ключ API и пересоздает клиента."""
        self.api_key = api_key.strip()
        self._init_client()

    def process_user_input(self, user_text: str) -> str:
        """
        Обрабатывает фразу пользователя:
        - Отправляет в Gemini
        - Если Gemini решает вызвать инструмент(ы), выполняет их и возвращает результат
        - Возвращает финальный голосовой ответ для пользователя
        """
        if not self.client or not self.chat:
            return "Ключ Gemini API не настроен. Пожалуйста, укажите ваш GEMINI_API_KEY в файле .env."

        try:
            print(f"[User]: {user_text}")
            response = self.chat.send_message(user_text)

            # Проверяем, есть ли вызовы функций
            while response.function_calls:
                function_responses = []
                for call in response.function_calls:
                    fn_name = call.name
                    args = dict(call.args) if call.args else {}
                    print(f"[Tool Call] {fn_name}({args})")

                    if fn_name in FUNCTIONS_MAP:
                        try:
                            result = FUNCTIONS_MAP[fn_name](**args)
                        except Exception as ex:
                            result = f"Ошибка при выполнении {fn_name}: {ex}"
                    else:
                        result = f"Функция {fn_name} не найдена."

                    print(f"[Tool Result] {result}")
                    function_responses.append(
                        types.Part.from_function_response(
                            name=fn_name,
                            response={"result": result},
                        )
                    )

                # Передаем результат выполнения функции обратно модели
                response = self.chat.send_message(function_responses)

            return response.text or "Готово!"

        except Exception as e:
            print(f"[Brain Process Error]: {e}")
            return "Произошла ошибка при обработке запроса. Попробуйте еще раз."


brain = AssistantBrain()
