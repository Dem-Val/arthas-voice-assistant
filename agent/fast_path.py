import re
from typing import Optional
from tools.app_scanner import app_scanner
from tools.system_control import SystemControl
from tools.web_tools import web_tools


class FastPathRouter:
    """
    Быстрый локальный роутер команд (Fast Path).
    Выполняет популярные системные команды мгновенно (за 0.01-0.05 сек)
    БЕЗ отправки в облачную нейросеть, экономя время пользователя и трафик.
    """

    def try_handle(self, command: str) -> Optional[str]:
        if not command:
            return None

        clean = command.lower().strip()
        clean = re.sub(r"^[,.\s!?]+|[,.\s!?]+$", "", clean)

        # 0. Быстрый запуск браузера
        if clean in ["открой браузер", "запусти браузер", "браузер", "включи браузер", "открой интернет", "интернет"]:
            print("[FastPath] Мгновенное открытие браузера")
            return app_scanner.launch("браузер")

        # 0.1 Управление вкладками браузера (мгновенные горячие клавиши)
        if any(p in clean for p in ["новую вкладку", "новая вкладка", "открой вкладку", "создай вкладку", "вкладку в бра", "вкладку в браузер"]):
            print("[FastPath] Открытие новой вкладки браузера (Ctrl+T)")
            return SystemControl.new_browser_tab()

        if any(p in clean for p in ["закрой вкладку", "закрыть вкладку", "закрой эту вкладку"]):
            print("[FastPath] Закрытие вкладки браузера (Ctrl+W)")
            return SystemControl.close_browser_tab()

        if any(p in clean for p in ["верни вкладку", "открой закрытую вкладку", "восстанови вкладку"]):
            print("[FastPath] Восстановление закрытой вкладки (Ctrl+Shift+T)")
            return SystemControl.reopen_closed_tab()

        if any(p in clean for p in ["следующая вкладка", "след вкладка", "переключи вкладку"]):
            print("[FastPath] Следующая вкладка (Ctrl+Tab)")
            return SystemControl.next_browser_tab()

        if any(p in clean for p in ["предыдущая вкладка", "пред вкладка"]):
            print("[FastPath] Предыдущая вкладка (Ctrl+Shift+Tab)")
            return SystemControl.prev_browser_tab()

        if any(p in clean for p in ["обнови страницу", "перезагрузи страницу", "обнови сайт", "обнови вкладку"]):
            print("[FastPath] Обновление страницы (F5)")
            return SystemControl.reload_page()


        # 1. Запуск приложений (открой / запусти / включи / вруби <приложение>)
        launch_match = re.match(
            r"^(?:открой|запусти|включи|вруби)\s+(?:программу\s+|приложение\s+|браузер\s+)?(.+)$",
            clean,
        )

        if launch_match:
            target = launch_match.group(1).strip()
            # Исключаем медиа-запросы, которые должны уйти в YouTube или плеер
            if not any(skip in target for skip in ["музык", "песн", "клип", "видео", "звук", "ютуб", "youtube"]):
                app_found = app_scanner.find_app(target)
                if app_found:
                    print(f"[FastPath] Мгновенный запуск приложения: {app_found[0]}")
                    return app_scanner.launch(target)

        # 2. Управление громкостью
        if any(clean == phrase for phrase in ["тише", "сделай тише", "потише", "убавь звук", "уменьши звук", "звук потише"]):
            print("[FastPath] Мгновенное изменение громкости: -15%")
            return SystemControl.change_volume(-15)

        if any(clean == phrase for phrase in ["громче", "сделай громче", "погромче", "прибавь звук", "увеличь звук", "звук погромче"]):
            print("[FastPath] Мгновенное изменение громкости: +15%")
            return SystemControl.change_volume(15)

        if any(clean == phrase for phrase in ["выключи звук", "включи звук", "без звука", "заглуши", "мут", "размут", "переключи звук"]):
            print("[FastPath] Мгновенное переключение звука (mute)")
            return SystemControl.mute_volume()

        # Громкость на конкретное число (например: "громкость 50", "звук на 30%")
        vol_match = re.match(r"^(?:поставь\s+)?(?:громкость|звук)\s+(?:на\s+)?(\d{1,3})\s*%?$", clean)
        if vol_match:
            val = int(vol_match.group(1))
            val = max(0, min(100, val))
            print(f"[FastPath] Установка громкости на {val}%")
            return SystemControl.set_volume(val)

        # 3. Управление окнами и рабочим столом
        if any(phrase in clean for phrase in ["сверни окна", "сверни все окна", "сверни всё", "свернуть окна", "покажи рабочий стол", "рабочий стол"]):
            print("[FastPath] Сворачивание всех окон")
            return SystemControl.minimize_all_windows()

        if any(phrase in clean for phrase in ["заблокируй пк", "заблокируй компьютер", "заблокируй комп", "заблокируй экран", "заблокируй"]):
            print("[FastPath] Блокировка ПК")
            return SystemControl.lock_pc()

        if any(phrase in clean for phrase in ["скриншот", "сделай скриншот", "снимок экрана", "сделай снимок экрана", "скрин"]):
            print("[FastPath] Снятие скриншота")
            return SystemControl.take_screenshot()

        # 4. Управление медиа-плеером Windows
        if any(clean == phrase for phrase in ["пауза", "поставь на паузу", "продолжи", "продолжить", "стоп музыка", "музыка на паузу"]):
            print("[FastPath] Пауза / Возобновление медиа")
            return SystemControl.media_play_pause()

        if any(phrase in clean for phrase in ["следующий трек", "следующая песня", "включи следующий трек", "след трек"]):
            print("[FastPath] Следующий трек")
            return SystemControl.media_next()

        if any(phrase in clean for phrase in ["предыдущий трек", "предыдущая песня", "пред трек"]):
            print("[FastPath] Предыдущий трек")
            return SystemControl.media_prev()

        # 5. Быстрый поиск в YouTube и Google
        yt_match = re.match(r"^(?:включи|найди|вруби|поставь)\s+(?:на\s+ютубе|на\s+youtube|в\s+ютубе)\s+(.+)$", clean)
        if yt_match:
            query = yt_match.group(1).strip()
            print(f"[FastPath] Открытие YouTube: {query}")
            return web_tools.play_youtube(query)

        g_match = re.match(r"^(?:найди\s+в\s+гугле|погугли|загугли)\s+(.+)$", clean)
        if g_match:
            query = g_match.group(1).strip()
            print(f"[FastPath] Google Поиск: {query}")
            return web_tools.search_google(query)

        # Если прямого быстрого пути нет — передаем запрос в нейросеть
        return None


fast_router = FastPathRouter()
