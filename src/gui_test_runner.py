# src/gui_test_runner.py
import sys
import asyncio
import logging
from PySide6.QtWidgets import QApplication
from qasync import QEventLoop

# --- НАСТРОЙКА ЛОГИРОВАНИЯ ---
# Включаем отладочный режим для asyncio
logging.basicConfig(level=logging.DEBUG)
# Получаем логгер для qasync, чтобы видеть его внутренние события
qasync_logger = logging.getLogger('qasync')
qasync_logger.setLevel(logging.DEBUG)
# -----------------------------

from pathlib import Path
from gui.main_window import MainWindow
from core.http_client import HttpClient
from core.module_loader import load_modules, shutdown_modules

async def startup():
    logging.debug("--- [DEBUG] НАЧАЛО АСИНХРОННОГО СТАРТА (startup) ---")
    await HttpClient.initialize()
    await load_modules()
    logging.debug("--- [DEBUG] АСИНХРОННЫЙ СТАРТ (startup) ЗАВЕРШЕН ---")

async def cleanup():
    logging.debug("--- [DEBUG] НАЧАЛО АСИНХРОННОЙ ОЧИСТКИ (cleanup) ---")
    await shutdown_modules()
    await HttpClient.close()
    logging.debug("--- [DEBUG] АСИНХРОННАЯ ОЧИСТКА (cleanup) ЗАВЕРШЕНА ---")

if __name__ == "__main__":
    logging.debug("--- [DEBUG] Скрипт запущен ---")
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    app = QApplication(sys.argv)
    logging.debug("--- [DEBUG] QApplication создан ---")
    
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    logging.debug("--- [DEBUG] QEventLoop создан и установлен ---")

    qss_path = Path(__file__).resolve().parent / "gui" / "theme.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))
        logging.debug("--- [DEBUG] Стили QSS применены ---")

    main_window = None
    try:
        logging.debug("--- [DEBUG] Вызов loop.run_until_complete(startup()) ---")
        loop.run_until_complete(startup())
        logging.debug("--- [DEBUG] startup() завершен ---")

        logging.debug("--- [DEBUG] Создание MainWindow ---")
        main_window = MainWindow()
        logging.debug("--- [DEBUG] MainWindow создан ---")
        
        logging.debug("--- [DEBUG] Вызов main_window.show() ---")
        main_window.show()
        logging.debug("--- [DEBUG] main_window.show() завершен ---")

        logging.debug("--- [DEBUG] Вызов app.exec() ---")
        exit_code = app.exec()
        logging.debug(f"--- [DEBUG] app.exec() завершен с кодом {exit_code} ---")
        sys.exit(exit_code)

    except Exception as e:
        logging.error(f"--- [CRITICAL] Неперехваченное исключение в главном потоке: {e}", exc_info=True)
    finally:
        logging.debug("--- [DEBUG] Вход в блок finally ---")
        if not loop.is_closed():
            logging.debug("--- [DEBUG] Вызов loop.run_until_complete(cleanup()) ---")
            loop.run_until_complete(cleanup())
            logging.debug("--- [DEBUG] cleanup() завершен ---")
            loop.close()
            logging.debug("--- [DEBUG] Цикл событий закрыт ---")
        logging.debug("--- [DEBUG] Выход из блока finally ---")