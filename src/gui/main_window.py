# src/gui/main_window.py
import asyncio, json, time
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QProgressBar,
    QFileDialog, QCheckBox, QFormLayout, QFrame, QScrollArea,
    QScroller, QCompleter
)
from PySide6.QtCore import Slot, Qt, QTimer, QStringListModel
from qasync import asyncSlot

from .widgets.result_card import ResultCard
from .widgets.log_console import LogConsole
from core.scanner import run_scan_session
from core.module_loader import get_loaded_modules, get_config
from core.username_generator import generate_variations
from core.data_model import normalize_for_search

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OSINT-Scout")
        self.resize(1100, 750)
        self.history_file = Path(__file__).resolve().parent.parent / "data" / "history.txt"
        self.history = self.load_history()
        self.modules_config = get_config().get("modules", {})
        self.loaded_modules = get_loaded_modules()
        
        main_layout = QHBoxLayout(self)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        input_layout = QHBoxLayout()
        self.input = QLineEdit()
        self.completer = QCompleter(self.history, self); self.completer.setCaseSensitivity(Qt.CaseInsensitive); self.input.setCompleter(self.completer)
        self.input.setPlaceholderText("Введите ник(и) или один ник для генерации")
        input_layout.addWidget(self.input)
        left_layout.addLayout(input_layout)

        controls_layout = QHBoxLayout(); self.generator_checkbox = QCheckBox("Генерировать вариации"); controls_layout.addWidget(self.generator_checkbox); controls_layout.addStretch(); self.scan_btn = QPushButton("Scan"); self.scan_btn.clicked.connect(self.on_scan_clicked); controls_layout.addWidget(self.scan_btn); self.save_btn = QPushButton("Export JSON"); self.save_btn.clicked.connect(self.on_export_clicked); controls_layout.addWidget(self.save_btn); self.clear_history_btn = QPushButton("Очистить историю"); self.clear_history_btn.clicked.connect(self.on_clear_history); controls_layout.addWidget(self.clear_history_btn);
        left_layout.addLayout(controls_layout)
        
        progress_layout = QHBoxLayout(); self.progress = QProgressBar(); self.progress.setRange(0, 100); progress_layout.addWidget(self.progress, 1); self.timer_label = QLabel("00:00"); progress_layout.addWidget(self.timer_label); self.scan_timer = QTimer(self); self.scan_timer.timeout.connect(self.update_timer_display); left_layout.addLayout(progress_layout)

        self.tabs = QTabWidget()
        self.tab_layouts = {}
        for name, module_cfg in self.modules_config.items():
            if module_cfg.get("enabled"):
                scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True); scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff); QScroller.grabGesture(scroll_area.viewport(), QScroller.ScrollerGestureType.LeftMouseButtonGesture)
                container = QWidget()
                layout = QVBoxLayout(container)
                layout.setAlignment(Qt.AlignmentFlag.AlignTop)
                self.tab_layouts[name] = layout
                scroll_area.setWidget(container)
                display_name = module_cfg.get("display_name", name)
                self.tabs.addTab(scroll_area, display_name)
        left_layout.addWidget(self.tabs, stretch=1)
        
        self.log = LogConsole(); self.log.setFixedHeight(160); left_layout.addWidget(self.log)
        main_layout.addWidget(left_panel, stretch=1)
        
        right_panel = QWidget(); right_panel.setFixedWidth(280); right_layout = QVBoxLayout(right_panel); filter_title = QLabel("Фильтры"); filter_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 5px;"); right_layout.addWidget(filter_title)
        filter_form = QFormLayout(); self.lastname_filter = QLineEdit(); self.lastname_filter.textChanged.connect(self.on_filter_changed); filter_form.addRow("Фамилия:", self.lastname_filter); self.firstname_filter = QLineEdit(); self.firstname_filter.textChanged.connect(self.on_filter_changed); filter_form.addRow("Имя:", self.firstname_filter); self.middlename_filter = QLineEdit(); self.middlename_filter.textChanged.connect(self.on_filter_changed); filter_form.addRow("Отчество:", self.middlename_filter)
        line1 = QFrame(); line1.setFrameShape(QFrame.Shape.HLine); line1.setFrameShadow(QFrame.Shadow.Sunken); filter_form.addRow(line1)
        self.location_filter = QLineEdit(); self.location_filter.setPlaceholderText("Город, страна..."); self.location_filter.textChanged.connect(self.on_filter_changed); filter_form.addRow("Место:", self.location_filter); self.email_filter = QLineEdit(); self.email_filter.textChanged.connect(self.on_filter_changed); filter_form.addRow("Email:", self.email_filter)
        line2 = QFrame(); line2.setFrameShape(QFrame.Shape.HLine); line2.setFrameShadow(QFrame.Shadow.Sunken); filter_form.addRow(line2)
        bdate_layout = QHBoxLayout(); self.day_filter = QLineEdit(); self.day_filter.setPlaceholderText("ДД"); self.day_filter.textChanged.connect(self.on_filter_changed); bdate_layout.addWidget(self.day_filter); self.month_filter = QLineEdit(); self.month_filter.setPlaceholderText("ММ"); self.month_filter.textChanged.connect(self.on_filter_changed); bdate_layout.addWidget(self.month_filter); self.year_filter = QLineEdit(); self.year_filter.setPlaceholderText("ГГГГ"); self.year_filter.textChanged.connect(self.on_filter_changed); bdate_layout.addWidget(self.year_filter)
        filter_form.addRow("Дата рождения:", bdate_layout)
        right_layout.addLayout(filter_form); right_layout.addStretch(); main_layout.addWidget(right_panel)
        self.latest_results = []; self.scan_start_time = 0
    
    @Slot()
    def on_filter_changed(self):
        lastname=normalize_for_search(self.lastname_filter.text());firstname=normalize_for_search(self.firstname_filter.text());middlename=normalize_for_search(self.middlename_filter.text());location=normalize_for_search(self.location_filter.text());email=normalize_for_search(self.email_filter.text());day=self.day_filter.text().strip();month=self.month_filter.text().strip();year=self.year_filter.text().strip()
        matching_source_usernames=set()
        for layout in self.tab_layouts.values():
            for i in range(layout.count()):
                widget = layout.itemAt(i).widget()
                if isinstance(widget, ResultCard) and widget.normalized_data:
                    norm_data = widget.normalized_data; lastname_match = not lastname or lastname in normalize_for_search(norm_data.last_name);firstname_match = not firstname or firstname in normalize_for_search(norm_data.first_name);middlename_match = not middlename or middlename in normalize_for_search(norm_data.middle_name);location_match = not location or location in norm_data.search_location;email_match = not email or email in norm_data.search_email
                    try: day_match=not day or(norm_data.birth_day and int(norm_data.birth_day)==int(day));month_match=not month or(norm_data.birth_month and int(norm_data.birth_month)==int(month));year_match=not year or(norm_data.birth_year and int(norm_data.birth_year)==int(year))
                    except(ValueError,TypeError):day_match,month_match,year_match=False,False,False
                    if(lastname_match and firstname_match and middlename_match and location_match and email_match and day_match and month_match and year_match): matching_source_usernames.add(widget.source_username)
        for layout in self.tab_layouts.values():
            for i in range(layout.count()):
                widget = layout.itemAt(i).widget()
                if isinstance(widget, ResultCard): widget.setVisible(widget.source_username in matching_source_usernames)
    
    def clear_filters(self): self.lastname_filter.clear();self.firstname_filter.clear();self.middlename_filter.clear();self.location_filter.clear();self.email_filter.clear();self.day_filter.clear();self.month_filter.clear();self.year_filter.clear()
    @Slot()
    def on_export_clicked(self):
        if not self.latest_results:self.log.log("Нет результатов для экспорта");return
        path,_=QFileDialog.getSaveFileName(self,"Сохранить результаты","results.json","JSON Files (*.json)");
        if not path:return
        try:
            with open(path,"w",encoding="utf-8")as f:json.dump(self.latest_results,f,ensure_ascii=False,indent=2)
            self.log.log(f"Результаты сохранены в {path}")
        except Exception as e:self.log.log(f"Ошибка сохранения файла: {e}")
    def load_history(self):
        if self.history_file.exists(): return [line.strip() for line in self.history_file.read_text('utf-8').splitlines() if line.strip()]
        return []
    def save_history(self):
        self.history_file.parent.mkdir(parents=True, exist_ok=True);
        with self.history_file.open('w', encoding='utf-8') as f: f.write('\n'.join(self.history[:50]))
    def add_to_history(self, text: str):
        if text in self.history: self.history.remove(text)
        self.history.insert(0, text); self.completer.setModel(QStringListModel(self.history)); self.save_history()
    @Slot()
    def on_clear_history(self): self.history = []; self.completer.setModel(QStringListModel(self.history)); self.save_history(); self.log.log("История запросов очищена.")
    @Slot()
    def update_timer_display(self): elapsed = time.monotonic() - self.scan_start_time; self.timer_label.setText(f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}")
    async def _result_callback(self, item: dict):
        self.latest_results.append(item); username = item.get("username")
        for name, layout in self.tab_layouts.items():
            if result_data := item.get(name):
                module = self.loaded_modules.get(name)
                if hasattr(module, "format_result_for_gui"):
                    card_data = module.format_result_for_gui(result_data, username); card = ResultCard(**card_data, source_username=username)
                    # Новые результаты всегда появляются сверху
                    layout.insertWidget(0, card)
    @asyncSlot()
    async def on_scan_clicked(self):
        text = self.input.text().strip();
        if not text: self.log.log("Введите хотя бы один никнейм"); return
        self.add_to_history(text); base_usernames=[x.strip()for x in text.replace("\n",",").split(",")if x.strip()]
        if self.generator_checkbox.isChecked():
            self.log.log(f"Генерация вариаций для {len(base_usernames)} никнеймов..."); all_variations=set();
            for name in base_usernames: all_variations.update(generate_variations(name))
            usernames_to_scan=list(all_variations); self.log.log(f"Сгенерировано {len(usernames_to_scan)} уникальных никнеймов для проверки.")
        else: usernames_to_scan = base_usernames
        if not usernames_to_scan: self.log.log("Не удалось определить никнеймы для сканирования."); return
        
        self.log.log(f"Запущен скан для {len(usernames_to_scan)} никнеймов..."); self.progress.setValue(0); self.scan_btn.setEnabled(False); self.latest_results=[]; self.clear_filters()
        
        for layout in self.tab_layouts.values():
            # Удаляем старую распорку, если она была
            if (item := layout.takeAt(layout.count() - 1)) and not item.widget():
                del item

            # Корректно очищаем все виджеты
            while (item := layout.takeAt(0)) is not None:
                if item.widget():
                    item.widget().deleteLater()
            
            # Добавляем новую распорку в пустой layout
            layout.addStretch(1)

        modules = get_loaded_modules(); bulk_module_count = sum(1 for m in modules.values() if hasattr(m, 'scan_bulk')); single_module_count = len(modules) - bulk_module_count; total_tasks = bulk_module_count + (single_module_count * len(usernames_to_scan)); completed_tasks = 0
        def progress_callback():
            nonlocal completed_tasks; completed_tasks += 1
            if total_tasks > 0: self.progress.setValue(int(completed_tasks / total_tasks * 100))
        
        self.scan_start_time = time.monotonic(); self.scan_timer.start(1000)
        try: await run_scan_session(usernames_to_scan, self._result_callback, progress_callback)
        finally:
            self.scan_timer.stop(); self.progress.setValue(100)
            total_found = len(self.latest_results)
            self.log.log(f"Скан завершён. Найдено {total_found} уникальных профилей."); self.scan_btn.setEnabled(True)