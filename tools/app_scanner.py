import os
import re
import glob
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from rapidfuzz import fuzz, process
except ImportError:
    # Запасной вариант на случай, если библиотека ещё не установлена
    fuzz = None
    process = None


# Системные команды и утилиты Windows
BUILTIN_APPS: Dict[str, str] = {
    "калькулятор": "calc.exe",
    "блокнот": "notepad.exe",
    "проводник": "explorer.exe",
    "диспетчер задач": "taskmgr.exe",
    "командная строка": "cmd.exe",
    "терминал": "wt.exe",
    "панель управления": "control.exe",
    "параметры": "ms-settings:",
    "настройки": "ms-settings:",
    "ножницы": "snippingtool.exe",
    "рисунок": "mspaint.exe",
    "paint": "mspaint.exe",
    "wordpad": "write.exe",
}

# Синонимы и сленг для популярных программ
APP_ALIASES: Dict[str, str] = {
    # Браузеры
    "опера": "opera",
    "оперу": "opera",
    "оперы": "opera",
    "опере": "opera",
    "opera": "opera",
    "хром": "chrome",
    "хрома": "chrome",
    "хроме": "chrome",
    "гугл": "chrome",
    "гугл хром": "chrome",
    "google chrome": "chrome",
    "яндекс": "yandex",
    "яндекса": "yandex",
    "яндекс браузер": "yandex",
    "yandex": "yandex",
    "эдж": "edge",
    "эджа": "edge",
    "edge": "edge",
    "мазила": "firefox",
    "файрфокс": "firefox",
    "фаерфокс": "firefox",
    "firefox": "firefox",

    # Мессенджеры и связь
    "телега": "telegram",
    "телегу": "telegram",
    "телеграм": "telegram",
    "телеграмм": "telegram",
    "телеграме": "telegram",
    "тг": "telegram",
    "telegram": "telegram",
    "дискорд": "discord",
    "дискорда": "discord",
    "дискорде": "discord",
    "дс": "discord",
    "discord": "discord",
    "ватсап": "whatsapp",
    "вацап": "whatsapp",
    "whatsapp": "whatsapp",

    # Игры и платформы
    "стим": "steam",
    "стима": "steam",
    "стиме": "steam",
    "steam": "steam",
    "эпик": "epic games",
    "эпик геймс": "epic games",

    # Музыка и медиа
    "музыка": "spotify",
    "спотифай": "spotify",
    "спотифая": "spotify",
    "споти": "spotify",
    "spotify": "spotify",
    "аимп": "aimp",
    "vlc": "vlc",

    # Разработка и редакторы
    "пайчарм": "pycharm",
    "пичарм": "pycharm",
    "пай чарм": "pycharm",
    "чарм": "pycharm",
    "pycharm": "pycharm",
    "вс код": "code",
    "вскод": "code",
    "vs code": "code",
    "код": "code",
    "вижуал студио": "visual studio",
    "нотпад": "notepad++",
    "ноутпад": "notepad++",
    "notepad++": "notepad++",

    # Офис
    "ворд": "word",
    "ворда": "word",
    "word": "word",
    "эксель": "excel",
    "экселя": "excel",
    "ексель": "excel",
    "excel": "excel",
    "поверпоинт": "powerpoint",
    "паверпоинт": "powerpoint",
    "презентация": "powerpoint",
    "powerpoint": "powerpoint",

    # Прочее
    "торрент": "torrent",
    "торрента": "torrent",
    "qbittorrent": "qbittorrent",
    "utorrent": "utorrent",
}


