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


# Описание инструментов для OpenAI-совместимых провайдеров (OpenRouter / Groq / DeepSeek)
OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "launch_application",
            "description": "Ищет и открывает программу или приложение на компьютере по названию (например: 'телеграм', 'калькулятор', 'хром', 'стим', 'блокнот', 'опера').",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Название программы"}
                },
                "required": ["app_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_google",
            "description": "Ищет информацию в интернете через браузер Google.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Поисковый запрос"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "play_youtube",
            "description": "Включает песню, видео или музыку на YouTube в браузере.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Название видео или песни"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_volume_percent",
            "description": "Устанавливает громкость звука системы от 0 до 100 процентов.",
            "parameters": {
                "type": "object",
                "properties": {
                    "percent": {"type": "integer", "description": "Громкость 0-100"}
                },
                "required": ["percent"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "change_volume",
            "description": "Изменяет громкость звука на указанное число процентов (+15 или -15).",
            "parameters": {
                "type": "object",
                "properties": {
                    "delta": {"type": "integer", "description": "Дельта громкости"}
                },
                "required": ["delta"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "toggle_mute",
            "description": "Выключает или включает звук на компьютере.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "minimize_windows",
            "description": "Сворачивает все открытые окна и показывает рабочий стол.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Делает снимок экрана (скриншот).",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lock_computer",
            "description": "Блокирует экран компьютера.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_website",
            "description": "Открывает веб-сайт по ссылке.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Ссылка"}
                },
                "required": ["url"],
            },
        },
    },
]


