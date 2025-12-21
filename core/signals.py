import os
from django.db.models.signals import pre_save, post_delete, post_save
from django.dispatch import receiver
from .models import Persona
from django.conf import settings


@receiver(pre_save, sender=Persona)
def eliminar_avatar_anterior(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_avatar = Persona.objects.get(pk=instance.pk).avatar
    except Persona.DoesNotExist:
        return

    if old_avatar and old_avatar != instance.avatar:
        if os.path.isfile(old_avatar.path):
            os.remove(old_avatar.path)



@receiver(post_delete, sender=Persona)
def eliminar_avatar_al_borrar_persona(sender, instance, **kwargs):
    if instance.avatar and instance.avatar.path:
        if os.path.isfile(instance.avatar.path):
            os.remove(instance.avatar.path)



@receiver(pre_save, sender=Persona)
def eliminar_archivo_anterior(sender, instance, **kwargs):
    try:
        persona_antigua = sender.objects.get(pk=instance.pk)

        if persona_antigua.avatar and persona_antigua.avatar != instance.avatar:
            if os.path.isfile(persona_antigua.avatar.path):
                os.remove(persona_antigua.avatar.path)

        if persona_antigua.cvitae and persona_antigua.cvitae != instance.cvitae:
            if os.path.isfile(persona_antigua.cvitae.path):
                os.remove(persona_antigua.cvitae.path)

    except sender.DoesNotExist:
        pass 


@receiver(post_delete, sender=Persona)
def eliminar_archivos_al_borrar(sender, instance, **kwargs):
    if instance.avatar and os.path.isfile(instance.avatar.path):
        os.remove(instance.avatar.path)

    if instance.cvitae and os.path.isfile(instance.cvitae.path):
        os.remove(instance.cvitae.path)