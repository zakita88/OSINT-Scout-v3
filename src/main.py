# src/main.py
import sys
import asyncio
from PySide6.QtWidgets import QApplication
from qasync import QEventLoop
from pathlib import Path

from gui.main_window import MainWindow
from core.http_client import HttpClient
from core.module_loader import load_modules, shutdown_modules

async def startup():
    """Асинхронные задачи перед запуском GUI."""
    await HttpClient.initialize()
    await load_modules()

async def cleanup():
    """Асинхронные задачи для корректного завершения."""
    print("[*] Начало процесса завершения...")
    await shutdown_modules()
    await HttpClient.close()
    print("[*] Все системы выгружены. Выход.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    qss_path = Path(__file__).resolve().parent / "gui" / "theme.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))
    
    main_window = None
    try:
        loop.run_until_complete(startup())
        main_window = MainWindow()
        main_window.show()
        
        with loop:
            loop.run_forever()

    except KeyboardInterrupt:
        print("\n[*] Приложение закрыто пользователем.")
    finally:
        if loop.is_running():
            print("[*] Цикл событий GUI завершен, выполняется очистка...")
            loop.run_until_complete(cleanup())
        loop.close()