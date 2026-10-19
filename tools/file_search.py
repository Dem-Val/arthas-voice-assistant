import os
import subprocess
from pathlib import Path
from typing import List, Optional

try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None


class FileSearchTool:
    """Умный поиск и открытие файлов на компьютере."""

    def __init__(self):
        user_profile = Path(os.environ.get("USERPROFILE", "C:\\Users\\Default"))
        self.priority_folders = [
            user_profile / "Desktop",
            user_profile / "Downloads",
            user_profile / "Documents",
            user_profile / "Pictures",
            user_profile / "Videos",
            user_profile / "Music",
            Path("A:\\"),
        ]
        # Отфильтруем только существующие папки
        self.priority_folders = [p for p in self.priority_folders if p.exists()]

    def search_files(self, query: str, max_depth: int = 3, limit: int = 5) -> List[Path]:
        """
        Ищет файлы по запросу в приоритетных пользовательских папках.
        """
        query_lower = query.strip().lower()
        matches = []

        for base_dir in self.priority_folders:
            try:
                for root, dirs, files in os.walk(base_dir):
                    depth = len(Path(root).relative_to(base_dir).parts)
                    if depth > max_depth:
                        dirs.clear()
                        continue

                    # Пропускаем скрытые и служебные папки
                    dirs[:] = [d for d in dirs if not d.startswith((".", "$")) and d not in ["AppData", "node_modules", ".git"]]

                    for file in files:
                        file_lower = file.lower()
                        # Точное или подстрочное совпадение
                        if query_lower in file_lower:
                            matches.append(Path(root) / file)
                            if len(matches) >= limit:
                                return matches
            except Exception:
                continue

        return matches

    def open_file_by_name(self, filename: str) -> str:
        """Находит файл и открывает его подходящей программой."""
        results = self.search_files(filename)
        if not results:
            return f"Не удалось найти файл '{filename}' в ваших основных папках."

        best_file = results[0]
        try:
            os.startfile(str(best_file))
            return f"Открыла файл {best_file.name}."
        except Exception as e:
            return f"Файл найден ({best_file.name}), но возникла ошибка при открытии: {e}"

    def show_in_folder(self, filename: str) -> str:
        """Находит файл и выделяет его в проводнике Windows."""
        results = self.search_files(filename)
        if not results:
            return f"Не удалось найти файл '{filename}'."

        best_file = results[0]
        try:
            subprocess.Popen(f'explorer /select,"{best_file}"')
            return f"Показываю {best_file.name} в папке."
        except Exception as e:
            return f"Ошибка открытия проводника: {e}"


file_search = FileSearchTool()
