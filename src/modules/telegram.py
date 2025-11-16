# src/modules/telegram.py
import os
import asyncio
from telethon import TelegramClient
from telethon.errors.rpcerrorlist import UsernameInvalidError, UsernameNotOccupiedError

_client: TelegramClient | None = None
SESSION_NAME = "tg_session"

async def initialize(module_config: dict):
    """
    Инициализирует объект клиента Telethon, но НЕ подключается.
    Подключение произойдет "лениво" при первом вызове scan.
    """
    global _client
    api_id = module_config.get("api_id")
    api_hash = module_config.get("api_hash")

    if not api_id or not api_hash:
        print("[!] Telegram api_id/api_hash не найдены в config.json. Модуль отключен.")
        return

    _client = TelegramClient(SESSION_NAME, api_id, api_hash)
    print("[*] Клиент Telegram инициализирован (не подключен).")

async def _ensure_connected():
    """Удостоверяется, что клиент подключен, и авторизуется при необходимости."""
    if _client and not _client.is_connected():
        try:
            print("[*] Выполняется подключение к Telegram...")
            await _client.connect()
            print("[*] Подключение к Telegram успешно.")
        except Exception as e:
            print(f"[!] Не удалось подключиться к Telegram: {e}")
            return False
    return _client and _client.is_connected()

async def shutdown():
    """Отключает клиент Telethon, если он был подключен."""
    if _client and _client.is_connected():
        await _client.disconnect()
        print("[*] Клиент Telegram отключен.")

async def scan(username: str):
    """Сканирует Telegram и скачивает фото."""
    if not await _ensure_connected():
        return {"error": "Клиент Telegram не подключен"}

    try:
        entity = await _client.get_entity(username)
    except (UsernameInvalidError, UsernameNotOccupiedError, ValueError):
        return None
    except Exception as e:
        return {"error": str(e)}

    info = {
        "id": getattr(entity, "id", None),
        "username": getattr(entity, "username", None),
        "first_name": getattr(entity, "first_name", None),
        "last_name": getattr(entity, "last_name", None),
        "is_bot": getattr(entity, "bot", False),
        "link": f"https://t.me/{username}",
        "photo": None,
    }

    if getattr(entity, "photo", None):
        try:
            os.makedirs("cache", exist_ok=True)
            path = f"cache/tg_{username}.jpg"
            await _client.download_profile_photo(entity, path)
            if os.path.exists(path):
                info["photo"] = path
        except Exception as e:
            print(f"Ошибка загрузки фото Telegram: {e}")

    return info

def format_result_for_gui(data: dict, username: str):
    """Форматирует данные от API для отображения в ResultCard."""
    subtitle = " ".join(filter(None, [data.get("first_name", ""), data.get("last_name", "")]))
    return {
        "title": f"{username} - Telegram",
        "subtitle": subtitle,
        "avatar_url": data.get("photo"),
        "details": {
            "ID": data.get("id"),
            "Username": data.get("username"),
            "Бот": "Да" if data.get("is_bot") else "Нет",
        }
    }