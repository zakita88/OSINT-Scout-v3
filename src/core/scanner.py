import asyncio
from core.telegram_api import scan_telegram
from core.vk_api import scan_vk
from core.github_api import scan_github


async def scan_one(username: str):
    """
    Сканирует 1 ник на всех платформах.
    """

    tg_task = asyncio.create_task(scan_telegram(username))
    vk_task = asyncio.create_task(scan_vk(username))
    gh_task = asyncio.create_task(scan_github(username))

    tg = await tg_task
    vk = await vk_task
    gh = await gh_task

    return {
        "username": username,
        "telegram": tg,
        "vk": vk,
        "github": gh
    }


async def scan_many(usernames: list[str]):
    """
    Сканирует сразу много ников.
    """
    tasks = [asyncio.create_task(scan_one(name)) for name in usernames]
    return await asyncio.gather(*tasks)
