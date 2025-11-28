# src/core/scanner.py
import asyncio
import random
from typing import List, Coroutine, Callable, Dict, Any

from .module_loader import get_loaded_modules

# Определяем стратегии для модулей
STRATEGY_BULK = "bulk"
STRATEGY_PARALLEL = "parallel"
STRATEGY_SEQUENTIAL = "sequential"

# Карта стратегий для известных модулей
MODULE_STRATEGIES = {
    "vk": STRATEGY_BULK,
    "telegram": STRATEGY_SEQUENTIAL,
    "github": STRATEGY_PARALLEL,
}

# --- Вспомогательные функции для каждой стратегии ---

async def _process_bulk_modules(modules: dict, usernames: list[str], result_callback: Callable, progress_callback: Callable):
    """Обрабатывает модули, поддерживающие пакетные запросы (VK)."""
    tasks = []
    for name, module in modules.items():
        print(f"[*] Создание пакетной задачи для модуля '{name}'...")
        task = asyncio.create_task(module.scan_bulk(usernames))
        tasks.append((name, task))

    for name, task in tasks:
        try:
            bulk_result = await task
            for username, data in bulk_result.items():
                if data and not data.get('error'):
                    await result_callback({'username': username, name: data})
        except Exception as e:
            print(f"[SCANNER CRITICAL] Ошибка в пакетной задаче '{name}': {e}")
        finally:
            progress_callback() # Один вызов на весь модуль


async def _process_parallel_modules(modules: dict, usernames: list[str], result_callback: Callable, progress_callback: Callable):
    """Обрабатывает модули, допускающие параллельные запросы с ограничением (GitHub)."""
    semaphore = asyncio.Semaphore(10) # Ограничение на 10 одновременных запросов
    tasks = []

    async def scan_with_semaphore(username, name, module):
        async with semaphore:
            try:
                data = await asyncio.wait_for(module.scan(username), timeout=20.0)
                if data and not data.get('error'):
                    await result_callback({'username': username, name: data})
            except asyncio.TimeoutError:
                print(f"[{name.upper()}] Таймаут для '{username}'")
            except Exception as e:
                print(f"[{name.upper()}] Исключение для '{username}': {e}")
            finally:
                progress_callback()

    for name, module in modules.items():
        for username in usernames:
            task = asyncio.create_task(scan_with_semaphore(username, name, module))
            tasks.append(task)
    
    if tasks:
        await asyncio.gather(*tasks)


async def _process_sequential_modules(modules: dict, usernames: list[str], result_callback: Callable, progress_callback: Callable):
    """Обрабатывает модули, требующие последовательных запросов с задержкой (Telegram)."""
    queue = asyncio.Queue()
    for name, module in modules.items():
        for username in usernames:
            await queue.put((username, name, module))

    if queue.empty():
        return

    # Запускаем одного медленного исполнителя (worker)
    async def worker():
        while not queue.empty():
            username, name, module = await queue.get()
            try:
                data = await asyncio.wait_for(module.scan(username), timeout=60.0)
                if data and not data.get('error'):
                    await result_callback({'username': username, name: data})
            except asyncio.TimeoutError:
                print(f"[{name.upper()}] Таймаут для '{username}'")
            except Exception as e:
                print(f"[{name.upper()}] Исключение для '{username}': {e}")
            finally:
                progress_callback()
                queue.task_done()
                # ИЗМЕНЕНИЕ: Уменьшена базовая задержка для быстрой работы
                base_delay = 1.0  # Устанавливаем базовую паузу в 1 секунду
                jitter = random.uniform(0.5, 1.2) # Добавляем небольшую случайность
                total_delay = base_delay + jitter
                # Убираем лог паузы, чтобы не засорять вывод
                await asyncio.sleep(total_delay)
    
    worker_task = asyncio.create_task(worker())
    await queue.join()
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass


async def run_scan_session(usernames: List[str], result_callback: Callable[[Dict[str, Any]], Coroutine], progress_callback: Callable[[], None]):
    """
    Основная функция сканирования, управляющая различными стратегиями.
    """
    all_modules = get_loaded_modules()
    if not all_modules:
        print("[SCANNER] Нет загруженных модулей для сканирования.")
        return

    bulk_modules = {}
    parallel_modules = {}
    sequential_modules = {}

    for name, module in all_modules.items():
        strategy = MODULE_STRATEGIES.get(name, STRATEGY_PARALLEL)
        if strategy == STRATEGY_BULK and hasattr(module, 'scan_bulk'):
            bulk_modules[name] = module
        elif strategy == STRATEGY_SEQUENTIAL and hasattr(module, 'scan'):
            sequential_modules[name] = module
        elif hasattr(module, 'scan'):
            parallel_modules[name] = module

    print(f"\n[SCANNER] Начинаем сессию сканирования для {len(usernames)} ников.")
    print(f"[SCANNER] Стратегии: Пакетные({len(bulk_modules)}), Параллельные({len(parallel_modules)}), Последовательные({len(sequential_modules)})")

    main_tasks = []
    if bulk_modules:
        main_tasks.append(_process_bulk_modules(bulk_modules, usernames, result_callback, progress_callback))
    if parallel_modules:
        main_tasks.append(_process_parallel_modules(parallel_modules, usernames, result_callback, progress_callback))
    if sequential_modules:
        main_tasks.append(_process_sequential_modules(sequential_modules, usernames, result_callback, progress_callback))

    if main_tasks:
        await asyncio.gather(*main_tasks)