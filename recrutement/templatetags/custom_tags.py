# recrutement/templatetags/custom_tags.py
from django import template

register = template.Library()

@register.simple_tag
def remove_param(request, param_name):
    """
    Retourne l'URL actuelle sans le paramètre spécifié
    Usage dans le template : {% remove_param request 'param_name' %}
    """
    params = request.GET.copy()
    if param_name in params:
        del params[param_name]
    return params.urlencode() if params else ''

@register.filter
def get_param_value(params, param_name):
    """
    Récupère la valeur d'un paramètre GET
    """
    return params.get(param_name, '')