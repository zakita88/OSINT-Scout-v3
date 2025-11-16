# src/modules/telegram.py
import os
import asyncio
from telethon import TelegramClient
from telethon.tl.types import UserStatusOnline, UserStatusOffline, UserStatusRecently, UserStatusLastWeek, UserStatusLastMonth
from telethon.errors.rpcerrorlist import UsernameInvalidError, UsernameNotOccupiedError
from datetime import datetime

_client: TelegramClient | None = None
SESSION_NAME = "tg_session"

async def initialize(module_config: dict):
    global _client
    api_id = module_config.get("api_id")
    api_hash = module_config.get("api_hash")
    if not api_id or not api_hash:
        print("[!] Telegram api_id/api_hash не найдены в config.json. Модуль отключен.")
        return
    _client = TelegramClient(SESSION_NAME, api_id, api_hash)
    print("[*] Клиент Telegram инициализирован (не подключен).")

async def _ensure_connected():
    if _client and not _client.is_connected():
        try:
            await _client.connect()
        except Exception as e:
            print(f"[!] Не удалось подключиться к Telegram: {e}")
            return False
    return _client and _client.is_connected()

async def shutdown():
    if _client and _client.is_connected():
        await _client.disconnect()

def _format_tg_status(status) -> str | None:
    if isinstance(status, UserStatusOnline):
        return f"Онлайн (до {status.expires.strftime('%H:%M')})"
    if isinstance(status, UserStatusOffline):
        return f"Был(а) в сети {status.was_online.strftime('%d.%m.%Y в %H:%M')}"
    if isinstance(status, UserStatusRecently):
        return "Был(а) в сети недавно"
    if isinstance(status, UserStatusLastWeek):
        return "Был(а) в сети на этой неделе"
    if isinstance(status, UserStatusLastMonth):
        return "Был(а) в сети в этом месяце"
    return None

async def scan(username: str):
    if not await _ensure_connected():
        return {"error": "Клиент Telegram не подключен"}
    try:
        entity = await _client.get_entity(username)
    except (UsernameInvalidError, UsernameNotOccupiedError, ValueError):
        return None
    except Exception as e:
        return {"error": str(e)}

    info = {
        "id": entity.id,
        "username": entity.username,
        "first_name": entity.first_name,
        "last_name": entity.last_name,
        "is_bot": entity.bot,
        "link": f"https://t.me/{username}",
        "photo": None,
        "status_text": _format_tg_status(getattr(entity, 'status', None))
    }

    if getattr(entity, "photo", None):
        try:
            os.makedirs("cache", exist_ok=True)
            path = f"cache/tg_{username}.jpg"
            await _client.download_profile_photo(entity, path)
            if os.path.exists(path): info["photo"] = path
        except Exception as e:
            print(f"Ошибка загрузки фото Telegram: {e}")
    return info

def format_result_for_gui(data: dict, username: str):
    subtitle = " ".join(filter(None, [data.get("first_name", ""), data.get("last_name", "")]))
    details = {}
    if status := data.get("status_text"): details["Статус"] = status
    details["ID"] = data.get("id")
    details["Username"] = data.get("username")
    details["Бот"] = "Да" if data.get("is_bot") else "Нет"

    return {
        "title": f"{username} - Telegram",
        "subtitle": subtitle,
        "avatar_url": data.get("photo"),
        "details": details
    }