class AssistantBrain:
    """Мозг ассистента: Двойной движок — OpenRouter (DeepSeek без VPN) и Google Gemini."""

    def __init__(self):
        self.openai_client = None
        self.openai_messages = [{"role": "system", "content": SYSTEM_INSTRUCTION}]

        self.gemini_client = None
        self.gemini_chat = None

        self._init_providers()

    def _init_providers(self):
        # 1. OpenRouter / Groq / GitHub / OpenAI-совместимый движок
        if config.OPENAI_API_KEY and OpenAI:
            key = config.OPENAI_API_KEY.strip()
            base_url = config.OPENAI_BASE_URL
            model = config.OPENAI_MODEL

            # Умное автоопределение провайдера по формату ключа:
            if key.startswith("gsk_"):
                # Ключ от сверхбыстрого Groq Cloud (100% бесплатно навсегда, без депозитов и карт)
                base_url = "https://api.groq.com/openai/v1"
                model = os.getenv("OPENAI_MODEL", "qwen/qwen3.8-27b").strip()
                print(f"[Brain] Распознан ключ Groq Cloud! Сверхбыстрая скорость (Модель: {model})")
            elif key.startswith("ghp_") or key.startswith("github_pat_"):
                # Токен GitHub Models (бесплатно для всех пользователей GitHub)
                base_url = "https://models.inference.ai.azure.com"
                model = "gpt-4o-mini"
                print(f"[Brain] Распознан ключ GitHub Models! (Модель: {model})")
            elif key.startswith("sk-or-"):
                base_url = "https://openrouter.ai/api/v1"
                print(f"[Brain] Распознан ключ OpenRouter! (Модель: {model})")

            http_client = None
            if config.AI_PROXY:
                try:
                    import httpx
                    http_client = httpx.Client(proxy=config.AI_PROXY)
                    print(f"[Brain] Задействован локальный прокси: {config.AI_PROXY}")
                except Exception as ex:
                    print(f"[Brain Warning] Не удалось подключить прокси для httpx: {ex}")

            try:
                self.openai_client = OpenAI(
                    api_key=key,
                    base_url=base_url,
                    http_client=http_client,
                )
                self.active_openai_model = model
                print(f"[Brain] Подключен безрегиональный ИИ ({model}) через {base_url}")
            except Exception as e:
                print(f"[Brain Error] Не удалось инициализировать OpenAI/Groq: {e}")
                self.openai_client = None



        # 2. Google Gemini
        if config.GEMINI_API_KEY:
            try:
                http_options = types.HttpOptions()
                if config.GEMINI_PROXY:
                    http_options.client_args = {"proxy": config.GEMINI_PROXY}
                if config.GEMINI_BASE_URL:
                    http_options.base_url = config.GEMINI_BASE_URL

                self.gemini_client = genai.Client(api_key=config.GEMINI_API_KEY, http_options=http_options)
                self.gemini_chat = self.gemini_client.chats.create(
                    model=config.GEMINI_MODEL,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        tools=TOOL_FUNCTIONS,
                        temperature=0.7,
                    ),
                )
                print(f"[Brain] Google Gemini инициализирован (Модель: {config.GEMINI_MODEL})")
            except Exception as e:
                print(f"[Brain Warning] Не удалось инициализировать Gemini: {e}")
                self.gemini_client = None
                self.gemini_chat = None

    def update_api_key(self, api_key: str):
        # Если ключ похож на OpenRouter (начинается на sk-or-) или OpenAI (sk-)
        if api_key.startswith("sk-"):
            config.OPENAI_API_KEY = api_key
            config.AI_PROVIDER = "openrouter"
        else:
            config.GEMINI_API_KEY = api_key
        self._init_providers()

    def process_user_input(self, user_text: str) -> str:
        """
        Обрабатывает фразу пользователя:
        - 1. Мгновенный Fast-Path (0.05-0.10 сек) без нейросети
        - 2. OpenRouter (DeepSeek/Gemini без ограничений региона) при наличии ключа
        - 3. Google Gemini при наличии ключа
        """
        # 1. Fast-Path
        fast_result = fast_router.try_handle(user_text)
        if fast_result is not None:
            return fast_result

        # 2. Приоритет Groq / OpenRouter / OpenAI (без VPN и региональных блоков)
        if self.openai_client:
            return self._process_openai(user_text)

        # 3. Google Gemini (только если нет OpenAI/Groq клиента)
        if self.gemini_chat:
            return self._process_gemini(user_text)

        return "Ключ ИИ не настроен. Укажите OPENAI_API_KEY (Groq/OpenRouter) или GEMINI_API_KEY в файле .env."


    def _process_openai(self, user_text: str) -> str:
        """Обработка через OpenRouter / Groq / OpenAI (DeepSeek V3, Llama 3.3)."""
        try:
            print(f"[User]: {user_text}")
            self.openai_messages.append({"role": "user", "content": user_text})
            # Ограничиваем историю диалога 12 сообщениями для экономии токенов
            if len(self.openai_messages) > 13:
                self.openai_messages = [self.openai_messages[0]] + self.openai_messages[-12:]

            active_model = getattr(self, "active_openai_model", config.OPENAI_MODEL)
            try:
                response = self.openai_client.chat.completions.create(
                    model=active_model,
                    messages=self.openai_messages,
                    tools=OPENAI_TOOLS,
                    tool_choice="auto",
                    temperature=0.7,
                )
            except Exception:
                # Если модель на бесплатном пуле не поддерживает tools schema, вызываем без tools
                response = self.openai_client.chat.completions.create(
                    model=active_model,
                    messages=self.openai_messages,
                    temperature=0.7,
                )


            msg = response.choices[0].message

            # Если нейросеть вызвала функцию
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_results = []
                for tc in msg.tool_calls:
                    fn_name = tc.function.name
                    fn_args = {}
                    try:
                        fn_args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                    except Exception:
                        pass

                    print(f"[Tool Call] {fn_name}({fn_args})")
                    if fn_name in FUNCTIONS_MAP:
                        try:
                            res = FUNCTIONS_MAP[fn_name](**fn_args)
                        except Exception as ex:
                            res = f"Ошибка: {ex}"
                    else:
                        res = f"Функция {fn_name} не найдена."

                    print(f"[Tool Result] {res}")
                    tool_results.append(str(res))

                self.openai_messages.append(msg)
                return " ".join(tool_results)

            answer = msg.content or "Слушаюсь и повинуюсь!"
            self.openai_messages.append({"role": "assistant", "content": answer})
            return answer

        except Exception as e:
            print(f"[OpenAI/OpenRouter Error]: {e}")
            if self.gemini_chat:
                print("[Brain] Автоматическое переключение на резервный Gemini...")
                return self._process_gemini(user_text)
            return "Произошла ошибка при обращении к нейросети. Попробуйте еще раз."

    def _process_gemini(self, user_text: str) -> str:
        """Обработка через Google Gemini с одношаговым выполнением инструментов."""
        try:
            print(f"[User]: {user_text}")
            response = self.gemini_chat.send_message(user_text)

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

                # Фоновая синхронизация контекста
                import threading
                def _sync_chat():
                    try:
                        self.gemini_chat.send_message(function_responses)
                    except Exception:
                        pass
                threading.Thread(target=_sync_chat, daemon=True).start()

                return " ".join(tool_results)

            return response.text or "Слушаюсь и повинуюсь!"

        except Exception as e:
            err_msg = str(e)
            print(f"[Brain Process Error]: {err_msg}")

            if "User location is not supported" in err_msg or "FAILED_PRECONDITION" in err_msg:
                print("\n" + "!" * 60)
                print(" ⚠️  РЕГИОНАЛЬНОЕ ОГРАНИЧЕНИЕ GOOGLE GEMINI:")
                print(" Google блокирует прямые запросы к AI Studio с IP-адресов РФ.")
                print(" Решение без VPN:")
                print("  Укажите бесплатный ключ OpenRouter (работает в РФ напрямую):")
                print("  OPENAI_API_KEY=sk-or-v1-... в файле .env")
                print("!" * 60 + "\n")
                return "Google ограничивает доступ из вашего региона. Подключите бесплатный OpenRouter (без VPN) в настройках .env."

            return "Произошла ошибка при обработке запроса. Попробуйте еще раз."


brain = AssistantBrain()

