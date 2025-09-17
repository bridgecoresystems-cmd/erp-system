# employees/templatetags/group_filters.py
from django import template

register = template.Library()

@register.filter
def has_group(user, group_name):
    """Проверяет, принадлежит ли пользователь к определенной группе"""
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name=group_name).exists()