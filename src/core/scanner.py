# src/core/scanner.py
import asyncio
from .module_loader import get_loaded_modules

async def scan_one(username: str):
    """
    Сканирует один никнейм по всем загруженным и активным модулям.
    """
    modules = get_loaded_modules()
    tasks = {}

    for name, module in modules.items():
        if hasattr(module, 'scan') and callable(module.scan):
            tasks[name] = asyncio.create_task(module.scan(username))
    
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    
    final_result = {"username": username}
    for name, result in zip(tasks.keys(), results):
        if isinstance(result, Exception):
            final_result[name] = {"error": f"Исключение в модуле: {result}"}
        else:
            final_result[name] = result
            
    return final_result

async def scan_many(usernames: list[str]):
    """
    Асинхронно запускает сканирование для списка никнеймов.
    """
    tasks = [asyncio.create_task(scan_one(name)) for name in usernames]
    return await asyncio.gather(*tasks)