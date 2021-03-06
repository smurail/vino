from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.html import escape

from .importable import ImportableMixin
from .models import (Symbol, ViabilityProblem, ParameterSet, Software, Kernel,
                     DataFormat)


admin.site.index_template = 'admin/sharekernel_index.html'


@admin.register(Symbol)
class SymbolAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'vp', 'type', 'longname', 'unit')


class SymbolInline(admin.TabularInline):
    model = Symbol
    extra = 0
    ordering = ('type', 'order')
    readonly_fields = ('type', 'order', 'name', 'longname', 'unit')


class KernelInline(admin.TabularInline):
    model = Kernel
    extra = 0
    show_change_link = True
    can_delete = False
    readonly_fields = (
        'title', 'size', 'format', 'software', 'date_created', 'date_updated')
    fields = ('owner', 'state') + readonly_fields


@admin.register(ParameterSet)
class ParameterSetAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'owner', 'state', 'date_created', 'date_updated')
    inlines = (KernelInline,)


class ParameterSetInline(admin.TabularInline):
    model = ParameterSet
    extra = 0
    show_change_link = True
    can_delete = False


@admin.register(Software)
class SoftwareAdmin(admin.ModelAdmin):
    list_display = ('title', 'version', 'owner', 'state', 'date_created', 'date_updated')


@admin.register(DataFormat)
class DataFormatAdmin(admin.ModelAdmin):
    list_display = ('title', 'parameters', 'owner', 'state', 'date_created', 'date_updated')


@admin.register(ViabilityProblem)
class ViabilityProblemAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'state_dimension', 'control_dimension', 'dynamics_type',
        'owner', 'state', 'date_created', 'date_updated')
    readonly_fields = (
        'date_created', 'date_updated', 'state_dimension', 'control_dimension', 'dynamics_type')
    fields = (
        'owner', 'state', 'title', 'date_created', 'date_updated',
        'description', 'publication', 'author', 'email', 'url', 'image',
        'state_dimension', 'control_dimension', 'dynamics_type',
        'dynamics', 'controls', 'constraints', 'domain', 'target')
    inlines = (ParameterSetInline, SymbolInline)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.with_dimensions()

    def state_dimension(self, obj):
        return obj.state_dimension
    state_dimension.short_description = 'State dimension'  # type: ignore
    state_dimension.admin_order_field = 'state_dimension'  # type: ignore

    def control_dimension(self, obj):
        return obj.control_dimension
    control_dimension.short_description = 'Control dimension'  # type: ignore
    control_dimension.admin_order_field = 'control_dimension'  # type: ignore


@admin.register(Kernel)
class KernelAdmin(ImportableMixin, admin.ModelAdmin):
    list_display = (
        'vp', 'title', 'size', 'format', 'software', 'owner', 'state',
        'date_created', 'date_updated')
    list_display_links = ('title',)
    readonly_fields = ('date_created', 'date_updated', 'vp', 'sourcefiles')
    ordering = ('params__vp__title', 'title')
    fields = (
        'owner', 'state', 'title', 'date_created', 'date_updated',
        'vp', 'params', 'format', 'software', 'datafile', 'sourcefiles',
        'description', 'publication', 'author', 'email', 'url', 'image')

    def vp(self, obj):
        vp = obj.params.vp
        url = reverse("admin:sharekernel_viabilityproblem_change", args=(vp.pk,))
        title = obj.params.vp.title
        return mark_safe(f'<a href="{escape(url)}">{escape(title)}</a>')
    vp.short_description = 'Viability problem'  # type: ignore
    vp.admin_order_field = 'params__vp__title'  # type: ignore
