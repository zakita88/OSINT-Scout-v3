import aiohttp
import asyncio


async def scan_github(username: str):
    """
    Асинхронный GitHub сканер через официальное REST API.
    """
    url = f"https://api.github.com/users/{username}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 404:
                    return None

                if resp.status != 200:
                    return {"error": f"GitHub HTTP {resp.status}"}

                data = await resp.json()

                return {
                    "id": data.get("id"),
                    "username": data.get("login"),
                    "name": data.get("name"),
                    "bio": data.get("bio"),
                    "avatar_url": data.get("avatar_url"),
                    "url": data.get("html_url"),
                }

    except asyncio.TimeoutError:
        return {"error": "timeout"}

    except Exception as e:
        return {"error": str(e)}
