from django import template


register = template.Library()


@register.inclusion_tag('kernel_visualize.html')
def kernel_visualize(kernels):
    return {
        'kernels': kernels
    }
