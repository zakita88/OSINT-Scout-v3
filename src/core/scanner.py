# src/core/scanner.py
import asyncio
from .module_loader import get_loaded_modules

async def scan_one(username: str):
    """
    Сканирует один никнейм по всем загруженным модулям с индивидуальными тайм-аутами.
    """
    modules = get_loaded_modules()
    tasks = {}

    # ИЗМЕНЕНИЕ: Оборачиваем каждый вызов модуля в asyncio.wait_for
    # Это гарантирует, что зависание одного модуля не остановит весь процесс.
    async def scan_module_with_timeout(module):
        try:
            return await asyncio.wait_for(module.scan(username), timeout=15.0)
        except asyncio.TimeoutError:
            return {"error": "Модуль превысил время ожидания (15с)"}
        except Exception as e:
            # Ловим другие возможные ошибки внутри модуля, чтобы не "уронить" gather
            return {"error": f"Исключение в модуле: {str(e)}"}

    for name, module in modules.items():
        if hasattr(module, 'scan') and callable(module.scan):
            tasks[name] = asyncio.create_task(scan_module_with_timeout(module))
    
    # Ждем результатов от всех обернутых задач
    await asyncio.gather(*tasks.values())
    
    final_result = {"username": username}
    for name, task in tasks.items():
        final_result[name] = task.result()
            
    return final_result

# Эта функция больше не используется GUI, но полезна для test_scan.py
async def scan_many(usernames: list[str]):
    """
    Асинхронно запускает сканирование для списка никнеймов.
    """
    tasks = [asyncio.create_task(scan_one(name)) for name in usernames]
    return await asyncio.gather(*tasks)