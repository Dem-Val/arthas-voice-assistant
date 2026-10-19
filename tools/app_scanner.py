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
    "телега": "telegram",
    "телегу": "telegram",
    "телеграм": "telegram",
    "хром": "chrome",
    "гугл": "chrome",
    "гугл хром": "google chrome",
    "яндекс": "yandex",
    "яндекс браузер": "yandex",
    "опера": "opera",
    "opera": "opera",
    "стим": "steam",
    "дискорд": "discord",
    "музыка": "spotify",
    "спотифай": "spotify",
    "вс код": "code",
    "код": "code",
    "vs code": "code",
    "ворд": "word",
    "эксель": "excel",
    "поверпоинт": "powerpoint",
    "торрент": "torrent",
    "эдж": "edge",
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
        for word in ["запусти", "открой", "включи", "программу", "приложение", "плиз", "пожалуйста"]:
            q = re.sub(rf"\b{word}\b", "", q)
        q = q.strip()
        # Проверяем синонимы
        if q in APP_ALIASES:
            q = APP_ALIASES[q]
        return q

    def find_app(self, query: str) -> Optional[Tuple[str, str]]:
        """
        Ищет приложение по названию с использованием точного, подстрочного и нечеткого поиска.
        Возвращает кортеж (имя_приложения, путь_к_файлу) или None.
        """
        norm_query = self._normalize_query(query)
        if not norm_query:
            return None

        # 1. Прямое совпадение
        if norm_query in self.apps_cache:
            return norm_query, self.apps_cache[norm_query]

        # 2. Поиск по отдельным словам в названиях (например "opera" в "браузер opera")
        for app_name, app_path in self.apps_cache.items():
            tokens = [t.strip() for t in re.split(r"[\s\-_]+", app_name)]
            if norm_query in tokens:
                return app_name, app_path

        # 3. Поиск подстроки
        for app_name, app_path in self.apps_cache.items():
            if norm_query in app_name:
                return app_name, app_path

        # 4. Нечеткий поиск (Fuzzy Matching)
        if fuzz and self.apps_cache:
            names = list(self.apps_cache.keys())
            best_match, score, _ = process.extractOne(norm_query, names, scorer=fuzz.token_set_ratio)
            if score >= 65:
                return best_match, self.apps_cache[best_match]

        return None

    def launch(self, query: str) -> str:
        """
        Находит и запускает программу.
        Возвращает понятное текстовое сообщение для ассистента.
        """
        result = self.find_app(query)
        if not result:
            # Попытка прямого запуска через shell Windows (например, если сказали calc или cmd)
            try:
                subprocess.Popen(query.strip(), shell=True)
                return f"Открываю: {query}"
            except Exception:
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
