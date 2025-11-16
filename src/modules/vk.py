# src/modules/vk.py
import asyncio
from core.http_client import HttpClient
from datetime import datetime
from core.data_model import NormalizedData

_token: str | None = None
_api_version = "5.199"

async def initialize(module_config: dict):
    """Инициализирует модуль, получая токен из конфигурации."""
    global _token
    _token = module_config.get("token")
    if not _token:
        print("[!] Токен VK не найден в config.json. Модуль отключен.")

async def scan(username: str):
    """Выполняет запрос к VK API для получения информации о пользователе."""
    if not _token:
        return {"error": "vk_token не настроен"}
    
    fields = "photo_max,city,domain,sex,bdate,status,contacts,last_seen,online,country,counters,occupation,site"
    url = "https://api.vk.com/method/users.get"
    params = {"user_ids": username, "fields": fields, "access_token": _token, "v": _api_version}
    
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
    """Преобразует числовой идентификатор пола в строку."""
    if sex_id == 1: return "Женский"
    if sex_id == 2: return "Мужской"
    return ""

def _format_timestamp(ts: int | None) -> str:
    """Форматирует timestamp в читаемую строку даты и времени."""
    if not ts:
        return ""
    return datetime.fromtimestamp(ts).strftime('%d %B %Y в %H:%M')

def format_result_for_gui(data: dict, username: str):
    """
    Адаптирует 'сырые' данные от API к единой модели NormalizedData и 
    формирует словарь для отображения в GUI.
    """
    # 1. Адаптируем данные к единой модели
    norm_data = NormalizedData.from_vk_api(data)
    
    # 2. Формируем словарь 'details' для отображения в карточке
    details = {}
    if domain := data.get("domain"):
        details["Ссылка на профиль"] = f"https://vk.com/{domain}"
        
    if data.get("online"):
        is_mobile = data.get("online_mobile")
        details["Статус"] = "Онлайн" + (" (моб.)" if is_mobile else "")
    elif last_seen := _format_timestamp(data.get('last_seen', {}).get('time')):
        details["Последний визит"] = last_seen
        
    if status := data.get("status"): details["Личный статус"] = status
    if sex := _format_sex(data.get("sex")): details["Пол"] = sex
    if bdate := data.get("bdate"): details["Дата рождения"] = bdate
    if norm_data.country: details["Страна"] = norm_data.country
    if norm_data.city: details["Город"] = norm_data.city
    if norm_data.company: details["Место работы/учебы"] = norm_data.company
    if followers := (data.get("counters") or {}).get("followers"):
        details["Подписчики"] = followers
    if site := data.get("site"):
        if site.strip(): details["Сайт"] = site
    details["ID"] = data.get("id")

    # 3. Возвращаем итоговый словарь для создания ResultCard
    return {
        "title": f"{norm_data.username} - VK",
        "subtitle": f"{norm_data.first_name} {norm_data.last_name}".strip(),
        "avatar_url": data.get("photo_max"),
        "details": details,
        "normalized_data": norm_data  # Передаем нормализованную модель в GUI
    }