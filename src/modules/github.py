# src/modules/github.py
import asyncio
from core.http_client import HttpClient
from datetime import datetime
from core.data_model import NormalizedData

_token: str | None = None
_headers: dict = {}

async def initialize(module_config: dict):
    global _token, _headers
    token_from_config = module_config.get("token")
    if isinstance(token_from_config, str) and token_from_config.strip():
        _token = token_from_config.strip()
        _headers = {"Authorization": f"Bearer {_token}"}
        print("[*] Модуль GitHub будет использовать токен авторизации.")
    else:
        print("[!] Токен GitHub не найден или пуст. Запросы будут анонимными с низким лимитом.")

async def shutdown():
    """Для этого модуля не требуется специальных действий при выключении."""
    pass

async def scan(username: str):
    print(f"[GITHUB] Запрос для '{username}'")
    url = f"https://api.github.com/users/{username}"
    session = HttpClient.get_session()
    
    try:
        async with session.get(url, headers=_headers) as resp:
            if resp.status == 404:
                return None
            if resp.status == 401:
                print(f"[GITHUB ERROR] Ошибка 401 для '{username}'. Неверный токен.")
                return {"error": "Ошибка авторизации GitHub"}
            if resp.status == 403:
                # API отвечает 403 при превышении лимита
                print(f"[GITHUB ERROR] HTTP 403 для '{username}'. Вероятно, превышен лимит запросов.")
                return {"error": "Превышен лимит запросов GitHub"}
            
            resp.raise_for_status() # Вызовет исключение для других ошибок 4xx/5xx
            return await resp.json()

    except asyncio.TimeoutError:
        print(f"[GITHUB ERROR] Таймаут для '{username}'")
        return {"error": "timeout"}
    except Exception as e:
        print(f"[GITHUB ERROR] Исключение для '{username}': {e}")
        return {"error": str(e)}

def _format_iso_date(date_str: str | None) -> str:
    if not date_str: return ""
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00')).strftime('%d %B %Y')
    except (ValueError, TypeError):
        return ""

def format_result_for_gui(data: dict, username: str):
    norm_data = NormalizedData.from_github_api(data)
    details = {}
    
    if profile_url := data.get("html_url"):
        details["Ссылка на профиль"] = profile_url
    if norm_data.company:
        details["Компания"] = norm_data.company
    if norm_data.city:
        details["Местоположение"] = norm_data.city
    if created_at := _format_iso_date(data.get("created_at")):
        details["Дата регистрации"] = created_at
    if public_repos := data.get("public_repos"):
        details["Публичные репозитории"] = public_repos
    if followers := data.get("followers"):
        details["Подписчики"] = followers
    if blog := data.get("blog"):
        if blog.strip():
            if not blog.startswith(('http://', 'https://')):
                details["Сайт"] = "http://" + blog
            else:
                details["Сайт"] = blog
    if twitter := data.get("twitter_username"):
        details["Twitter"] = f"https://twitter.com/{twitter}"
    if bio := data.get("bio"):
        details["Описание"] = bio

    return {
        "title": f"{norm_data.username} - GitHub",
        "subtitle": f"{norm_data.first_name} {norm_data.last_name}".strip(),
        "avatar_url": data.get("avatar_url"),
        "details": details,
        "normalized_data": norm_data
    }