import requests
from .config_loader import load_config

_cfg = load_config()
VK_TOKEN = _cfg.get("vk_token")
VK_API_VERSION = "5.131"

def get_vk_user(username: str):
    if not VK_TOKEN:
        return {"error": "vk_token not set in config.json"}

    url = "https://api.vk.com/method/users.get"
    params = {
        "user_ids": username,
        "fields": "photo_max,city,domain,sex,bdate,status,contacts",
        "access_token": VK_TOKEN,
        "v": VK_API_VERSION
    }

    try:
        r = requests.get(url, params=params, timeout=10, verify=True)
        data = r.json()
    except Exception as e:
        return {"error": str(e)}

    if "error" in data:
        return {"error": data["error"].get("error_msg", data["error"])}

    resp = data.get("response")
    if not resp:
        return None
    
    user = resp[0]
    user["link"] = f"https://vk.com/{user.get('domain')}"
    return user


async def scan_vk(username: str):
    """Асинхронный адаптер над синхронным VK API"""
    return get_vk_user(username)
