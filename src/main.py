# src/main.py
import sys
import asyncio
from PySide6.QtWidgets import QApplication
from qasync import QEventLoop
from gui.main_window import MainWindow
from pathlib import Path
from core.http_client import HttpClient

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # применяем QSS-стиль
    qss_path = Path(__file__).resolve().parent / "gui" / "theme.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    main = MainWindow()
    main.show()

    try:
        with loop:
            loop.run_forever()
    finally:
        # Корректно закрываем сессию перед выходом
        if loop.is_running():
             loop.run_until_complete(HttpClient.close_session())