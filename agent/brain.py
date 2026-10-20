import json
import os
import sys
from typing import Callable, Dict, Any, List
from google import genai
from google.genai import types

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

import config
from agent.fast_path import fast_router
from tools.app_scanner import app_scanner
from tools.file_search import file_search
from tools.system_control import SystemControl
from tools.web_tools import web_tools


# Системный промпт Артаса
SYSTEM_INSTRUCTION = f"""
Ты — {config.ASSISTANT_NAME.capitalize()}, мощный, умный и преданный голосовой помощник и интеллектуальный агент для операционной системы Windows.
Ты управляешь компьютером, мгновенно выполняешь команды пользователя и отвечаешь на вопросы уверенным, лаконичным тоном.

ПРАВИЛА ПОВЕДЕНИЯ:
1. Если пользователь просит выполнить системное действие (открыть программу, найти файл, изменить звук, открыть сайт, включить музыку, свернуть окна, заблокировать ПК), ТЫ ОБЯЗАН вызвать подходящую функцию (tool).
2. Пользователь может говорить разговорно (например: "открой телегу", "выруби звук", "сделай потише", "вруби на ютубе музыку", "найди файл диплома"). Распознавай суть и выбирай правильный инструмент.
3. Голосовой ответ должен быть кратким, живым и естественным (1-2 коротких предложения), так как он будет озвучиваться вслух. Никаких длинных монологов без просьбы.
4. После вызова инструмента коротко подтверди выполнение пользователю.
"""


# Определение системных инструментов
def launch_application(app_name: str) -> str:
    """Ищет и открывает программу или приложение на компьютере по названию (например: 'телеграм', 'калькулятор', 'хром', 'стим', 'блокнот', 'опера')."""
    return app_scanner.launch(app_name)


def open_file(filename: str) -> str:
    """Находит и открывает файл на компьютере подходящей программой (например: 'отчет.docx', 'список покупок', 'фото')."""
    return file_search.open_file_by_name(filename)


def show_file_in_folder(filename: str) -> str:
    """Находит файл и показывает его расположение в проводнике Windows."""
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
    """Включает или ставит на паузу воспроизведение музыки или видео."""
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
    """Ищет информацию в интернете через браузер."""
    return web_tools.search_google(query)


def open_website(url: str) -> str:
    """Открывает веб-сайт или ссылку в браузере."""
    return web_tools.open_url(url)


def play_youtube(query: str) -> str:
    """Ищет и включает видео, песню или клип на YouTube в браузере."""
    return web_tools.play_youtube(query)


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
    """Мозг ассистента: Google Gemini с поддержкой прокси, VPN и альтернативных провайдеров."""

    def __init__(self):
        self.api_key = config.GEMINI_API_KEY
        self.model_name = config.GEMINI_MODEL
        self.client = None
        self.chat = None

        if self.api_key:
            self._init_client()

    def _init_client(self):
        try:
            http_options = types.HttpOptions()
            # Настройка прокси при наличии
            if config.GEMINI_PROXY:
                http_options.client_args = {"proxy": config.GEMINI_PROXY}
                print(f"[Brain] Используется прокси для Gemini: {config.GEMINI_PROXY}")
            if config.GEMINI_BASE_URL:
                http_options.base_url = config.GEMINI_BASE_URL

            self.client = genai.Client(api_key=self.api_key, http_options=http_options)
            self.chat = self.client.chats.create(
                model=self.model_name,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    tools=TOOL_FUNCTIONS,
                    temperature=0.7,
                ),
            )
            print(f"[Brain] Мозг {config.ASSISTANT_NAME.capitalize()} (Gemini) успешно инициализирован.")
        except Exception as e:
            print(f"[Brain Error] Не удалось инициализировать Gemini: {e}")
            self.client = None

    def update_api_key(self, api_key: str):
        self.api_key = api_key.strip()
        self._init_client()

    def process_user_input(self, user_text: str) -> str:
        """
        Обрабатывает фразу пользователя:
        - Проверяет мгновенный Fast-Path (0.01-0.05 сек)
        - При необходимости отправляет в ИИ Gemini
        - Выполняет инструменты за один шаг без задержки
        """
        # 1. Проверяем Fast-Path (мгновенный локальный ответ без задержки)
        fast_result = fast_router.try_handle(user_text)
        if fast_result is not None:
            return fast_result

        if not self.client or not self.chat:
            return "Ключ Gemini API не настроен. Пожалуйста, укажите ваш GEMINI_API_KEY в файле .env."

        try:
            print(f"[User]: {user_text}")
            response = self.chat.send_message(user_text)

            # Выполнение Function Calling
            if response.function_calls:
                tool_results = []
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
                    tool_results.append(str(result))
                    function_responses.append(
                        types.Part.from_function_response(
                            name=fn_name,
                            response={"result": result},
                        )
                    )

                # Синхронизируем контекст диалога в фоновом потоке, не блокируя ответ пользователю
                import threading
                def _sync_chat():
                    try:
                        self.chat.send_message(function_responses)
                    except Exception:
                        pass
                threading.Thread(target=_sync_chat, daemon=True).start()

                # Мгновенно отдаем пользователю подтверждение от выполненного инструмента
                return " ".join(tool_results)

            return response.text or "Слушаюсь и повинуюсь!"


        except Exception as e:
            err_msg = str(e)
            print(f"[Brain Process Error]: {err_msg}")

            # Проверка на региональную блокировку Google (User location is not supported)
            if "User location is not supported" in err_msg or "FAILED_PRECONDITION" in err_msg:
                print("\n" + "!" * 60)
                print(" ⚠️  РЕГИОНАЛЬНОЕ ОГРАНИЧЕНИЕ GOOGLE GEMINI:")
                print(" Google блокирует прямые запросы к AI Studio с IP-адресов РФ.")
                print(" Решения:")
                print("  1. Включите любой системный VPN на вашем компьютере (Amnezia, WireGuard, VLESS, Outline и др.)")
                print("  2. ИЛИ пропишите локальный прокси в файле .env: GEMINI_PROXY=http://127.0.0.1:10809")
                print("  3. ИЛИ используйте OpenRouter (работает в РФ без VPN): укажите OPENAI_API_KEY в .env")
                print("!" * 60 + "\n")
                return "Google ограничивает доступ из вашего региона. Пожалуйста, включите VPN на компьютере или настройте прокси в файле настроек."

            return "Произошла ошибка при обработке запроса. Попробуйте еще раз."


brain = AssistantBrain()
