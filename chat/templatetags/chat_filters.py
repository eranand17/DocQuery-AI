import markdown
import nh3

from django import template
from django.utils.safestring import mark_safe


register = template.Library()


@register.filter
def render_markdown(value):
    if not value:
        return ""

    html = markdown.markdown(
        str(value),
        extensions=["extra", "sane_lists"],
    )

    clean_html = nh3.clean(
        html,
        tags={
            "p", "br", "strong", "em", "del",
            "ul", "ol", "li", "blockquote",
            "code", "pre", "h1", "h2", "h3",
            "h4", "hr", "a",
        },
        attributes={"a": {"href", "title"}},
        url_schemes={"http", "https", "mailto"},
    )

    return mark_safe(clean_html)
