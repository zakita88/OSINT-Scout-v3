# src/modules/github.py
import asyncio
from core.http_client import HttpClient

async def scan(username: str):
    """
    Асинхронный GitHub сканер через официальное REST API.
    """
    url = f"https://api.github.com/users/{username}"
    session = HttpClient.get_session()

    try:
        async with session.get(url) as resp:
            if resp.status == 404:
                return None
            if resp.status != 200:
                return {"error": f"GitHub HTTP {resp.status}"}
            return await resp.json()
    except asyncio.TimeoutError:
        return {"error": "timeout"}
    except Exception as e:
        return {"error": str(e)}

def format_result_for_gui(data: dict, username: str):
    """Форматирует данные от API для отображения в ResultCard."""
    return {
        "title": f"{username} - GitHub",
        "subtitle": data.get("name") or "",
        "avatar_url": data.get("avatar_url"),
        "details": {
            "Публичные репозитории": data.get("public_repos"),
            "Подписчики": data.get("followers"),
            "Описание": data.get("bio"),
        }
    }