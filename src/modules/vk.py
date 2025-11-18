# src/modules/vk.py
import asyncio
from core.http_client import HttpClient
from datetime import datetime
from core.data_model import NormalizedData

_token:str|None=None; _api_version="5.199"
async def initialize(module_config:dict):
    global _token; _token=module_config.get("token")
    if not _token: print("[!] Токен VK не найден в config.json. Модуль отключен.")

async def scan_bulk(usernames: list[str]):
    print(f"[VK] Пакетный запрос для {len(usernames)} ников.")
    if not _token or not usernames: return {}
    user_ids_str = ",".join(usernames)
    fields = "photo_max,city,domain,sex,bdate,status,contacts,last_seen,online,country,counters,occupation,site"
    url = "https://api.vk.com/method/users.get"
    params = {"user_ids": user_ids_str, "fields": fields, "access_token": _token, "v": _api_version}
    session = HttpClient.get_session(); semaphore = HttpClient.get_vk_semaphore()
    try:
        async with semaphore:
            await asyncio.sleep(0.35)
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    print(f"[VK ERROR] Пакетный запрос вернул HTTP {resp.status}")
                    return {u: {"error": f"VK HTTP {resp.status}"} for u in usernames}
                data = await resp.json(content_type=None)
                if "error" in data:
                    print(f"[VK ERROR] API ВКонтакте вернуло ошибку: {data['error']}")
                    return {u: {"error": data["error"].get("error_msg")} for u in usernames}
                results_by_username = {}
                if response_list := data.get("response"):
                    print(f"[VK] Пакетный запрос вернул {len(response_list)} профилей.")
                    for user_data in response_list:
                        if domain := user_data.get("domain"):
                            results_by_username[domain] = user_data
                return results_by_username
    except Exception as e:
        print(f"[VK ERROR] Исключение при пакетном запросе: {e}")
        return {u: {"error": str(e)} for u in usernames}

async def scan(username: str):
    result_dict = await scan_bulk([username])
    return result_dict.get(username)

# ... (остальной код модуля vk.py без изменений) ...
def _format_sex(sex_id: int) -> str:
    if sex_id == 1: return "Женский";
    if sex_id == 2: return "Мужской";
    return ""
def _format_timestamp(ts: int | None) -> str:
    if not ts: return ""
    return datetime.fromtimestamp(ts).strftime('%d %B %Y в %H:%M')
def format_result_for_gui(data: dict, username: str):
    norm_data = NormalizedData.from_vk_api(data); details = {}
    if domain := data.get("domain"): details["Ссылка на профиль"] = f"https://vk.com/{domain}"
    if data.get("online"):
        is_mobile = data.get("online_mobile"); details["Статус"] = "Онлайн" + (" (моб.)" if is_mobile else "")
    elif last_seen := _format_timestamp(data.get('last_seen', {}).get('time')): details["Последний визит"] = last_seen
    if status := data.get("status"): details["Личный статус"] = status
    if sex := _format_sex(data.get("sex")): details["Пол"] = sex
    if bdate := data.get("bdate"): details["Дата рождения"] = bdate
    if norm_data.country: details["Страна"] = norm_data.country
    if norm_data.city: details["Город"] = norm_data.city
    if norm_data.company: details["Место работы/учебы"] = norm_data.company
    if followers := (data.get("counters") or {}).get("followers"): details["Подписчики"] = followers
    if site := data.get("site"):
        if site.strip(): details["Сайт"] = site
    details["ID"] = data.get("id")
    return {"title": f"{norm_data.username} - VK", "subtitle": f"{norm_data.first_name} {norm_data.last_name}".strip(), "avatar_url": data.get("photo_max"), "details": details, "normalized_data": norm_data}