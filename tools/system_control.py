import os
import subprocess
from typing import Optional

try:
    import pyautogui
    pyautogui.FAILSAFE = False
except ImportError:
    pyautogui = None

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
