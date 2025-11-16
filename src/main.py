# src/main.py
import sys
import asyncio
from PySide6.QtWidgets import QApplication
from qasync import QEventLoop
from pathlib import Path
from core.http_client import HttpClient
from core.module_loader import load_modules, shutdown_modules
from gui.main_window import MainWindow

async def startup():
    """Асинхронные задачи, которые нужно выполнить перед запуском GUI."""
    await HttpClient.initialize()
    await load_modules()

async def cleanup():
    """Асинхронные задачи для корректного завершения работы."""
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

    # Применяем стили
    qss_path = Path(__file__).resolve().parent / "gui" / "theme.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))
    
    main_window = None
    try:
        # Выполняем асинхронный старт
        loop.run_until_complete(startup())

        main_window = MainWindow()
        main_window.show()

        # Запускаем основной цикл каноничным для qasync способом
        with loop:
            loop.run_forever()

    except KeyboardInterrupt:
        print("\n[*] Приложение закрыто пользователем.")
    finally:
        if loop.is_running():
            # Если вышли по ошибке, а цикл еще работает
            loop.run_until_complete(cleanup())