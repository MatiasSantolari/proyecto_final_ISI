import os
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from .models import Persona

@receiver(pre_save, sender=Persona)
def eliminar_avatar_anterior(sender, instance, **kwargs):
    if not instance.pk:
        return  # Si es un nuevo usuario, no hay nada que borrar

    try:
        old_avatar = Persona.objects.get(pk=instance.pk).avatar
    except Persona.DoesNotExist:
        return

    # Si el avatar cambió, borramos el anterior del disco
    if old_avatar and old_avatar != instance.avatar:
        if os.path.isfile(old_avatar.path):
            os.remove(old_avatar.path)



@receiver(post_delete, sender=Persona)
def eliminar_avatar_al_borrar_persona(sender, instance, **kwargs):
    if instance.avatar and instance.avatar.path:
        if os.path.isfile(instance.avatar.path):
            os.remove(instance.avatar.path)