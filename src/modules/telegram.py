# src/modules/telegram.py
import os, asyncio
from telethon import TelegramClient, types
from telethon.tl.types import UserStatusOnline, UserStatusOffline, UserStatusRecently, UserStatusLastWeek, UserStatusLastMonth
from telethon.errors.rpcerrorlist import UsernameInvalidError, UsernameNotOccupiedError, FloodWaitError
from datetime import datetime
from core.data_model import NormalizedData

_client_cfg = {}
SESSION_NAME = "tg_session"

async def initialize(module_config:dict):
    """Просто сохраняет конфигурацию."""
    global _client_cfg
    _client_cfg = { "api_id": module_config.get("api_id"), "api_hash": module_config.get("api_hash") }

def get_client_config():
    """Возвращает сохраненную конфигурацию для создания клиента."""
    return _client_cfg

async def scan(username: str, client: TelegramClient):
    """
    Выполняет запрос, используя предоставленный, уже подключенный клиент.
    """
    print(f"[TELEGRAM] Запрос для '{username}'")
    if not (client and client.is_connected()):
        return {"error": "Клиент Telegram не предоставлен или не подключен"}
    
    try:
        entity = await client.get_entity(username)
    except FloodWaitError as e:
        # Если даже при таком подходе получаем FloodWait, просто пропускаем
        print(f"[TELEGRAM FLOOD] Получен FloodWait для '{username}' на {e.seconds}с. Запрос отменен.")
        return {"error": f"FloodWait ({e.seconds}с)"}
    except (UsernameInvalidError, UsernameNotOccupiedError, ValueError):
        return None
    except Exception as e:
        return {"error": str(e)}

    if not isinstance(entity, types.User):
        return None

    info={"id":entity.id,"username":entity.username,"first_name":entity.first_name,"last_name":entity.last_name,"is_bot":entity.bot,"status_text":_format_tg_status(getattr(entity,'status',None)),"link":f"https://t.me/{entity.username}"if entity.username else None}
    if getattr(entity, "photo", None):
        try:
            os.makedirs("cache", exist_ok=True)
            path=f"cache/tg_{username}.jpg"
            await client.download_profile_photo(entity, path)
            info["photo"] = path
        except Exception as e:
            print(f"Ошибка загрузки фото Telegram: {e}")
    return info

# ... (остальной код модуля без изменений) ...
def _format_tg_status(status)->str|None:
    if isinstance(status,UserStatusOnline):return f"Онлайн (до {status.expires.strftime('%H:%M')})"
    if isinstance(status,UserStatusOffline):return f"Был(а) в сети {status.was_online.strftime('%d.%m.%Y в %H:%M')}"
    if isinstance(status,UserStatusRecently):return"Был(а) в сети недавно"
    if isinstance(status,UserStatusLastWeek):return"Был(а) в сети на этой неделе"
    if isinstance(status,UserStatusLastMonth):return"Был(а) в сети в этом месяце"
    return None
def format_result_for_gui(data: dict, username: str):
    norm_data = NormalizedData.from_telegram_api(data); details = {};
    if profile_link := data.get("link"): details["Ссылка на профиль"] = profile_link
    if status := data.get("status_text"): details["Статус"] = status
    details["ID"] = data.get("id"); details["Username"] = norm_data.username; details["Бот"] = "Да" if data.get("is_bot") else "Нет"
    return {"title": f"{norm_data.username} - Telegram", "subtitle": f"{norm_data.first_name} {norm_data.last_name}".strip(), "avatar_url": data.get("photo"), "details": details, "normalized_data": norm_data}