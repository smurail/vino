from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.html import escape

from .importable import ImportableMixin
from .models import Symbol, ViabilityProblem, ParameterSet, Software, Kernel

# Register your models here.

admin.site.register(ParameterSet)
admin.site.register(Software)


@admin.register(Symbol)
class SymbolAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'vp', 'type', 'longname', 'unit')


class SymbolInline(admin.TabularInline):
    model = Symbol
    extra = 0
    ordering = ('type', 'order')


@admin.register(ViabilityProblem)
class ViabilityProblemAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'state', 'date_created', 'date_updated')
    readonly_fields = ('date_created', 'date_updated')
    fields = (
        'owner', 'state', 'title', 'date_created', 'date_updated',
        'description', 'publication', 'author', 'email', 'url', 'image',
        'dynamics', 'controls', 'constraints', 'domain', 'target')
    inlines = (SymbolInline,)


@admin.register(Kernel)
class KernelAdmin(ImportableMixin, admin.ModelAdmin):
    list_display = (
        'vp', 'title', 'format', 'software', 'owner', 'state',
        'date_created', 'date_updated')
    list_display_links = ('title',)
    readonly_fields = ('date_created', 'date_updated', 'vp')
    ordering = ('params__vp__title', 'title')
    fields = (
        'owner', 'state', 'title', 'date_created', 'date_updated',
        'vp', 'params', 'format', 'software', 'datafile',
        'description', 'publication', 'author', 'email', 'url', 'image')

    def vp(self, obj):
        vp = obj.params.vp
        url = reverse("admin:sharekernel_viabilityproblem_change", args=(vp.pk,))
        title = obj.params.vp.title
        return mark_safe(f'<a href="{escape(url)}">{escape(title)}</a>')
    vp.short_description = 'Viability problem'  # type: ignore
    vp.admin_order_field = 'params__vp__title'  # type: ignore
