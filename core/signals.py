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




# Eliminar archivo anterior al actualizar avatar o cvitae
@receiver(pre_save, sender=Persona)
def eliminar_archivo_anterior(sender, instance, **kwargs):
    try:
        persona_antigua = sender.objects.get(pk=instance.pk)

        # Si cambió el avatar
        if persona_antigua.avatar and persona_antigua.avatar != instance.avatar:
            if os.path.isfile(persona_antigua.avatar.path):
                os.remove(persona_antigua.avatar.path)

        # Si cambió el cvitae
        if persona_antigua.cvitae and persona_antigua.cvitae != instance.cvitae:
            if os.path.isfile(persona_antigua.cvitae.path):
                os.remove(persona_antigua.cvitae.path)

    except sender.DoesNotExist:
        pass  # Es una nueva persona, no hay archivo anterior


# Eliminar archivos al borrar persona
@receiver(post_delete, sender=Persona)
def eliminar_archivos_al_borrar(sender, instance, **kwargs):
    # Eliminar avatar
    if instance.avatar and os.path.isfile(instance.avatar.path):
        os.remove(instance.avatar.path)

    # Eliminar CV
    if instance.cvitae and os.path.isfile(instance.cvitae.path):
        os.remove(instance.cvitae.path)
