from django import template
import pygments
from pygments.formatters.html import HtmlFormatter
from pygments import lexers
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def pygmentize(value):
    return mark_safe(pygments.highlight(value, lexers.get_lexer_by_name('c'),
                                        HtmlFormatter()))
