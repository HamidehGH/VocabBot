from django.urls import path
from . import views

urlpatterns = [
    path('', views.home , name = 'home'),
    path('add/', views.add_vocabulary, name='add_vocabulary'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('link-telegram/', views.link_telegram, name='link_telegram'),
    path('vocab_detail/<int:pk>', views.vocab_detail, name = 'vocab_detail'),
    path('allvocabs/' , views.allvocabs, name = 'allvocabs'),
    path('delete_vocab/<int:pk>', views.delete_vocab, name = 'delete_vocab'),
  
]