# src/gui/widgets/result_card.py
import asyncio
import os
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy
from PySide6.QtGui import QPixmap, QImage
from core.http_client import HttpClient

class ResultCard(QWidget):
    def __init__(self, title, subtitle="", avatar_url=None, details=None):
        super().__init__()
        self.setObjectName("card") # Для применения стилей из QSS

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
        self.title.setObjectName("cardTitle")

        self.subtitle = QLabel(subtitle)
        self.subtitle.setObjectName("cardSubtitle")

        block.addWidget(self.title)
        block.addWidget(self.subtitle)

        if details:
            for k, v in details.items():
                detail_label = QLabel(f"<b>{k}:</b> {v}")
                detail_label.setObjectName("cardDetails")
                detail_label.setWordWrap(True)
                block.addWidget(detail_label)
        
        block.addStretch() # Добавляет растягивающееся пространство вниз

        main.addLayout(block)

        if avatar_url:
            self.set_avatar(avatar_url)

    def set_avatar(self, src: str):
        """Определяет, URL это или локальный файл, и запускает загрузку."""
        if isinstance(src, str) and (src.startswith("http://") or src.startswith("https://")):
            # Запускаем асинхронную загрузку в фоне, не блокируя GUI
            asyncio.create_task(self._load_from_url(src))
        else:
            self._load_from_file(src)

    async def _load_from_url(self, url: str):
        """Асинхронно загружает изображение из сети."""
        session = HttpClient.get_session()
        try:
            async with session.get(url) as resp:
                resp.raise_for_status()
                content = await resp.read()
                img = QImage.fromData(content)
                if not img.isNull():
                    pixmap = QPixmap.fromImage(img).scaled(96, 96)
                    self.avatar.setPixmap(pixmap)
        except Exception as e:
            print(f"Error loading image from {url}: {e}")

    def _load_from_file(self, path: str):
        """Загружает изображение из локального файла."""
        try:
            if not os.path.isabs(path):
                # cache/tg_user.jpg -> /path/to/project/cache/tg_user.jpg
                path = os.path.abspath(path)

            if not os.path.exists(path):
                print(f"FILE NOT FOUND: {path}")
                return

            with open(path, "rb") as f:
                content = f.read()
            
            img = QImage.fromData(content)
            if img.isNull():
                print(f"IMAGE NULL: {path}")
                return

            pixmap = QPixmap.fromImage(img).scaled(96, 96)
            self.avatar.setPixmap(pixmap)
        except Exception as e:
            print(f"LOAD ERROR: {path}, {e}")