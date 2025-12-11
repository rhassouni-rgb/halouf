from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Job, Notification

@receiver(post_save, sender=Job)
def create_notification(sender, instance, created, **kwargs):
    # إذا تم إنشاء حجز جديد والمصدر هو الموقع الإلكتروني
    if created and instance.source == 'website':
        Notification.objects.create(
            job=instance,
            message=f"🔔 حجز جديد: {instance.client_name} ({instance.service.name})"
        )