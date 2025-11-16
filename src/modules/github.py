# src/modules/github.py
import asyncio
from core.http_client import HttpClient
from datetime import datetime

async def scan(username: str):
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

def _format_iso_date(date_str: str | None) -> str:
    if not date_str: return ""
    try:
        # Формат: '2011-01-25T18:44:36Z'
        return datetime.fromisoformat(date_str.replace('Z', '+00:00')).strftime('%d %B %Y')
    except (ValueError, TypeError):
        return ""

def format_result_for_gui(data: dict, username: str):
    details = {}
    # ИНТЕЛЛЕКТУАЛЬНОЕ ФОРМАТИРОВАНИЕ: Добавляем поле, только если оно не пустое
    if company := data.get("company"): details["Компания"] = company
    if location := data.get("location"): details["Местоположение"] = location
    if created_at := _format_iso_date(data.get("created_at")): details["Дата регистрации"] = created_at
    if public_repos := data.get("public_repos"): details["Публичные репозитории"] = public_repos
    if followers := data.get("followers"): details["Подписчики"] = followers
    if blog := data.get("blog"): details["Сайт"] = blog
    if twitter := data.get("twitter_username"): details["Twitter"] = f"https://twitter.com/{twitter}"
    if bio := data.get("bio"): details["Описание"] = bio

    return {
        "title": f"{data.get('login', username)} - GitHub",
        "subtitle": data.get("name") or "",
        "avatar_url": data.get("avatar_url"),
        "details": details
    }