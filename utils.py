# utils.py
import re


def validate_name(name: str) -> bool:
    """Проверяет, что имя не пустое и содержит хотя бы 2 буквы"""
    return bool(name and len(name.strip()) >= 2)


def validate_phone(phone: str) -> bool:
    """Простая проверка телефона (цифры, +, пробелы, скобки, дефисы)"""
    cleaned = re.sub(r'[\s\(\)\-]', '', phone)
    return bool(re.match(r'^\+?\d{10,15}$', cleaned))


def format_preferences(prefs: list) -> str:
    """Форматирует список предпочтений в строку"""
    if not prefs:
        return "Не указаны"
    return ", ".join(prefs)