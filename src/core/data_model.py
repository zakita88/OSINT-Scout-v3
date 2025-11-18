# src/core/data_model.py
from dataclasses import dataclass, field
from transliterate import translit

def normalize_for_search(text: str | None) -> str:
    """Приводит текст к нижнему регистру и транслитерирует для поиска."""
    if not text:
        return ""
    try:
        return translit(str(text).lower(), 'ru', reversed=True)
    except Exception:
        return str(text).lower()

def _normalize_month(month_str: str) -> str:
    """Централизованный нормализатор месяцев."""
    if not month_str: return ""
    month_str = str(month_str).lower()
    if month_str.isdigit(): return month_str
    month_map = {
        'янв': '1', 'jan': '1', 'января': '1', 'фев': '2', 'feb': '2', 'февраля': '2',
        'мар': '3', 'mar': '3', 'марта': '3', 'апр': '4', 'apr': '4', 'апреля': '4',
        'мая': '5', 'may': '5', 'июн': '6', 'jun': '6', 'июня': '6',
        'июл': '7', 'jul': '7', 'июля': '7', 'авг': '8', 'aug': '8', 'августа': '8',
        'сен': '9', 'sep': '9', 'сентября': '9', 'окт': '10', 'oct': '10', 'октября': '10',
        'ноя': '11', 'nov': '11', 'ноября': '11', 'дек': '12', 'dec': '12', 'декабря': '12',
    }
    return month_map.get(month_str, month_str)

@dataclass
class NormalizedData:
    """Единая модель данных для результатов поиска."""
    # Основные идентификаторы
    username: str = ""
    first_name: str = ""
    last_name: str = ""
    middle_name: str = "" # НОВОЕ ПОЛЕ
    email: str = "" # НОВОЕ ПОЛЕ
    
    # Местоположение
    city: str = ""
    country: str = ""
    
    # Дата рождения
    birth_day: str = ""
    birth_month: str = ""
    birth_year: str = ""
    
    # Другое
    company: str = ""
    
    # Служебные поля для поиска
    search_name: str = field(init=False, repr=False)
    search_location: str = field(init=False, repr=False)
    search_email: str = field(init=False, repr=False)

    def __post_init__(self):
        """Вызывается после создания объекта для генерации поисковых полей."""
        self.search_name = normalize_for_search(f"{self.username} {self.first_name} {self.last_name} {self.middle_name}")
        self.search_location = normalize_for_search(f"{self.city} {self.country} {self.company}")
        self.search_email = normalize_for_search(self.email) # Email и так обычно в латинице

    @classmethod
    def from_vk_api(cls, data: dict):
        """Фабричный метод для создания объекта из ответа VK API."""
        bday, bmonth, byear = "", "", ""
        if bdate := data.get("bdate"):
            parts = bdate.replace('.', ' ').split()
            if len(parts) >= 1: bday = parts[0]
            if len(parts) >= 2: bmonth = _normalize_month(parts[1])
            if len(parts) == 3: byear = parts[2]
            
        return cls(
            username=data.get("domain", ""),
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            city=(data.get("city") or {}).get("title", ""),
            country=(data.get("country") or {}).get("title", ""),
            company=(data.get("occupation") or {}).get("name", ""),
            birth_day=bday, birth_month=bmonth, birth_year=byear
        )
        
    @classmethod
    def from_github_api(cls, data: dict):
        """Фабричный метод для создания объекта из ответа GitHub API."""
        name_parts = (data.get("name") or "").split()
        first_name = name_parts[0] if len(name_parts) >= 1 else ""
        last_name = name_parts[1] if len(name_parts) >= 2 else ""
        # GitHub не предоставляет отчество, но мы можем предположить его, если есть 3 слова
        middle_name = " ".join(name_parts[2:]) if len(name_parts) >= 3 else ""

        return cls(
            username=data.get("login", ""),
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            email=data.get("email", ""),
            city=data.get("location", ""),
            company=data.get("company", "")
        )
    
    @classmethod
    def from_telegram_api(cls, data: dict):
        """Фабричный метод для создания объекта из ответа Telegram API."""
        return cls(
            username=data.get("username", ""),
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", "")
        )