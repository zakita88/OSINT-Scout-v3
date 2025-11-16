from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy
from PySide6.QtGui import QPixmap, QImage
import requests
import os


class ResultCard(QWidget):
    def __init__(self, title, subtitle="", avatar_url=None, details=None):
        super().__init__()

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        main = QHBoxLayout()
        self.setLayout(main)

        # avatar
        self.avatar = QLabel()
        self.avatar.setFixedSize(96, 96)
        self.avatar.setStyleSheet("border-radius:6px; background:#2b3340;")
        main.addWidget(self.avatar)

        # text
        block = QVBoxLayout()
        self.title = QLabel(title)
        self.subtitle = QLabel(subtitle)
        block.addWidget(self.title)
        block.addWidget(self.subtitle)

        if details:
            for k, v in details.items():
                block.addWidget(QLabel(f"<b>{k}:</b> {v}"))

        main.addLayout(block)

        if avatar_url:
            self.set_avatar(avatar_url)

    # ------------------ АВАТАР ------------------

    def set_avatar(self, src):
        """Определяет — URL или локальный файл."""
        if isinstance(src, str) and (src.startswith("http://") or src.startswith("https://")):
            self._load_from_url(src)
        else:
            self._load_from_file(src)

    def _load_from_url(self, url):
        try:
            r = requests.get(url, timeout=6)
            r.raise_for_status()
            img = QImage.fromData(r.content)
            if img.isNull():
                return
            self.avatar.setPixmap(QPixmap.fromImage(img).scaled(96, 96))
        except:
            pass

    def _load_from_file(self, path):
        try:
            # корректно ищем абсолютный путь
            if not os.path.isabs(path):
                base = os.path.abspath(os.getcwd())
                path = os.path.join(base, path)

            if not os.path.exists(path):
                print("FILE NOT FOUND:", path)
                return

            with open(path, "rb") as f:
                data = f.read()

            img = QImage.fromData(data)
            if img.isNull():
                print("IMAGE NULL:", path)
                return

            self.avatar.setPixmap(QPixmap.fromImage(img).scaled(96, 96))

        except Exception as e:
            print("LOAD ERROR:", e)
            return
