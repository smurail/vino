from django.contrib import admin
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
class KernelAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'state', 'date_created', 'date_updated')
    readonly_fields = ('date_created', 'date_updated')
    fields = (
        'owner', 'state', 'params', 'file', 'format', 'software', 'title',
        'date_created', 'date_updated', 'description', 'publication', 'author',
        'email', 'url', 'image')
