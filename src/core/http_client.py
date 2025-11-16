# src/core/http_client.py
import asyncio
import aiohttp
import ssl
import certifi

class HttpClient:
    _session: aiohttp.ClientSession | None = None
    # Лимит VK API - 3 запроса в секунду для большинства методов.
    # Семафор ограничивает количество ОДНОВРЕМЕННЫХ запросов к VK.
    _vk_semaphore = asyncio.Semaphore(3)

    @classmethod
    def get_session(cls) -> aiohttp.ClientSession:
        """Возвращает глобальный экземпляр aiohttp.ClientSession."""
        if cls._session is None or cls._session.closed:
            # ИСПРАВЛЕНИЕ: Создаем SSL-контекст, который доверяет сертификатам из пакета certifi.
            # Это решает проблему 'CERTIFICATE_VERIFY_FAILED' в окружениях с антивирусами/прокси.
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            connector = aiohttp.TCPConnector(ssl=ssl_context)

            # Устанавливаем разумный общий таймаут для всех запросов
            timeout = aiohttp.ClientTimeout(total=10)
            cls._session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        return cls._session

    @classmethod
    async def close_session(cls):
        """Закрывает глобальную сессию."""
        if cls._session and not cls._session.closed:
            await cls._session.close()

    @classmethod
    def get_vk_semaphore(cls) -> asyncio.Semaphore:
        """Возвращает семафор для контроля запросов к VK API."""
        return cls._vk_semaphore