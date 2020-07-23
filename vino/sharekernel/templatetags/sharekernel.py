import re

from django import template

# For kernel_url tag
from django.urls import reverse
from django.utils.html import conditional_escape

# For pluck filter
from django.template import VariableDoesNotExist, TemplateSyntaxError
from django.template.defaultfilters import _property_resolver


register = template.Library()


@register.inclusion_tag('visualize.html', takes_context=True)
def visualize(context, kernels=None):
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


class KernelURLNode(template.Node):
    VIEW_NAME = 'viabilityproblem'

    def __init__(self, kernel):
        self.arg = kernel

    def render(self, context):
        try:
            current_app = context.request.current_app
        except AttributeError:
            try:
                current_app = context.request.resolver_match.namespace
            except Exception:
                current_app = None

        kernel = self.arg.resolve(context)
        args = [kernel.vp.pk]
        url = reverse(self.VIEW_NAME, args=args, current_app=current_app)
        url += f'#kernel/{kernel.pk}'

        if context.autoescape:
            url = conditional_escape(url)

        return url


@register.tag
def kernel_url(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError("'%s' takes at least one argument, a Kernel instance." % bits[0])

    kernel = parser.compile_filter(bits[1])

    return KernelURLNode(kernel)


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


_mathjax_indice = re.compile("([a-zA-Z_][a-zA-Z0-9_']*)_([a-zA-Z0-9']{2,})")


@register.filter
def mathjax(value):
    value = _mathjax_indice.sub(r'\1_{\2}', value)
    return r'\(' + str(value).replace('\\', '\\\\') + r'\)'


@register.filter
def mathjax_list(value):
    return [mathjax(item) for item in value]
