from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, VocabularyImage

# To create a UserProfile automatically when a new User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        

#To save the UserProfile whenever the User is saved
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.userprofile.save()
    except UserProfile.DoesNotExist:
        pass

# To change the image flag after getting feedback from user
@receiver(post_save, sender=VocabularyImage)
def post_save(sender, instance, **kwargs):
    images_queryset = VocabularyImage.objects.all()
    if not images_queryset.exists():
        return

    if not images_queryset.filter(flag=0).exists():
        print(f"All images have flag=1. Setting all to 0.")
        images_queryset.update(flag=0)
    else:
        print(f"Not all images have flag=1. No change.")