class WindowsAppScanner:
    """
    Динамический сканер приложений Windows.
    Находит установленные программы через ярлыки меню «Пуск», рабочий стол и реестр.
    Не требует жестко заданных путей!
    """

    def __init__(self):
        self.apps_cache: Dict[str, str] = {}
        self.refresh_cache()

    def _get_search_dirs(self) -> List[Path]:
        dirs = []
        appdata = os.environ.get("APPDATA")
        allusers = os.environ.get("ALLUSERSPROFILE", r"C:\ProgramData")
        userprofile = os.environ.get("USERPROFILE")

        # Меню «Пуск» пользователя и общее
        if appdata:
            dirs.append(Path(appdata) / r"Microsoft\Windows\Start Menu\Programs")
        if allusers:
            dirs.append(Path(allusers) / r"Microsoft\Windows\Start Menu\Programs")

        # Рабочие столы
        if userprofile:
            dirs.append(Path(userprofile) / "Desktop")
        dirs.append(Path(r"C:\Users\Public\Desktop"))

        return [d for d in dirs if d.exists()]

    def refresh_cache(self):
        """Сканирует систему и обновляет кэш доступных программ."""
        self.apps_cache.clear()

        # 1. Добавляем системные программы
        for name, cmd in BUILTIN_APPS.items():
            self.apps_cache[name.lower()] = cmd

        # 2. Сканируем ярлыки (.lnk и .url)
        for directory in self._get_search_dirs():
            try:
                for file_path in directory.rglob("*"):
                    if file_path.suffix.lower() in [".lnk", ".url"]:
                        clean_name = file_path.stem.lower()
                        # Убираем лишние приписки типа " (64-bit)" или " - ярлык"
                        clean_name = re.sub(r"\s*\((?:32|64)[-\s]*bit\)", "", clean_name)
                        clean_name = re.sub(r"\s*-\s*ярлык", "", clean_name)
                        clean_name = clean_name.strip()

                        # Игнорируем деинсталляторы и справку
                        if any(bad in clean_name for bad in ["uninstall", "удалить", "help", "справка", "readme"]):
                            continue

                        if clean_name and clean_name not in self.apps_cache:
                            self.apps_cache[clean_name] = str(file_path)
            except Exception:
                continue

    def _normalize_query(self, query: str) -> str:
        q = query.strip().lower()
        # Удаляем вводные слова
        for word in ["запусти", "открой", "включи", "вруби", "программу", "приложение", "плиз", "пожалуйста"]:
            q = re.sub(rf"\b{word}\b", "", q)
        q = q.strip(",.!? \t\n")

        # Если остался только браузер - не удаляем его
        if q in ["браузер", "browser", "интернет", "инет"]:
            return "браузер"

        # Если есть "браузер opera" или "браузер хром", убираем слово "браузер"
        if " " in q and "браузер" in q:
            q = re.sub(r"\bбраузер[а-я]*\b", "", q).strip(",.!? \t\n")

        # Проверяем полное совпадение с синонимами
        if q in APP_ALIASES:
            return APP_ALIASES[q]

        # Заменяем токены по синонимам и стеммингу
        tokens = q.split()
        mapped_tokens = []
        for t in tokens:
            if t in APP_ALIASES:
                mapped_tokens.append(APP_ALIASES[t])
            else:
                # Базовый стемминг русских окончаний существительных
                stemmed = t
                if len(t) > 3:
                    if t.endswith(("у", "ю")):
                        stemmed = t[:-1] + "а"
                    elif t.endswith(("а", "я", "е", "ом", "ем")):
                        stemmed = t[:-1] if not t.endswith(("ом", "ем")) else t[:-2]
                mapped_tokens.append(APP_ALIASES.get(stemmed, t))

        return " ".join(mapped_tokens).strip()

    def find_app(self, query: str) -> Optional[Tuple[str, str]]:
        """
        Ищет приложение по названию с использованием точного, подстрочного и нечеткого поиска.
        Возвращает кортеж (имя_приложения, путь_к_файлу) или None.
        """
        norm_query = self._normalize_query(query)
        if not norm_query:
            return None

        # Специальная обработка запроса "браузер": находим установленный браузер
        if norm_query in ["браузер", "browser", "интернет", "инет"]:
            for b in ["opera", "chrome", "yandex", "firefox", "edge"]:
                for name, path in self.apps_cache.items():
                    if b in name:
                        return name, path
            # Системный браузер Windows Edge по умолчанию
            return "браузер", "msedge.exe"

        # 1. Прямое совпадение
        if norm_query in self.apps_cache:
            return norm_query, self.apps_cache[norm_query]

        # 2. Поиск по отдельным словам в названиях (например "opera" в "браузер opera")
        for app_name, app_path in self.apps_cache.items():
            tokens = [t.strip() for t in re.split(r"[\s\-_]+", app_name)]
            if norm_query in tokens or any(norm_query == t for t in tokens):
                return app_name, app_path


        # 3. Поиск подстроки
        for app_name, app_path in self.apps_cache.items():
            if norm_query in app_name or app_name in norm_query:
                return app_name, app_path

        # 4. Нечеткий поиск (Fuzzy Matching через RapidFuzz)
        if fuzz and self.apps_cache:
            names = list(self.apps_cache.keys())
            best_match, score, _ = process.extractOne(norm_query, names, scorer=fuzz.token_set_ratio)
            if score >= 65:
                return best_match, self.apps_cache[best_match]

            # Дополнительная попытка по token_sort_ratio
            best_sort, sort_score, _ = process.extractOne(norm_query, names, scorer=fuzz.token_sort_ratio)
            if sort_score >= 65:
                return best_sort, self.apps_cache[best_sort]

        return None

    def launch(self, query: str) -> str:
        """
        Находит и запускает программу.
        Возвращает понятное текстовое сообщение для ассистента.
        """
        result = self.find_app(query)
        if not result:
            # Для чистых латинских системных команд (calc, cmd, notepad, wt)
            q_clean = query.strip().lower()
            if q_clean.isascii() and len(q_clean.split()) == 1:
                try:
                    subprocess.Popen(q_clean, shell=True)
                    return f"Открываю: {query}"
                except Exception:
                    pass
            return f"Не удалось найти приложение '{query}'. Проверьте, установлено ли оно."

        app_name, app_path = result
        try:
            if app_path.startswith("ms-settings:"):
                os.system(f"start {app_path}")
            elif app_path.endswith(".exe"):
                subprocess.Popen(app_path, shell=True)
            else:
                os.startfile(app_path)
            return f"Открываю {app_name}."
        except Exception as e:
            return f"Ошибка при запуске {app_name}: {e}"


# Синглтон для повторного использования
app_scanner = WindowsAppScanner()

