from django.apps import AppConfig


class SharekernelConfig(AppConfig):
    name = 'vino.sharekernel'

    def ready(self):
        from fieldsignals import pre_save_changed, post_save_changed  # type: ignore

        for model in self.models.values():
            if hasattr(model, 'pre_save'):
                pre_save_changed.connect(model.pre_save, sender=model)
            if hasattr(model, 'post_save'):
                post_save_changed.connect(model.post_save, sender=model)
