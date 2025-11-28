# setup_telegram.py
import asyncio
import json
from pathlib import Path
from telethon import TelegramClient

SESSION_NAME = "tg_session"

async def main():
    """
    Скрипт для одноразовой авторизации и создания файла сессии Telegram.
    """
    print("--- Telegram Session Setup ---")
    
    # 1. Загружаем конфигурацию
    try:
        config_path = Path(__file__).parent / "data" / "config.json"
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        tg_config = config.get("modules", {}).get("telegram", {})
        api_id = tg_config.get("api_id")
        api_hash = tg_config.get("api_hash")
        if not api_id or not api_hash:
            print("[CRITICAL] 'api_id' и 'api_hash' не найдены в data/config.json")
            return
    except (FileNotFoundError, KeyError):
        print("[CRITICAL] Не удалось загрузить конфигурацию Telegram.")
        return

    # 2. Создаем клиент и проходим авторизацию
    # Telethon автоматически запросит все необходимые данные в консоли
    client = TelegramClient(SESSION_NAME, int(api_id), api_hash)
    
    try:
        await client.start()
        
        me = await client.get_me()
        print(f"\n[SUCCESS] Авторизация прошла успешно.")
        print(f"Вы вошли как: @{me.username} (ID: {me.id})")
        print(f"Файл сессии '{SESSION_NAME}.session' создан/обновлен.")
        print("Теперь вы можете запускать основное приложение.")
        
    except Exception as e:
        print(f"\n[ERROR] Произошла ошибка при авторизации: {e}")
    finally:
        if client.is_connected():
            await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())