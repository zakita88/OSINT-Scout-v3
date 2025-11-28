# src/core/module_loader.py
import importlib
from .config_loader import load_config

_loaded_modules = {}
_config = None

def get_config():
    """Загружает и кэширует конфигурацию."""
    global _config
    if _config is None:
        _config = load_config()
    return _config

async def load_modules():
    """
    Находит, импортирует и инициализирует все включенные в конфиге модули.
    """
    if _loaded_modules:
        return # Предотвращаем повторную загрузку

    config = get_config()
    modules_config = config.get("modules", {})

    for name, module_cfg in modules_config.items():
        if module_cfg.get("enabled", False):
            try:
                module = importlib.import_module(f"modules.{name}")
                if hasattr(module, "initialize"):
                    await module.initialize(module_cfg)
                _loaded_modules[name] = module
                print(f"[*] Модуль '{name}' успешно загружен.")
            except ImportError as e:
                print(f"[!] Ошибка импорта модуля '{name}': {e}")
            except Exception as e:
                print(f"[!] Ошибка инициализации модуля '{name}': {e}")


def get_loaded_modules():
    """Возвращает словарь с загруженными модулями."""
    return _loaded_modules

async def shutdown_modules():
    """Корректно выгружает все модули, вызывая их функции shutdown."""
    for name, module in _loaded_modules.items():
        if hasattr(module, "shutdown"):
            try:
                await module.shutdown()
                print(f"[*] Модуль '{name}' корректно остановлен.")
            except Exception as e:
                print(f"[!] Ошибка при остановке модуля '{name}': {e}")
    _loaded_modules.clear()
    print("[*] Все модули выгружены.")