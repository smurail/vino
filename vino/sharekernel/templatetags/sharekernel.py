from django import template
from django.template import VariableDoesNotExist
from django.template.defaultfilters import _property_resolver


register = template.Library()


@register.inclusion_tag('visualize.html', takes_context=True)
def visualize(context, kernels):
    if 'visualize' not in context:
        context['visualize'] = {
            'id': 0,
        }

    state = context.get('visualize')
    state['id'] += 1

    return {
        'id': state['id'],
        'kernels': kernels,
    }


@register.filter
def lowfirst(x):
    return x and str(x)[0].lower() + str(x)[1:]


@register.filter
def pluck(value, arg):
    try:
        getter = _property_resolver(arg)
        for item in value:
            yield getter(item)
    except (TypeError, VariableDoesNotExist):
        pass
