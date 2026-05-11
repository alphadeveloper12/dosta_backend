from django import template

register = template.Library()

@register.filter
def divide(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0

@register.filter
def percentage(value, arg):
    try:
        return (float(value) / float(arg)) * 100
    except (ValueError, ZeroDivisionError, TypeError):
        return 0
