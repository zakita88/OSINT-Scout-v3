# src/modules/telegram.py
import os
import asyncio
from telethon import types
from telethon.errors.rpcerrorlist import UsernameInvalidError, UsernameNotOccupiedError, FloodWaitError
from datetime import datetime

from core.data_model import NormalizedData
from core.telegram_client import TelegramClientManager


async def initialize(module_config: dict):
    """Инициализирует глобальный клиент Telegram."""
    await TelegramClientManager.initialize(module_config)

async def shutdown():
    """Корректно отключает глобальный клиент Telegram."""
    await TelegramClientManager.close()

async def scan(username: str):
    """Выполняет запрос, используя общий, уже подключенный клиент."""
    try:
        client = TelegramClientManager.get_client()
    except RuntimeError as e:
        return {"error": str(e)}

    print(f"[TELEGRAM] Запрос для '{username}'")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            entity = await client.get_entity(username)
            break
        except FloodWaitError as e:
            if e.seconds > 60:
                print(f"[TELEGRAM FLOOD] Слишком долгое ожидание ({e.seconds}с) для '{username}'. Запрос отменен.")
                return {"error": f"FloodWait too long ({e.seconds}s)"}
            
            print(f"[TELEGRAM FLOOD] Получен FloodWait для '{username}' на {e.seconds}с. Ожидание...")
            await asyncio.sleep(e.seconds + 2)
            continue
        except (UsernameInvalidError, UsernameNotOccupiedError, ValueError):
            return None
        except Exception as e:
            return {"error": str(e)}
    else:
        return {"error": f"Failed after {max_retries} retries"}

    if not isinstance(entity, types.User):
        return None

    info = {
        "id": entity.id,
        "username": entity.username,
        "first_name": entity.first_name,
        "last_name": entity.last_name,
        "is_bot": entity.bot,
        "status_text": _format_tg_status(getattr(entity, 'status', None)),
        "link": f"https://t.me/{entity.username}" if entity.username else None
    }

    if getattr(entity, "photo", None):
        try:
            os.makedirs("cache", exist_ok=True)
            path = f"cache/tg_{username}.jpg"
            await client.download_profile_photo(entity, path)
            info["photo"] = path
        except Exception as e:
            print(f"Ошибка загрузки фото Telegram: {e}")
            
    return info


def _format_tg_status(status) -> str | None:
    if isinstance(status, types.UserStatusOnline):
        return f"Онлайн (до {status.expires.strftime('%H:%M')})"
    if isinstance(status, types.UserStatusOffline):
        return f"Был(а) в сети {status.was_online.strftime('%d.%m.%Y в %H:%M')}"
    if isinstance(status, types.UserStatusRecently):
        return "Был(а) в сети недавно"
    if isinstance(status, types.UserStatusLastWeek):
        return "Был(а) в сети на этой неделе"
    if isinstance(status, types.UserStatusLastMonth):
        return "Был(а) в сети в этом месяце"
    return None

def format_result_for_gui(data: dict, username: str):
    norm_data = NormalizedData.from_telegram_api(data)
    details = {}
    if profile_link := data.get("link"):
        details["Ссылка на профиль"] = profile_link
    if status := data.get("status_text"):
        details["Статус"] = status
    details["ID"] = data.get("id")
    details["Username"] = norm_data.username
    details["Бот"] = "Да" if data.get("is_bot") else "Нет"
    return {
        "title": f"{norm_data.username} - Telegram",
        "subtitle": f"{norm_data.first_name} {norm_data.last_name}".strip(),
        "avatar_url": data.get("photo"),
        "details": details,
        "normalized_data": norm_data
    }