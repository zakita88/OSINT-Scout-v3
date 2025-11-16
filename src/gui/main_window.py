import asyncio
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QListWidget, QListWidgetItem, QProgressBar, QFileDialog
)
from PySide6.QtCore import Slot
from qasync import asyncSlot
from gui.widgets.result_card import ResultCard
from gui.widgets.log_console import LogConsole
from core.scanner import scan_many


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OSINT-Scout")
        self.resize(900, 700)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # верхняя панель
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

        # прогресс
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        layout.addWidget(self.progress)

        # вкладки
        self.tabs = QTabWidget()
        self.tab_list_widgets = {}
        for name in ("Telegram", "VK", "GitHub"):
            listw = QListWidget()
            self.tab_list_widgets[name] = listw
            self.tabs.addTab(listw, name)
        layout.addWidget(self.tabs, stretch=1)

        # лог
        self.log = LogConsole()
        self.log.setFixedHeight(160)
        layout.addWidget(self.log)

        self.latest_results = []

    @Slot()
    def on_export_clicked(self):
        if not self.latest_results:
            self.log.log("Нет результатов для экспорта")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Save results", "results.json", "JSON Files (*.json)")
        if not path:
            return

        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.latest_results, f, ensure_ascii=False, indent=2)

        self.log.log(f"Saved results to {path}")

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

        results = await scan_many(raw)
        self.latest_results = results

        total = len(results)
        done = 0

        for item in results:
            username = item.get("username")
            self.log.log(f"Результат для {username} получен")

            # ---------- TELEGRAM ----------
            tg = item.get("telegram")
            if tg:
                title = f"{username} — Telegram"
                subtitle = " ".join(filter(None, [
                    tg.get("first_name", ""),
                    tg.get("last_name", "")
                ]))
                avatar = tg.get("photo")   # <-- ТУТ ПЕРЕДАЁМ ПУТЬ К КЭШУ !!!

                card = ResultCard(
                    title,
                    subtitle,
                    avatar_url=avatar,
                    details={
                        "id": tg.get("id"),
                        "username": tg.get("username"),
                        "is_bot": tg.get("is_bot")
                    }
                )
                lw = self.tab_list_widgets["Telegram"]
                it = QListWidgetItem()
                it.setSizeHint(card.sizeHint())
                lw.addItem(it)
                lw.setItemWidget(it, card)
            else:
                self.tab_list_widgets["Telegram"].addItem(f"{username} — not found")

            # ---------- VK ----------
            vk = item.get("vk")
            if vk and isinstance(vk, dict) and not vk.get("error"):
                title = f"{username} — VK"
                name = f"{vk.get('first_name','')} {vk.get('last_name','')}"
                avatar = vk.get("photo_max")

                card = ResultCard(
                    title,
                    name,
                    avatar_url=avatar,
                    details={
                        "id": vk.get("id"),
                        "city": (vk.get("city") or {}).get("title", ""),
                        "bdate": vk.get("bdate"),
                        "status": vk.get("status")
                    }
                )
                lw = self.tab_list_widgets["VK"]
                it = QListWidgetItem()
                it.setSizeHint(card.sizeHint())
                lw.addItem(it)
                lw.setItemWidget(it, card)
            else:
                self.tab_list_widgets["VK"].addItem(f"{username} — not found")

            # ---------- GitHub ----------
            gh = item.get("github")
            if gh and isinstance(gh, dict) and not gh.get("error"):
                title = f"{username} — GitHub"
                subtitle = gh.get("name") or ""
                avatar = gh.get("avatar_url")

                card = ResultCard(
                    title,
                    subtitle,
                    avatar_url=avatar,
                    details={
                        "public_repos": gh.get("public_repos"),
                        "followers": gh.get("followers"),
                        "bio": gh.get("bio")
                    }
                )
                lw = self.tab_list_widgets["GitHub"]
                it = QListWidgetItem()
                it.setSizeHint(card.sizeHint())
                lw.addItem(it)
                lw.setItemWidget(it, card)
            else:
                self.tab_list_widgets["GitHub"].addItem(f"{username} — not found")

            done += 1
            self.progress.setValue(int(done / total * 100))

        self.log.log("Скан завершён")
