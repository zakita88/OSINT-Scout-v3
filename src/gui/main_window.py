# src/gui/main_window.py
import asyncio, json
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QPushButton,QTabWidget,QListWidget,QListWidgetItem,QProgressBar,QFileDialog,QCheckBox,QFormLayout,QFrame)
from PySide6.QtCore import Slot, Qt
from qasync import asyncSlot
from gui.widgets.result_card import ResultCard
from gui.widgets.log_console import LogConsole
from core.scanner import scan_one
from core.module_loader import get_loaded_modules,get_config
from core.username_generator import generate_variations
from core.data_model import normalize_for_search

class MainWindow(QWidget):
    # ... (код __init__ без изменений) ...
    def __init__(self):
        super().__init__();self.setWindowTitle("OSINT-Scout");self.resize(1100,750)
        self.modules_config=get_config().get("modules",{});self.loaded_modules=get_loaded_modules()
        main_layout=QHBoxLayout(self);left_panel=QWidget();left_layout=QVBoxLayout(left_panel)
        input_layout=QHBoxLayout();self.input=QLineEdit();self.input.setPlaceholderText("Введите ник(и) или один ник для генерации");input_layout.addWidget(self.input);left_layout.addLayout(input_layout)
        controls_layout=QHBoxLayout();self.generator_checkbox=QCheckBox("Генерировать вариации");controls_layout.addWidget(self.generator_checkbox);controls_layout.addStretch();self.scan_btn=QPushButton("Scan");self.scan_btn.clicked.connect(self.on_scan_clicked);controls_layout.addWidget(self.scan_btn);self.save_btn=QPushButton("Export JSON");self.save_btn.clicked.connect(self.on_export_clicked);controls_layout.addWidget(self.save_btn);left_layout.addLayout(controls_layout)
        self.progress=QProgressBar();self.progress.setRange(0,100);left_layout.addWidget(self.progress)
        self.tabs=QTabWidget();self.tab_list_widgets={};
        for name,module_cfg in self.modules_config.items():
            if module_cfg.get("enabled"):listw=QListWidget();display_name=module_cfg.get("display_name",name);self.tab_list_widgets[name]=listw;self.tabs.addTab(listw,display_name)
        left_layout.addWidget(self.tabs,stretch=1)
        self.log=LogConsole();self.log.setFixedHeight(160);left_layout.addWidget(self.log)
        main_layout.addWidget(left_panel,stretch=1)
        right_panel=QWidget();right_panel.setFixedWidth(280);right_layout=QVBoxLayout(right_panel)
        filter_title=QLabel("Фильтры");filter_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 5px;");right_layout.addWidget(filter_title)
        filter_form=QFormLayout();self.name_filter=QLineEdit();self.name_filter.setPlaceholderText("Имя, фамилия, ник...");self.name_filter.textChanged.connect(self.on_filter_changed);filter_form.addRow("Имя/Ник:",self.name_filter)
        self.location_filter=QLineEdit();self.location_filter.setPlaceholderText("Город, страна, компания...");self.location_filter.textChanged.connect(self.on_filter_changed);filter_form.addRow("Местоположение:",self.location_filter)
        line=QFrame();line.setFrameShape(QFrame.HLine);line.setFrameShadow(QFrame.Sunken);filter_form.addRow(line)
        bdate_layout=QHBoxLayout();self.day_filter=QLineEdit();self.day_filter.setPlaceholderText("ДД");self.day_filter.textChanged.connect(self.on_filter_changed);bdate_layout.addWidget(self.day_filter)
        self.month_filter=QLineEdit();self.month_filter.setPlaceholderText("ММ");self.month_filter.textChanged.connect(self.on_filter_changed);bdate_layout.addWidget(self.month_filter)
        self.year_filter=QLineEdit();self.year_filter.setPlaceholderText("ГГГГ");self.year_filter.textChanged.connect(self.on_filter_changed);bdate_layout.addWidget(self.year_filter)
        filter_form.addRow("Дата рождения:",bdate_layout)
        right_layout.addLayout(filter_form);right_layout.addStretch();main_layout.addWidget(right_panel)
        self.latest_results=[]

    @Slot()
    def on_filter_changed(self):
        name_term = normalize_for_search(self.name_filter.text())
        location_term = normalize_for_search(self.location_filter.text())
        day = self.day_filter.text().strip()
        month = self.month_filter.text().strip()
        year = self.year_filter.text().strip()

        # ШАГ 1: Собираем "факты" - составляем список "успешных" исходных никнеймов
        matching_source_usernames = set()
        
        for list_widget in self.tab_list_widgets.values():
            for i in range(list_widget.count()):
                card = list_widget.itemWidget(list_widget.item(i))
                if not isinstance(card, ResultCard) or not card.normalized_data: continue
                
                norm_data = card.normalized_data
                
                name_match = not name_term or name_term in norm_data.search_name
                location_match = not location_term or location_term in norm_data.search_location
                
                try:
                    day_match = not day or (norm_data.birth_day and int(norm_data.birth_day) == int(day))
                    month_match = not month or (norm_data.birth_month and int(norm_data.birth_month) == int(month))
                    year_match = not year or (norm_data.birth_year and int(norm_data.birth_year) == int(year))
                except (ValueError, TypeError): day_match,month_match,year_match=False,False,False
                
                if name_match and location_match and day_match and month_match and year_match:
                    matching_source_usernames.add(card.source_username)

        # ШАГ 2: Применяем фильтр - показываем карточки только "успешных" никнеймов
        for list_widget in self.tab_list_widgets.values():
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                card = list_widget.itemWidget(item)
                if isinstance(card, ResultCard):
                    is_visible = card.source_username in matching_source_usernames
                    item.setHidden(not is_visible)

    # ... (clear_filters и on_export_clicked без изменений) ...
    def clear_filters(self):
        self.name_filter.clear();self.location_filter.clear();self.day_filter.clear();self.month_filter.clear();self.year_filter.clear()
    @Slot()
    def on_export_clicked(self):
        if not self.latest_results:self.log.log("Нет результатов для экспорта");return
        path,_=QFileDialog.getSaveFileName(self,"Сохранить результаты","results.json","JSON Files (*.json)")
        if not path:return
        try:
            with open(path,"w",encoding="utf-8")as f:json.dump(self.latest_results,f,ensure_ascii=False,indent=2)
            self.log.log(f"Результаты сохранены в {path}")
        except Exception as e:self.log.log(f"Ошибка сохранения файла: {e}")

    @asyncSlot()
    async def on_scan_clicked(self):
        # ... (логика генерации usernames_to_scan без изменений) ...
        text=self.input.text().strip();
        if not text:self.log.log("Введите хотя бы один никнейм");return
        base_usernames=[x.strip()for x in text.replace("\n",",").split(",")if x.strip()]
        if self.generator_checkbox.isChecked():
            self.log.log(f"Генерация вариаций для {len(base_usernames)} никнеймов...")
            all_variations=set()
            for name in base_usernames:
                all_variations.update(generate_variations(name))
            usernames_to_scan=list(all_variations)
            self.log.log(f"Сгенерировано {len(usernames_to_scan)} уникальных никнеймов для проверки.")
        else:
            usernames_to_scan=base_usernames
        if not usernames_to_scan:self.log.log("Не удалось определить никнеймы для сканирования.");return

        self.log.log(f"Запущен скан для {len(usernames_to_scan)} никнеймов...")
        self.progress.setValue(0);self.scan_btn.setEnabled(False);self.latest_results=[];self.clear_filters()
        for w in self.tab_list_widgets.values():w.clear()
        tasks=[asyncio.create_task(scan_one(name))for name in usernames_to_scan]
        total_tasks,completed_tasks,total_found=len(tasks),0,0

        for future in asyncio.as_completed(tasks):
            try:
                item = await future
                self.latest_results.append(item)
                has_any_result=any(val for name,val in item.items()if name!='username'and val and not val.get('error'))
                if has_any_result:
                    # ИЗМЕНЕНИЕ: `username` здесь - это вариация, а не базовый ник
                    username = item.get("username")
                    self.log.log(f"Найдены данные для {username}")
                    
                    for name,list_widget in self.tab_list_widgets.items():
                        result_data=item.get(name)
                        module=self.loaded_modules.get(name)
                        if result_data and not result_data.get("error")and hasattr(module,"format_result_for_gui"):
                            card_data=module.format_result_for_gui(result_data,username)
                            
                            # Передаем исходный никнейм (username) в карточку
                            card = ResultCard(**card_data, source_username=username)
                            
                            list_item=QListWidgetItem();list_item.setSizeHint(card.sizeHint());list_widget.addItem(list_item);list_widget.setItemWidget(list_item,card);total_found+=1
            except Exception as e:
                self.log.log(f"Ошибка при обработке результата: {e}")
            finally:
                completed_tasks+=1
                self.progress.setValue(int(completed_tasks/total_tasks*100))
        self.log.log(f"Скан завершён. Найдено {total_found} аккаунтов.");self.scan_btn.setEnabled(True)