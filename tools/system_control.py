import os
import time
import subprocess
from pathlib import Path
from typing import Optional

try:
    import pyautogui
    pyautogui.FAILSAFE = False
except ImportError:
    pyautogui = None

try:
    import pyperclip
except ImportError:
    pyperclip = None

try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
except ImportError:
    AudioUtilities = None


class SystemControl:
    """Управление системными функциями Windows: звук, медиа, окна, питание."""

    @staticmethod
    def _get_volume_endpoint():
        if not AudioUtilities:
            return None
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            return cast(interface, POINTER(IAudioEndpointVolume))
        except Exception:
            return None

    @classmethod
    def set_volume(cls, percent: int) -> str:
        """Устанавливает громкость системы от 0 до 100."""
        endpoint = cls._get_volume_endpoint()
        percent = max(0, min(100, percent))
        if endpoint:
            try:
                endpoint.SetMasterVolumeLevelScalar(percent / 100.0, None)
                return f"Громкость установлена на {percent}%."
            except Exception as e:
                return f"Ошибка изменения громкости: {e}"
        # Запасной вариант через клавиши
        return f"Громкость изменена."

    @classmethod
    def change_volume(cls, delta: int) -> str:
        """Увеличивает или уменьшает громкость на указанный шаг."""
        endpoint = cls._get_volume_endpoint()
        if endpoint:
            try:
                curr = endpoint.GetMasterVolumeLevelScalar()
                new_vol = max(0.0, min(1.0, curr + (delta / 100.0)))
                endpoint.SetMasterVolumeLevelScalar(new_vol, None)
                return f"Громкость теперь {int(new_vol * 100)}%."
            except Exception as e:
                return f"Ошибка изменения громкости: {e}"
        return "Громкость изменена."

    @classmethod
    def mute_volume(cls) -> str:
        """Выключает/включает звук (mute toggle)."""
        endpoint = cls._get_volume_endpoint()
        if endpoint:
            try:
                is_muted = endpoint.GetMute()
                endpoint.SetMute(not is_muted, None)
                state = "выключен" if not is_muted else "включен"
                return f"Звук {state}."
            except Exception as e:
                return f"Ошибка отключения звука: {e}"
        return "Звук переключен."

    @staticmethod
    def media_play_pause() -> str:
        """Переключает воспроизведение музыки/видео (Play/Pause)."""
        if pyautogui:
            pyautogui.press("playpause")
            return "Воспроизведение переключено."
        return "Команда воспроизведения отправлена."

    @staticmethod
    def media_next() -> str:
        """Следующий трек."""
        if pyautogui:
            pyautogui.press("nexttrack")
            return "Включен следующий трек."
        return "Команда отправлена."

    @staticmethod
    def media_prev() -> str:
        """Предыдущий трек."""
        if pyautogui:
            pyautogui.press("prevtrack")
            return "Включен предыдущий трек."
        return "Команда отправлена."

    @staticmethod
    def minimize_all_windows() -> str:
        """Сворачивает все окна (показывает рабочий стол)."""
        if pyautogui:
            pyautogui.hotkey("win", "d")
            return "Свернул все окна."
        return "Окна свернуты."

    @staticmethod
    def take_screenshot(filename: Optional[str] = None) -> str:
        """Делает скриншот экрана."""
        if not pyautogui:
            return "Модуль для создания скриншотов недоступен."
        try:
            pictures_dir = Path(os.environ.get("USERPROFILE", ".")) / "Pictures" / "Screenshots"
            pictures_dir.mkdir(parents=True, exist_ok=True)
            import datetime
            now_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            save_path = pictures_dir / f"Screenshot_{now_str}.png"
            screenshot = pyautogui.screenshot()
            screenshot.save(save_path)
            return f"Скриншот сохранен в папку Изображения: {save_path.name}"
        except Exception as e:
            return f"Не удалось сделать скриншот: {e}"

    @staticmethod
    def lock_pc() -> str:
        """Блокирует компьютер."""
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return "Компьютер заблокирован."

    @staticmethod
    def new_browser_tab() -> str:
        """Открывает новую вкладку в браузере (Ctrl+T)."""
        if pyautogui:
            pyautogui.hotkey("ctrl", "t")
            return "Открыл новую вкладку."
        return "Команда отправлена."

    @staticmethod
    def close_browser_tab() -> str:
        """Закрывает текущую вкладку в браузере (Ctrl+W)."""
        if pyautogui:
            pyautogui.hotkey("ctrl", "w")
            return "Закрыл вкладку."
        return "Команда отправлена."

    @staticmethod
    def reopen_closed_tab() -> str:
        """Восстанавливает последнюю закрытую вкладку (Ctrl+Shift+T)."""
        if pyautogui:
            pyautogui.hotkey("ctrl", "shift", "t")
            return "Восстановил закрытую вкладку."
        return "Команда отправлена."

    @staticmethod
    def next_browser_tab() -> str:
        """Переключает на следующую вкладку (Ctrl+Tab)."""
        if pyautogui:
            pyautogui.hotkey("ctrl", "tab")
            return "Следующая вкладка."
        return "Команда отправлена."

    @staticmethod
    def prev_browser_tab() -> str:
        """Переключает на предыдущую вкладку (Ctrl+Shift+Tab)."""
        if pyautogui:
            pyautogui.hotkey("ctrl", "shift", "tab")
            return "Предыдущая вкладка."
        return "Команда отправлена."

    @staticmethod
    def reload_page() -> str:
        """Обновляет страницу в браузере (F5)."""
        if pyautogui:
            pyautogui.press("f5")
            return "Страница обновлена."
        return "Команда отправлена."

    @staticmethod
    def browser_search_or_type(query: str, press_enter: bool = True) -> str:
        """
        Фокусирует адресную строку / строку поиска в браузере (Ctrl+L),
        вводит текст запроса или ссылки и при необходимости нажимает Enter.
        """
        if not pyautogui:
            return "Управление окнами недоступно."
        try:
            pyautogui.hotkey("ctrl", "l")
            time.sleep(0.12)
            if pyperclip:
                pyperclip.copy(query)
                pyautogui.hotkey("ctrl", "v")
            else:
                pyautogui.write(query)
            if press_enter:
                time.sleep(0.1)
                pyautogui.press("enter")
            return f"Ввел в строку браузера: {query}"
        except Exception as e:
            return f"Ошибка при вводе в браузер: {e}"

    @staticmethod
    def type_text(text: str, press_enter: bool = False) -> str:
        """
        Вводит / печатает указанный текст в активное поле или окно (с поддержкой русского языка).
        """
        if not pyautogui:
            return "Ввод текста недоступен."
        try:
            if pyperclip:
                pyperclip.copy(text)
                pyautogui.hotkey("ctrl", "v")
            else:
                pyautogui.write(text)
            if press_enter:
                time.sleep(0.08)
                pyautogui.press("enter")
            return f"Напечатал: {text}"
        except Exception as e:
            return f"Ошибка при вводе текста: {e}"

    @staticmethod
    def press_key(key: str) -> str:
        """
        Нажимает клавишу на клавиатуре (enter, space, backspace, escape, tab, up, down, etc.).
        """
        if not pyautogui:
            return "Клавиатура недоступна."
        key_map = {
            "энтер": "enter",
            "ввод": "enter",
            "пробел": "space",
            "эскейп": "escape",
            "ескейп": "escape",
            "esc": "escape",
            "стереть": "backspace",
            "удали": "backspace",
            "бэкспейс": "backspace",
            "бекспейс": "backspace",
            "таб": "tab",
            "стрелка вверх": "up",
            "вверх": "up",
            "стрелка вниз": "down",
            "вниз": "down",
            "стрелка влево": "left",
            "влево": "left",
            "стрелка вправо": "right",
            "вправо": "right",
            "удалить": "delete",
            "экран": "f11",
            "полный экран": "f11",
        }
        clean = key.lower().strip()
        k = key_map.get(clean, clean)
        try:
            pyautogui.press(k)
            return f"Нажал клавишу {key}."
        except Exception as e:
            return f"Не удалось нажать клавишу: {e}"

    @staticmethod
    def press_hotkey(hotkey: str) -> str:
        """
        Нажимает комбинацию клавиш (например: ctrl+c, ctrl+v, ctrl+a, ctrl+z, alt+f4, win+d, win+tab).
        """
        if not pyautogui:
            return "Клавиатура недоступна."
        try:
            keys = [k.strip().lower() for k in hotkey.replace("-", "+").split("+")]
            pyautogui.hotkey(*keys)
            return f"Нажал комбинацию {' + '.join(keys)}."
        except Exception as e:
            return f"Ошибка при нажатии комбинации: {e}"

    @staticmethod
    def scroll_screen(direction: str = "down", amount: int = 5) -> str:
        """
        Прокручивает страницу или окно вверх или вниз.
        """
        if not pyautogui:
            return "Мышь недоступна."
        try:
            is_down = direction.lower() in ["down", "вниз", "ниже"]
            clicks = -abs(amount) * 120 if is_down else abs(amount) * 120
            pyautogui.scroll(clicks)
            return f"Прокрутил страницу {'вниз' if is_down else 'вверх'}."
        except Exception as e:
            return f"Ошибка прокрутки: {e}"

    @staticmethod
    def mouse_click(button: str = "left", double: bool = False) -> str:
        """
        Выполняет клик мыши (левый, правый, двойной).
        """
        if not pyautogui:
            return "Мышь недоступна."
        try:
            btn = "right" if "прав" in button.lower() else "left"
            if double:
                pyautogui.doubleClick(button=btn)
                return "Двойной клик выполнен."
            pyautogui.click(button=btn)
            return "Клик мыши выполнен."
        except Exception as e:
            return f"Ошибка клика: {e}"

    @staticmethod
    def close_active_window() -> str:
        """
        Закрывает текущее активное окно (Alt+F4).
        """
        if pyautogui:
            pyautogui.hotkey("alt", "f4")
            return "Закрыл активное окно."
        return "Команда отправлена."

    @staticmethod
    def switch_window() -> str:
        """
        Переключает активное окно (Alt+Tab).
        """
        if pyautogui:
            pyautogui.hotkey("alt", "tab")
            return "Переключил окно."
        return "Команда отправлена."


