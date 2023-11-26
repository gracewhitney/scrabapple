from django.template import Library

register = Library()


@register.filter(name="getitem")
def template_getitem(obj, item_name):
    return obj[item_name]

