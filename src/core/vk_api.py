# src/core/vk_api.py
import asyncio
from .config_loader import load_config
from .http_client import HttpClient

_cfg = load_config()
VK_TOKEN = _cfg.get("vk_token")
VK_API_VERSION = "5.199"

async def scan_vk(username: str):
    """Асинхронный сканер VK через официальное API с ограничением запросов."""
    if not VK_TOKEN:
        return {"error": "vk_token not set in config.json"}

    url = "https://api.vk.com/method/users.get"
    params = {
        "user_ids": username,
        "fields": "photo_max,city,domain,sex,bdate,status,contacts",
        "access_token": VK_TOKEN,
        "v": VK_API_VERSION
    }

    session = HttpClient.get_session()
    semaphore = HttpClient.get_vk_semaphore()

    try:
        # Ожидаем "свободного слота" для выполнения запроса
        async with semaphore:
            # Добавляем небольшую задержку для надежности, чтобы не превышать лимит "в секунду"
            await asyncio.sleep(0.35)
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return {"error": f"VK HTTP {resp.status}"}
                
                # ИСПРАВЛЕНИЕ: Добавляем content_type=None, чтобы обойти строгую проверку aiohttp,
                # так как API VK может присылать заголовок 'application/json; charset=utf-8'.
                data = await resp.json(content_type=None)

                if "error" in data:
                    return {"error": data["error"].get("error_msg", data["error"])}

                resp_list = data.get("response")
                if not resp_list:
                    return None

                user = resp_list[0]
                user["link"] = f"https://vk.com/{user.get('domain')}"
                return user

    except asyncio.TimeoutError:
        return {"error": "timeout"}
    except Exception as e:
        return {"error": str(e)}