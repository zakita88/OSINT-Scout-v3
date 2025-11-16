import sys
from PySide6.QtWidgets import QApplication
from qasync import QEventLoop
from gui.main_window import MainWindow
from pathlib import Path

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # применяем QSS-стиль
    qss_path = Path(__file__).resolve().parent / "gui" / "theme.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    loop = QEventLoop(app)
    import asyncio
    asyncio.set_event_loop(loop)

    main = MainWindow()
    main.show()

    with loop:
        loop.run_forever()
