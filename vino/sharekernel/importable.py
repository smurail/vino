from django import forms
from django.contrib import admin
from django.urls import path
from django.utils.translation import gettext_lazy as _


class ImportForm(forms.Form):
    files = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'multiple': True}),
        label=_('Files'),
        help_text=_('After clicking above button, you can then select several '
                    'files by holding Ctrl key (or Command on macOS)'),
    )

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)


class ImportAdmin(admin.ModelAdmin):
    form = ImportForm

    import_view = admin.ModelAdmin.add_view

    def get_form(self, request, obj=None, change=False, **kwargs):
        return self.form

    def get_changeform_initial_data(self, request):
        return dict((
            (k, v) for (k, v) in request.GET.items()
            if k in self.form.base_fields
        ))

    def render_change_form(self, request, context, *args, **kwargs):
        opts = self.model._meta
        context.update(**{
            'title': _('Import %s') % opts.verbose_name,
            'import': True,
        })
        return super().render_change_form(request, context, *args, **kwargs)

    def save_form(self, request, form, change):
        files = request.FILES.getlist('files')
        return self.model.from_files(*files)

    def save_related(self, request, form, formsets, change):
        # Override this method to avoid errors
        pass

    def save_model(self, request, obj, form, change):
        # Imported model is already saved at this point, don't do anything
        pass


class ImportableMixin(object):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.import_admin = ImportAdmin(self.model, self.admin_site)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['is_importable'] = True
        return super().changelist_view(request, extra_context)

    def get_urls(self):
        urls = super().get_urls()
        model_info = self.model._meta.app_label, self.model._meta.model_name
        importable_urls = [
            path(
                'import/',
                self.admin_site.admin_view(self.import_admin.import_view),
                name='%s_%s_import' % model_info
            ),
        ]
        return importable_urls + urls

    def get_model_perms(self, request):
        perms = super().get_model_perms(request)
        perms['import'] = True
        return perms
