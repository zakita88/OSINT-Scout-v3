# src/core/telegram_client.py
import asyncio
from telethon import TelegramClient

class TelegramClientManager:
    """
    Управляет единственным экземпляром TelegramClient для всего приложения.
    """
    _client: TelegramClient | None = None
    _config: dict = {}
    SESSION_NAME = "tg_session"

    @classmethod
    async def initialize(cls, config: dict):
        """Инициализирует и подключает клиент Telegram, используя существующую сессию."""
        if cls._client and cls._client.is_connected():
            print("[*] Клиент Telegram уже инициализирован.")
            return

        api_id = config.get("api_id")
        api_hash = config.get("api_hash")

        if not api_id or not api_hash:
            print("[!] API ID/Hash для Telegram не найдены в конфигурации. Модуль будет отключен.")
            return

        cls._config = config
        print("[*] Инициализация клиента Telegram...")
        cls._client = TelegramClient(cls.SESSION_NAME, int(api_id), api_hash)
        try:
            await cls._client.connect()
            if not await cls._client.is_user_authorized():
                # Теперь мы не пытаемся авторизоваться здесь
                print("\n" + "="*50)
                print("[CRITICAL] Авторизация в Telegram не пройдена.")
                print(f"[ACTION]    Пожалуйста, запустите скрипт 'python setup_telegram.py' для создания файла сессии.")
                print("="*50 + "\n")
                await cls._client.disconnect()
                cls._client = None
                return

            me = await cls._client.get_me()
            print(f"[*] Клиент Telegram успешно подключен и авторизован как: @{me.username}")

        except Exception as e:
            print(f"[CRITICAL] Не удалось подключить клиент Telegram: {e}")
            cls._client = None


    @classmethod
    def get_client(cls) -> TelegramClient:
        """Возвращает активный экземпляр клиента."""
        if not cls._client or not cls._client.is_connected():
            raise RuntimeError("Клиент Telegram не был инициализирован или отключен.")
        return cls._client

    @classmethod
    async def close(cls):
        """Отключает клиент Telegram."""
        if cls._client and cls._client.is_connected():
            print("[*] Отключение клиента Telegram...")
            await cls._client.disconnect()
            cls._client = None
            print("[*] Клиент Telegram отключен.")