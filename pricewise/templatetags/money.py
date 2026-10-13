from decimal import Decimal

from django import template

register = template.Library()


@register.filter
def money(value):
    """Format a price the Colombian way: dots for thousands, comma for decimals (10031.5 -> 10.031,50)."""
    if value is None or value == '':
        return ''
    return f"{Decimal(value):,.2f}".translate(str.maketrans(',.', '.,'))
