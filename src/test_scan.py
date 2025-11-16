# src/test_scan.py
import asyncio
import json
import sys
from core.config_loader import load_config
from core.scanner import scan_many

def safe_init(module_name: str, func_name: str, *args):
    """
    Попытка вызвать init-функцию, если она есть в модуле.
    Не будет падать, если функция отсутствует.
    """
    try:
        mod = __import__(f"core.{module_name}", fromlist=[func_name])
        if hasattr(mod, func_name):
            fn = getattr(mod, func_name)
            try:
                # если синхронная функция
                fn(*args)
                print(f"{module_name}.{func_name} called (sync)")
            except TypeError:
                # возможно асинхронная — пропустим, т.к. не хотим await на старте
                print(f"{module_name}.{func_name} exists but failed sync call; skipping")
    except Exception:
        # модуль не найден или другая ошибка — молча игнорируем
        pass

def init_from_config():
    cfg = load_config()
    tg_id = cfg.get("telegram_api_id")
    tg_hash = cfg.get("telegram_api_hash")
    vk_token = cfg.get("vk_token")
    gh_token = cfg.get("github_token")

    # безопасно вызывать init-функции если они есть
    safe_init("telegram_api", "init_telegram", tg_id, tg_hash)
    safe_init("vk_api", "init_vk", vk_token)
    safe_init("github_api", "init_github", gh_token)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python src/test_scan.py <username1> [username2 ...]")
        sys.exit(1)

    init_from_config()
    usernames = sys.argv[1:]
    results = asyncio.run(scan_many(usernames))
    print(json.dumps(results, ensure_ascii=False, indent=2))
