# src/modules/vk.py
import asyncio
from core.http_client import HttpClient
from datetime import datetime

_token: str | None = None
_api_version = "5.199"

async def initialize(module_config: dict):
    global _token
    _token = module_config.get("token")
    if not _token:
        print("[!] Токен VK не найден в config.json. Модуль отключен.")

async def scan(username: str):
    if not _token:
        return {"error": "vk_token не настроен"}
    
    # РАСШИРЕНИЕ СБОРА: Добавляем новые поля
    fields = "photo_max,city,domain,sex,bdate,status,contacts,last_seen,online,country,counters,occupation,site"
    url = "https://api.vk.com/method/users.get"
    params = {
        "user_ids": username,
        "fields": fields,
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

def _format_sex(sex_id: int) -> str:
    if sex_id == 1: return "Женский"
    if sex_id == 2: return "Мужской"
    return ""

def _format_timestamp(ts: int | None) -> str:
    if not ts: return ""
    return datetime.fromtimestamp(ts).strftime('%d %B %Y в %H:%M')

def format_result_for_gui(data: dict, username: str):
    full_name = f"{data.get('first_name', '')} {data.get('last_name', '')}"
    
    details = {}
    if online_status := data.get("online"):
        is_mobile = data.get("online_mobile")
        details["Статус"] = "Онлайн" + (" (моб.)" if is_mobile else "")
    elif last_seen := _format_timestamp(data.get('last_seen', {}).get('time')):
        details["Последний визит"] = last_seen
    
    if status := data.get("status"): details["Личный статус"] = status
    if sex := _format_sex(data.get("sex")): details["Пол"] = sex
    if bdate := data.get("bdate"): details["Дата рождения"] = bdate
    if country := (data.get("country") or {}).get("title"): details["Страна"] = country
    if city := (data.get("city") or {}).get("title"): details["Город"] = city
    if occupation := (data.get("occupation") or {}).get("name"): details["Место работы/учебы"] = occupation
    if followers := (data.get("counters") or {}).get("followers"): details["Подписчики"] = followers
    if site := data.get("site"): details["Сайт"] = site
    details["ID"] = data.get("id")

    return {
        "title": f"{data.get('domain', username)} - VK",
        "subtitle": full_name.strip(),
        "avatar_url": data.get("photo_max"),
        "details": details
    }