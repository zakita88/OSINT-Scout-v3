# src/gui/main_window.py
import asyncio
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QListWidget, QListWidgetItem, QProgressBar,
    QFileDialog
)
from PySide6.QtCore import Slot
from qasync import asyncSlot
from gui.widgets.result_card import ResultCard
from gui.widgets.log_console import LogConsole
from core.scanner import scan_many
from core.module_loader import get_loaded_modules, get_config

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OSINT-Scout")
        self.resize(900, 700)

        # Загружаем конфигурацию модулей один раз
        self.modules_config = get_config().get("modules", {})
        self.loaded_modules = get_loaded_modules()

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Верхняя панель
        bar = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Введите ник(и) через запятую или новую строку")
        bar.addWidget(self.input)

        self.scan_btn = QPushButton("Scan")
        self.scan_btn.clicked.connect(self.on_scan_clicked)
        bar.addWidget(self.scan_btn)

        self.save_btn = QPushButton("Export JSON")
        self.save_btn.clicked.connect(self.on_export_clicked)
        bar.addWidget(self.save_btn)
        layout.addLayout(bar)

        # Прогресс
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        layout.addWidget(self.progress)

        # Вкладки (создаются динамически)
        self.tabs = QTabWidget()
        self.tab_list_widgets = {}
        for name, module_cfg in self.modules_config.items():
            if module_cfg.get("enabled"):
                listw = QListWidget()
                display_name = module_cfg.get("display_name", name)
                self.tab_list_widgets[name] = listw
                self.tabs.addTab(listw, display_name)

        layout.addWidget(self.tabs, stretch=1)

        # Лог
        self.log = LogConsole()
        self.log.setFixedHeight(160)
        layout.addWidget(self.log)

        self.latest_results = []

    @Slot()
    def on_export_clicked(self):
        if not self.latest_results:
            self.log.log("Нет результатов для экспорта")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Сохранить результаты", "results.json", "JSON Files (*.json)")
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.latest_results, f, ensure_ascii=False, indent=2)
            self.log.log(f"Результаты сохранены в {path}")
        except Exception as e:
            self.log.log(f"Ошибка сохранения файла: {e}")

    @asyncSlot()
    async def on_scan_clicked(self):
        text = self.input.text().strip()
        if not text:
            self.log.log("Введите хотя бы один никнейм")
            return

        raw = [x.strip() for x in text.replace("\n", ",").split(",") if x.strip()]
        self.log.log(f"Запущен скан для: {', '.join(raw)}")
        self.progress.setValue(0)

        for w in self.tab_list_widgets.values():
            w.clear()

        self.latest_results = await scan_many(raw)
        
        total = len(self.latest_results)
        done = 0

        for item in self.latest_results:
            username = item.get("username")
            self.log.log(f"Обработка результата для {username}")

            # Динамическая обработка результатов по модулям
            for name, list_widget in self.tab_list_widgets.items():
                result_data = item.get(name)
                module = self.loaded_modules.get(name)

                if result_data and not result_data.get("error") and hasattr(module, "format_result_for_gui"):
                    
                    card_data = module.format_result_for_gui(result_data, username)
                    card = ResultCard(
                        title=card_data.get("title"),
                        subtitle=card_data.get("subtitle"),
                        avatar_url=card_data.get("avatar_url"),
                        details=card_data.get("details")
                    )
                    
                    list_item = QListWidgetItem()
                    list_item.setSizeHint(card.sizeHint())
                    list_widget.addItem(list_item)
                    list_widget.setItemWidget(list_item, card)
                else:
                    error_msg = result_data.get('error') if isinstance(result_data, dict) else "не найден"
                    list_widget.addItem(f"{username} - {error_msg}")

            done += 1
            self.progress.setValue(int(done / total * 100))

        self.log.log("Скан завершён")