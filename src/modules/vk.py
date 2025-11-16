# src/modules/vk.py
import asyncio
from core.config_loader import load_config
from core.http_client import HttpClient

_token: str | None = None
_api_version = "5.199"

async def initialize(module_config: dict):
    """Получает токен из конфигурации модуля."""
    global _token
    _token = module_config.get("token")
    if not _token:
        print("[!] Токен VK не найден в config.json. Модуль отключен.")

async def scan(username: str):
    """Асинхронный сканер VK через API с ограничением запросов."""
    if not _token:
        return {"error": "vk_token не настроен"}

    url = "https://api.vk.com/method/users.get"
    params = {
        "user_ids": username,
        "fields": "photo_max,city,domain,sex,bdate,status,contacts",
        "access_token": _token,
        "v": _api_version
    }

    session = HttpClient.get_session()
    semaphore = HttpClient.get_vk_semaphore()

    try:
        async with semaphore:
            await asyncio.sleep(0.35)
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return {"error": f"VK HTTP {resp.status}"}
                
                data = await resp.json(content_type=None)
                if "error" in data:
                    return {"error": data["error"].get("error_msg", data["error"])}

                resp_list = data.get("response")
                return resp_list[0] if resp_list else None

    except asyncio.TimeoutError:
        return {"error": "timeout"}
    except Exception as e:
        return {"error": str(e)}

def format_result_for_gui(data: dict, username: str):
    """Форматирует данные от API для отображения в ResultCard."""
    full_name = f"{data.get('first_name', '')} {data.get('last_name', '')}"
    return {
        "title": f"{username} - VK",
        "subtitle": full_name.strip(),
        "avatar_url": data.get("photo_max"),
        "details": {
            "ID": data.get("id"),
            "Город": (data.get("city") or {}).get("title", ""),
            "Дата рождения": data.get("bdate"),
            "Статус": data.get("status"),
        }
    }