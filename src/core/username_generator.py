# src/core/username_generator.py
from itertools import product

def generate_variations(base_username: str) -> list[str]:
    """
    Генерирует список вероятных вариаций для заданного никнейма.
    """
    if not base_username:
        return []

    # Используем set для автоматического исключения дубликатов
    variations = {base_username}

    # Популярные числовые суффиксы
    common_suffixes = [
        '123', '321', '111', '777', '007',
        '1', '2', '3', '7',
        '2005', '2006', '2007', '2008',
        '1998', '1999', '2000',
        '88', '99', '83'
    ]
    # Популярные разделители
    separators = ['_', '.']

    # 1. Просто добавляем суффиксы: user -> user123
    for suffix in common_suffixes:
        variations.add(f"{base_username}{suffix}")

    # 2. Добавляем разделители: user -> user_, user.
    for sep in separators:
        variations.add(f"{base_username}{sep}")

    # 3. Комбинируем разделители и суффиксы: user -> user_123, user.2005
    for sep, suffix in product(separators, common_suffixes):
        variations.add(f"{base_username}{sep}{suffix}")
        
    # 4. Вставляем разделители в середину, если ник достаточно длинный
    if len(base_username) > 4:
        # Например, 'username' -> 'user_name'
        mid = len(base_username) // 2
        for sep in separators:
            variations.add(f"{base_username[:mid]}{sep}{base_username[mid:]}")

    # Ограничиваем количество, чтобы не создавать тысячи запросов
    # Сортируем для более предсказуемого порядка
    return sorted(list(variations))[:100]