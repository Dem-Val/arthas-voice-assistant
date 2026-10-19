import urllib.parse
import webbrowser


class WebTools:
    """Инструменты для работы с браузером и поиском в интернете."""

    @staticmethod
    def open_url(url: str) -> str:
        """Открывает указанный URL в браузере по умолчанию."""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        webbrowser.open(url)
        return f"Открываю {url}."

    @staticmethod
    def search_google(query: str) -> str:
        """Ищет информацию в Google через браузер."""
        encoded = urllib.parse.quote_plus(query.strip())
        url = f"https://www.google.com/search?q={encoded}"
        webbrowser.open(url)
        return f"Ищу в интернете: {query}."

    @staticmethod
    def play_youtube(query: str) -> str:
        """Ищет и включает видео или музыку на YouTube."""
        encoded = urllib.parse.quote_plus(query.strip())
        url = f"https://www.youtube.com/results?search_query={encoded}"
        webbrowser.open(url)
        return f"Ищу на YouTube: {query}."


web_tools = WebTools()
