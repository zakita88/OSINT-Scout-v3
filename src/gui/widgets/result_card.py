# src/gui/widgets/result_card.py
import asyncio, os
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
from core.http_client import HttpClient
from core.data_model import NormalizedData

class ResultCard(QWidget):
    def __init__(self, title, subtitle="", avatar_url=None, details=None, 
                 normalized_data: NormalizedData = None, source_username: str = None):
        super().__init__()
        self.setObjectName("card")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self.normalized_data = normalized_data
        # НОВОЕ ПОЛЕ: Храним ник, по которому искали, для связи карточек между собой
        self.source_username = source_username

        # ... (остальной код __init__ без изменений) ...
        main=QHBoxLayout();self.setLayout(main)
        self.avatar=QLabel();self.avatar.setFixedSize(96,96);self.avatar.setStyleSheet("border-radius:6px; background:#2b3340;");main.addWidget(self.avatar)
        block=QVBoxLayout();self.title_label=QLabel(title);self.title_label.setObjectName("cardTitle");self.subtitle_label=QLabel(subtitle);self.subtitle_label.setObjectName("cardSubtitle");block.addWidget(self.title_label);block.addWidget(self.subtitle_label)
        if details:
            for k,v in details.items():
                if v is None or v=="": continue
                detail_text=f"<b>{k}:</b> "
                if isinstance(v,str)and v.startswith(('http://','https://')): detail_text+=f'<a href="{v}">{v}</a>'
                else: detail_text+=str(v)
                detail_label=QLabel(detail_text);detail_label.setTextFormat(Qt.RichText);detail_label.setTextInteractionFlags(Qt.TextBrowserInteraction);detail_label.setOpenExternalLinks(True);detail_label.setObjectName("cardDetails");detail_label.setWordWrap(True);block.addWidget(detail_label)
        block.addStretch();main.addLayout(block)
        if avatar_url: self.set_avatar(avatar_url)

    # ... (методы set_avatar, _load_from_url, _load_from_file без изменений) ...
    def set_avatar(self,src:str):
        if isinstance(src,str)and(src.startswith("http://")or src.startswith("https://")):asyncio.create_task(self._load_from_url(src))
        else:self._load_from_file(src)
    async def _load_from_url(self,url:str):
        session=HttpClient.get_session()
        try:
            async with session.get(url) as resp:
                resp.raise_for_status();content=await resp.read();img=QImage.fromData(content)
                if not img.isNull():self.avatar.setPixmap(QPixmap.fromImage(img).scaled(96,96))
        except Exception as e:print(f"Error loading image from {url}: {e}")
    def _load_from_file(self,path:str):
        try:
            if not os.path.isabs(path):path=os.path.abspath(path)
            if not os.path.exists(path):print(f"FILE NOT FOUND: {path}");return
            with open(path,"rb") as f:content=f.read()
            img=QImage.fromData(content)
            if img.isNull():print(f"IMAGE NULL: {path}");return
            self.avatar.setPixmap(QPixmap.fromImage(img).scaled(96,96))
        except Exception as e:print(f"LOAD ERROR: {path}, {e}")