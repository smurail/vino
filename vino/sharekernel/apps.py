from django.apps import AppConfig


class SharekernelConfig(AppConfig):
    name = 'vino.sharekernel'

    def ready(self):
        # Register custom system checks
        # See https://docs.djangoproject.com/en/2.2/topics/checks/
        # And https://stackoverflow.com/questions/31619635/registering-django-system-checks-in-appconfigs-ready-method/36450374#36450374
        import vino.sharekernel.checks  # noqa: F401

        # Connect field signals with pre_save and post_save models methods
        # See https://github.com/craigds/django-fieldsignals
        from fieldsignals import pre_save_changed, post_save_changed  # type: ignore

        for model in self.models.values():
            if hasattr(model, 'pre_save'):
                pre_save_changed.connect(model.pre_save, sender=model)
            if hasattr(model, 'post_save'):
                post_save_changed.connect(model.post_save, sender=model)
