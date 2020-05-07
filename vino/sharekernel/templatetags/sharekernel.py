from django import template


register = template.Library()


@register.inclusion_tag('visualize.html')
def visualize(kernels):
    return {
        'kernels': kernels
    }
