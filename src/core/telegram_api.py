import asyncio
import os
from telethon import TelegramClient
from telethon.errors.rpcerrorlist import UsernameInvalidError, UsernameNotOccupiedError
from .config_loader import load_config

_cfg = load_config()
API_ID = _cfg.get("telegram_api_id")
API_HASH = _cfg.get("telegram_api_hash")

SESSION_NAME = "tg_session"
_client = None


def init_telegram(api_id=None, api_hash=None):
    global API_ID, API_HASH, _client

    if api_id:
        API_ID = api_id
    if api_hash:
        API_HASH = api_hash

    if _client is not None:
        try:
            asyncio.get_event_loop().create_task(_client.disconnect())
        except Exception:
            pass

    _client = None
    return True


def _create_client():
    global _client
    if _client is None and API_ID and API_HASH:
        _client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    return _client


async def _ensure_started():
    client = _create_client()
    if not client:
        return None

    if not client.is_connected():
        await client.connect()

    try:
        await client.start()
    except Exception:
        pass

    return client


async def scan_telegram(username: str):
    """Сканирует Telegram и скачивает фото."""

    if not API_ID or not API_HASH:
        return {"error": "telegram api_id/api_hash not set in config.json"}

    client = await _ensure_started()
    if not client:
        return {"error": "failed to initialize telegram client"}

    try:
        entity = await client.get_entity(username)
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
        "has_photo": bool(getattr(entity, "photo", None)),
        "link": f"https://t.me/{username}",
        "photo": None,
    }

    # Фото
    if info["has_photo"]:
        try:
            os.makedirs("cache", exist_ok=True)
            path = f"cache/tg_{username}.jpg"

            await client.download_profile_photo(entity, path)

            if os.path.exists(path):
                info["photo"] = path

        except Exception as e:
            print("Error downloading telegram photo:", e)
            info["photo"] = None

    return info
