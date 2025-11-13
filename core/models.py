from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
import requests
from datetime import timedelta
import uuid


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    chat_id = models.BigIntegerField(null = True)
    telegram_verification_token = models.CharField(max_length=64, unique = True, null = True)
    telegram_token_expiry = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}"

    def generate_telegram_token(self):
        # A short, unique token
        self.telegram_verification_token = uuid.uuid4().hex[:12].upper() 
        self.telegram_token_expiry = timezone.now() + timedelta(minutes=15) 
        self.save()
        return self.telegram_verification_token

    def clear_telegram_token(self):
        self.telegram_verification_token = None
        self.telegram_token_expiry = None
        self.save()

    

class Vocabulary(models.Model):
    user = models.ForeignKey(UserProfile, related_name = 'vocabs', on_delete=models.CASCADE)
    word = models.CharField(max_length = 250)
    meaning = models.CharField(max_length = 250)
    description = models.TextField(blank = True)
    date_added = models.DateTimeField(auto_now_add = True)
    
    def __str__(self):
        return f"{self.word}"



class VocabularyImage(models.Model):
    vocabulary = models.ForeignKey(Vocabulary, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to = 'img/')
    caption = models.CharField(max_length=255, blank=True)
    flag = models.BooleanField(default = 0)

    def __str__(self):
        return f"Image for {self.vocabulary.word} ({self.id})"

  
# This model tracks the user's journey with a specific word
class UserVocabularyProgress(models.Model):
    user = models.ForeignKey(UserProfile, related_name='vocab_progress', on_delete=models.CASCADE)
    vocabulary = models.ForeignKey(Vocabulary, related_name='user_progress', on_delete=models.CASCADE)
    appeared_count = models.IntegerField(default=0)
    knew_count = models.IntegerField(default=0)
    didnt_know_count = models.IntegerField(default=0)
    last_appeared = models.DateTimeField(null=True, blank=True)
    next_review = models.DateTimeField(default=timezone.now)
    # Review interval in days (starts at 0 for new cards)
    interval = models.IntegerField(default=0) 
    # SM2 ease factor (starts at 2.5)
    ease_factor = models.FloatField(default=2.5) 

    class Meta:
        unique_together = ('user', 'vocabulary')

    def __str__(self):
        return f"Progress for '{self.vocabulary.word}' by {self.user}"






