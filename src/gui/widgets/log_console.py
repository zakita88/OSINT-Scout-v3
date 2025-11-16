from PySide6.QtWidgets import QTextEdit

class LogConsole(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setObjectName("logConsole")

    def log(self, text: str):
        from datetime import datetime
        t = datetime.now().strftime("%H:%M:%S")
        self.append(f"[{t}] {text}")
        self.ensureCursorVisible()
