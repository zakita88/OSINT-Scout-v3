# src/core/http_client.py
import asyncio
import aiohttp
import ssl
import certifi

class HttpClient:
    _session: aiohttp.ClientSession | None = None
    _vk_semaphore = asyncio.Semaphore(3)

    @classmethod
    async def initialize(cls):
        """
        ИНИЦИАЛИЗИРУЕТ глобальную сессию aiohttp.
        Этот метод должен быть вызван один раз после запуска event loop.
        """
        if cls._session is None:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            timeout = aiohttp.ClientTimeout(total=10)
            cls._session = aiohttp.ClientSession(timeout=timeout, connector=connector)
            print("[*] Сетевая сессия HttpClient инициализирована.")

    @classmethod
    async def close(cls):
        """ЗАКРЫВАЕТ глобальную сессию."""
        if cls._session and not cls._session.closed:
            await cls._session.close()
            cls._session = None
            print("[*] Сетевая сессия HttpClient закрыта.")

    @classmethod
    def get_session(cls) -> aiohttp.ClientSession:
        """
        Возвращает уже инициализированный экземпляр сессии.
        Вызовет ошибку, если сессия не была инициализирована.
        """
        if cls._session is None:
            raise RuntimeError("HttpClient сессия не была инициализирована. Вызовите HttpClient.initialize() сначала.")
        return cls._session

    @classmethod
    def get_vk_semaphore(cls) -> asyncio.Semaphore:
        """Возвращает семафор для контроля запросов к VK API."""
        return cls._vk_semaphore