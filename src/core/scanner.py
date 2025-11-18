# src/core/scanner.py
import asyncio
from telethon import TelegramClient
from .module_loader import get_loaded_modules

async def run_scan_session(usernames: list[str], result_callback, progress_callback):
    modules = get_loaded_modules()
    print(f"\n[SCANNER] Начинаем сессию сканирования для {len(usernames)} ников.")
    
    tg_client = None
    telegram_module = modules.get("telegram")
    if telegram_module:
        cfg = telegram_module.get_client_config()
        if cfg:
            tg_client = TelegramClient(telegram_module.SESSION_NAME, cfg['api_id'], cfg['api_hash'])
            print("[SCANNER] Создан новый клиент Telegram для этой сессии.")
            await tg_client.connect()
    
    try:
        tasks = []
        
        # --- ИЗМЕНЕНИЕ: Отделяем VK для пакетной обработки ---
        vk_module = modules.get("vk")
        if vk_module and hasattr(vk_module, 'scan_bulk'):
            print("[SCANNER] Создаю пакетную задачу для VK...")
            # Оборачиваем пакетную задачу, чтобы ее результат был совместим
            task = asyncio.create_task(process_bulk_wrapper("vk", vk_module, usernames))
            tasks.append(task)
        
        # --- Создаем одиночные задачи для ВСЕХ ОСТАЛЬНЫХ модулей ---
        print("[SCANNER] Создаю одиночные задачи для Telegram и GitHub...")
        for username in usernames:
            for name, module in modules.items():
                if name == "vk": # Пропускаем VK, так как он уже в пакетной задаче
                    continue
                
                if name == "telegram" and tg_client:
                    task = asyncio.create_task(scan_one_wrapper(username, name, module, client=tg_client))
                elif name != "telegram": # Для всех остальных (GitHub)
                    task = asyncio.create_task(scan_one_wrapper(username, name, module))
                else:
                    continue
                tasks.append(task)
        
        print(f"[SCANNER] Всего создано задач: {len(tasks)}")
            
        for future in asyncio.as_completed(tasks):
            try:
                results_list = await future
                for result_item in results_list:
                    await result_callback(result_item)
            except Exception as e:
                print(f"[SCANNER CRITICAL] Ошибка при обработке Future: {e}")
            finally:
                progress_callback()
            
    finally:
        if tg_client and tg_client.is_connected():
            print("[SCANNER] Завершаю сессию клиента Telegram...")
            await tg_client.disconnect()

async def process_bulk_wrapper(module_name, module, usernames):
    """Обертка для пакетной задачи, чтобы ее результат был совместим."""
    bulk_result = await module.scan_bulk(usernames)
    results_list = []
    for username, data in bulk_result.items():
        if data and not data.get('error'):
            results_list.append({'username': username, module_name: data})
    return results_list

async def scan_one_wrapper(username: str, module_name: str, module, client=None):
    """Обертка для одиночной задачи, которая может принимать доп. клиент."""
    try:
        if module_name == "telegram" and client:
            data = await asyncio.wait_for(module.scan(username, client=client), timeout=20.0)
        else:
            # Для GitHub и других будущих одиночных модулей
            data = await asyncio.wait_for(module.scan(username), timeout=20.0)

        if data and not data.get('error'):
            return [{'username': username, module_name: data}]
        return []
    except asyncio.TimeoutError:
        print(f"[{module_name.upper()}] Таймаут для '{username}'")
        return []
    except Exception as e:
        print(f"[{module_name.upper()}] Исключение для '{username}': {e}")
        return []