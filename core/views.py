from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import VocabularyForm, CustomRegistrationForm, VocabularyImageFormSet
from .models import Vocabulary, UserProfile , UserVocabularyProgress
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from .forms import CustomLoginForm
from django.contrib.auth.models import User


@login_required
def home(request):
    user = request.user
    chat_id = None
    vocabs = Vocabulary.objects.none()
    if user.is_authenticated:
        try:
            user_profile = user.userprofile
            chat_id = user_profile.chat_id
            # Get the search query from the URL parameter 'q'
            search_query = request.GET.get('q') 
            if search_query:
                search_conditions = (
                    Q(word__icontains=search_query) |
                    Q(meaning__icontains=search_query) |
                    Q(description__icontains=search_query)
                )
                # Combine user filter with search conditions
                vocabs = Vocabulary.objects.filter(
                    Q(user=user_profile) & search_conditions
                ).order_by('-date_added')
            else:
                vocabs = Vocabulary.objects.filter(user=user_profile).order_by('-date_added')[:3]
                
        except UserProfile.DoesNotExist:
            print(f"UserProfile for user {user.username} not found.")   
            pass
    else:
        print("User is not authenticated.")

    context = {
        'chat_id': chat_id,
        'vocabs': vocabs,  
        'search_query': search_query
    }
    return render(request, 'core/home.html', context)



@login_required
def allvocabs(request):
    user = request.user
    user_profile = UserProfile.objects.get(user = user)
    # access the vocabs through the related_name vocabs
    vocabs = user_profile.vocabs.all().order_by('-date_added')
    context = {
        'vocabs': vocabs
    }
    return render(request, 'core/allvocabs.html', context)



@login_required
def vocab_detail(request, pk):
    vocab = get_object_or_404(Vocabulary, pk=pk)
    if request.method == 'POST':
        form = VocabularyForm(request.POST, instance=vocab)
        # formset handles creating, updating, and deleting images
        formset = VocabularyImageFormSet(request.POST, request.FILES, instance=vocab)

        if form.is_valid() and formset.is_valid():
            # Using a transaction to ensure all or nothing is saved
            with transaction.atomic(): 
                form.save()
                formset.save() 
            messages.success(request, 'Vocabulary and images updated successfully!')
            #return redirect('vocab_detail', pk=vocab.pk)
            return redirect('allvocabs')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = VocabularyForm(instance=vocab)
        formset = VocabularyImageFormSet(instance=vocab)

    context = {
        'vocab': vocab,
        'form': form,
        'formset': formset,
    }
    return render(request, 'core/vocab_detail.html', context)



@login_required
def link_telegram(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    token = None
    if request.method == 'POST':
        if 'generate_token' in request.POST:
            token = user_profile.generate_telegram_token()
      
        elif 'clear_link' in request.POST:
            user_profile.clear_telegram_token()
            user_profile.telegram_id = None
            user_profile.chat_id = None
            user_profile.save()
            messages.success(request, 'Your Telegram account has been unlinked.')
        return redirect('link_telegram')
 
    if user_profile.telegram_verification_token and user_profile.telegram_token_expiry > timezone.now():
        token = user_profile.telegram_verification_token
    elif user_profile.telegram_verification_token and user_profile.telegram_token_expiry <= timezone.now():
        user_profile.clear_telegram_token()
        messages.warning(request, 'کد اتصال به تلگرام شما منقضی شد. لطفا یک کد جدید ایجاد کنید')

    context = {
        'user_profile': user_profile,
        'current_token': token
    }
    return render(request, 'core/link_telegram.html', context)



@login_required
def add_vocabulary(request):
    if request.method == 'POST':
        form = VocabularyForm(request.POST, request.FILES)
        # formset handles creating, updating, and deleting images
        formset = VocabularyImageFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            # creates the object but doesn't save it to the database yet:
            vocabulary_item = form.save(commit=False)
            
            try:
                user_profile = request.user.userprofile
                vocabulary_item.user = user_profile 

            except UserProfile.DoesNotExist:
                print("Could not find the associated UserProfile for account. Cannot save word.")
                return render(request, 'core/add_vocabulary.html', {'form': form})
      
            vocabulary_item.save()
            formset.instance = vocabulary_item 
            formset.save()
            messages.success(request, f"Vocabulary word '{vocabulary_item.word}' added successfully!")
            return redirect('allvocabs')
       
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = VocabularyForm()
        formset = VocabularyImageFormSet()

    return render(request, 'core/add_vocabulary.html', {'form': form, 'formset': formset})



@login_required
def delete_vocab(request, pk):
    vocab = Vocabulary.objects.get(pk = pk)
    vocab.delete()
    return redirect('allvocabs')



def login_view(request):
    if request.user.is_authenticated:
        return redirect('')
    if request.method == 'POST':
        form = CustomLoginForm(request=request, data=request.POST)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            # Django's authenticate function
            user = authenticate(request, username=username, password=password)
            print('Authentication result:', user)

            if user is not None:
                # Log the user in to establish a session
                auth_login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Please enter a valid username and password.")
    else:
        form = CustomLoginForm(request=request)

    next_param = request.GET.get('next', '')
    return render(request, 'core/login.html', {'form': form, 'next': next_param})



def logout_view(request):
    auth_logout(request)
    messages.success(request, "You logged out successfully")
    return redirect('login')



def register_view(request):
    if request.method == 'POST':
        form = CustomRegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            try:
                user = User.objects.create_user(username=username, password=password)
                user_profile = user.userprofile 
                user_profile.save()
                # Log the new user in immediately after registration
                auth_login(request, user)
                messages.success(request, "ثبت نام انجام شد")
                return redirect('link_telegram')
               
            except Exception as e:
                messages.error(request, f"خطایی در ثبت نام رخ داده است")
                print(f"An error occurred during registration: {e}")
    else: 
        form = CustomRegistrationForm()
    return render(request, 'core/register.html', {'form': form})




