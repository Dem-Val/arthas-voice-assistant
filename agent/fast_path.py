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

        # 0.2 Ввод в поисковую строку браузера (Ctrl+L -> вставить текст -> Enter)
        # Примеры: "напиши в строку поиска в браузере ютуб", "введи в поиск ютуб", "напиши в строке поиска котики"
        browser_type_match = re.match(
            r"^(?:напиши|введи|вбей|найди)\s+(?:в\s+строку\s+поиска\s+(?:в\s+браузере\s+)?|в\s+строке\s+поиска\s+(?:в\s+браузере\s+)?|в\s+поисковую\s+строку\s+(?:в\s+браузере\s+)?|в\s+поиск\s+(?:в\s+браузере\s+)?|в\s+браузере\s+в\s+поиск\s+|в\s+браузере\s+)(.+)$",
            clean,
        )
        if browser_type_match:
            query = browser_type_match.group(1).strip()
            print(f"[FastPath] Ввод в поисковую строку браузера: {query}")
            return SystemControl.browser_search_or_type(query, press_enter=True)

        # 0.3 Печать произвольного текста в активное окно
        # Примеры: "напечатай привет", "введи текст 123", "напиши ютуб" (если не совпало выше)
        type_match = re.match(r"^(?:напечатай|введи\s+текст)\s+(.+)$", clean)
        if type_match:
            text = type_match.group(1).strip()
            print(f"[FastPath] Печать текста в активное окно: {text}")
            return SystemControl.type_text(text, press_enter=False)

        # 0.4 Нажатие клавиш (Enter, Space, Backspace, Esc, Tab, F11)
        if clean in ["нажми энтер", "нажми ввод", "энтер", "ввод", "жми энтер"]:
            print("[FastPath] Нажатие клавиши Enter")
            return SystemControl.press_key("enter")

        if clean in ["нажми пробел", "пробел", "жми пробел"]:
            print("[FastPath] Нажатие клавиши Space")
            return SystemControl.press_key("space")

        if clean in ["нажми эскейп", "эскейп", "нажми esc", "отмена"]:
            print("[FastPath] Нажатие клавиши Escape")
            return SystemControl.press_key("escape")

        if clean in ["сотри", "удали", "бэкспейс", "бекспейс", "нажми бэкспейс"]:
            print("[FastPath] Нажатие клавиши Backspace")
            return SystemControl.press_key("backspace")

        if clean in ["нажми таб", "таб"]:
            print("[FastPath] Нажатие клавиши Tab")
            return SystemControl.press_key("tab")

        # 0.5 Прокрутка экрана / страниц
        if any(p in clean for p in ["прокрути вниз", "пролистай вниз", "скролл вниз", "чуть ниже", "листай вниз"]):
            print("[FastPath] Прокрутка вниз")
            return SystemControl.scroll_screen("down")

        if any(p in clean for p in ["прокрути вверх", "пролистай вверх", "скролл вверх", "чуть выше", "листай вверх"]):
            print("[FastPath] Прокрутка вверх")
            return SystemControl.scroll_screen("up")

        # 0.6 Управление окнами
        if any(clean == p for p in ["закрой окно", "закрой программу", "закрой приложение"]):
            print("[FastPath] Закрытие активного окна (Alt+F4)")
            return SystemControl.close_active_window()

        if any(clean == p for p in ["переключи окно", "следующее окно", "смени окно"]):
            print("[FastPath] Переключение окна (Alt+Tab)")
            return SystemControl.switch_window()

        if any(clean == p for p in ["на весь экран", "полный экран"]):
            print("[FastPath] Полный экран (F11)")
            return SystemControl.press_key("f11")

        if any(clean == p for p in ["выдели всё", "выделить всё"]):
            return SystemControl.press_hotkey("ctrl+a")

        if any(clean == p for p in ["скопируй", "скопировать"]):
            return SystemControl.press_hotkey("ctrl+c")

        if any(clean == p for p in ["вставь", "вставить"]):
            return SystemControl.press_hotkey("ctrl+v")


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
