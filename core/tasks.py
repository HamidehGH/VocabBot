import json
import html
import requests
from .models import Vocabulary, UserVocabularyProgress, UserProfile, VocabularyImage
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from decouple import config
import random
import os
import re


API_KEY = config('API_KEY')
api_url = 'https://api.telegram.org'
#api_url ='https://myworker.hgh5310.workers.dev'

# Function to fetche updates from Telegram
def get_updates(offset=None):
    payload = {"offset": offset} if offset else {}    
    result = send_telegram_request("getUpdates", payload)
    if result is None:
        return []
    elif isinstance(result, list):
        return result
    else:
        print(f"getUpdates returned unexpected type: {type(result)}. Content: {result}")
        return []


# Function to handle bot's incoming text messages
def handle_message(update):
    message = update.get('message')
    if not message:
        print("Update does not contain a message. Skipping.")
        return

    chat_id = message['chat']['id']
    from_user_id = message['from']['id']
    text = message.get('text', '').strip()
    username = message['from'].get('username', f"ID:{from_user_id}")

    print(f"\n--- MESSAGE RECEIVED ---")
    print(f"FROM: @{username} (Telegram ID: {from_user_id})")
    print(f"CHAT ID: {chat_id}")
    print(f"TEXT: '{text}'")

    # If the message is a /start command
    if text == '/start':
        print(f"Detected /start command from {username}.")
        welcome_message = (
            "<b>Hello! Welcome to the Vocabulary Bot!</b>\n\n"
            "To get started and receive flashcards, please link your account "
            "from our website. Go to your profile page and generate a linking token.\n\n"
            "Then, send that token to me here."
        )
        send_text_message(chat_id, welcome_message)
        print(f"Sent welcome message to chat {chat_id}.")
        return

    # To link account using a token, if the message is a valid token
    if re.match(r'^[A-Z0-9]{12}$', text):
        print(f"Detected potential linking token: '{text}'")
        try:
            user_profile = UserProfile.objects.get(
                telegram_verification_token=text,
                telegram_token_expiry__gt=timezone.now()
            )
            print(f"Token '{text}' matched user {user_profile.user.username}.")
            user_profile.chat_id = chat_id
            user_profile.clear_telegram_token()
            user_profile.save()

            success_message = (
                f"<b>Account successfully linked!</b> 🎉\n\n"
                f"Dear {user_profile.user.username}!\n"
                "You will start receiving your vocabulary flashcards through this bot soon!"
            )
            send_text_message(chat_id, success_message)
            print(f"Successfully linked Telegram user {from_user_id} to Django user {user_profile.user.username}.")
        except UserProfile.DoesNotExist:
            send_text_message(chat_id, "That linking token is invalid or expired. Please generate a new one from the website.")
            print(f"Failed linking attempt: Token '{text}' not found or expired.")
        except Exception as e:
            send_text_message(chat_id, f"An error occurred while linking your account. Please try again later.")
            print(f"ERROR: Error linking account for token '{text}': {e}")
        return
    # Default message for unlinked users or unknown commands from linked users
    try:
        user_profile = UserProfile.objects.get(chat_id=chat_id)
        send_text_message(chat_id,
            f"Hello @{user_profile.user.username}! I'm a vocabulary bot. "
            "I'll send you flashcards automatically. I don't currently support other commands."
        )
        print(f"User {user_profile.user.username} is linked, sent unrecognized message.")
    except UserProfile.DoesNotExist:
        send_text_message(chat_id,
            "I don't recognize this message. To link your account and receive flashcards, "
            "please visit our website and generate a linking token. Then send it here.\n"
            "You can also type /start for instructions."
        )
        print(f"Unlinked user {from_user_id} sent unrecognized message.")
    except Exception as e:
        send_text_message(chat_id, f"An internal error occurred. Please try again later")
        print(f"ERROR: Error processing message from {from_user_id}: {e}")



# Function to send a request to the Telegram Bot API
def send_telegram_request(method, payload, files_payload = None):
    url = f"{api_url}/bot{API_KEY}/{method}"
    try:
        print(f"send_telegram_request called for method '{method}'")
        if method == 'sendPhoto':
            response = requests.post(url, data=payload, files=files_payload)
        else:
            response = requests.post(url, data=payload)

        response.raise_for_status()
        response_data = response.json()
        if response_data.get('ok'):
            print(f"Telegram request '{method}' successful! Description: {response_data.get('description', 'OK')}")
            return response_data.get('result')
        else:
            error_code = response_data.get('error_code')
            error_description = response_data.get('description', 'Unknown error')
            print(f"ERROR: Telegram request '{method}' FAILED: Code {error_code} - {error_description}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Network request '{method}' failed: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to decode JSON response for '{method}': {e}")
        return None



# This function implements the SM2 algorithm to update review intervals and ease factors
def sm2(progress, quality):
    ease_factor = progress.ease_factor
    interval = progress.interval
    if quality >= 3:
        # First review
        if interval == 0:  
            interval = 1
        # Second review
        elif interval == 1:  
            interval = 6
        else:
            interval = round(interval * ease_factor)
        ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    else:
        interval = 1
        ease_factor = ease_factor - 0.8
    if ease_factor < 1.3:
        ease_factor = 1.3

    progress.interval = interval
    progress.ease_factor = ease_factor
    progress.last_appeared = timezone.now()
    progress.next_review = timezone.now() + timedelta(days=interval)
    progress.appeared_count += 1
    return progress



def handle_callback_query(update):
    query = update['callback_query']
    message_id = query['message']['message_id']
    chat_id = query['message']['chat']['id']
    callback_data = query['data']

    print(f"Received callback: {callback_data} from Chat ID: {chat_id}")
    try:
        parts = callback_data.split(':')
        action = parts[0]
        vocab_id = int(parts[1])
        # image_id could be 'None' if no image was sent.
        image_id = None
        if len(parts) > 2 and parts[2].isdigit():
            image_id = int(parts[2])

        user = UserProfile.objects.get(chat_id = chat_id)
        vocab = Vocabulary.objects.get(id = vocab_id)
        # transaction for atomic updates
        with transaction.atomic():
            # First, handles UserVocabularyProgress logic
            try:
                progress = UserVocabularyProgress.objects.get(user = user, vocabulary = vocab)
            except UserVocabularyProgress.DoesNotExist:
                progress = UserVocabularyProgress.objects.create(user = user, vocabulary = vocab)

            if action == 'knew':
                # quality number of SM2 algorithm (4: correct response after a hesitation) 
                progress = sm2(progress, 4)
                progress.knew_count += 1
                feedback_text = "Good job!"
            elif action == 'didnt_know':
                # quality number of SM2 algorithm (1: incorrect response; the correct one remembered)
                progress = sm2(progress, 1)
                progress.didnt_know_count += 1
                feedback_text = "It's ok, we'll review it later."
            else:
                feedback_text = "Unknown"
            progress.save()

            # Second, updates the image flag
            if image_id: 
                try:
                    vocab_image = VocabularyImage.objects.get(id=image_id, vocabulary=vocab)
                    if action == 'knew':
                        vocab_image.flag = 1
                        vocab_image.save()
                        print(f"Image {vocab_image.id} flag for Vocab '{vocab.word}' set to 1 (Knew It).")
                    elif action == 'didnt_know':
                        vocab_image.flag = 0 
                        vocab_image.save()
                        print(f"Image {vocab_image.id} flag for Vocab '{vocab.word}' reset to 0 (Didn't Know).")
               
                except VocabularyImage.DoesNotExist:
                    print(f"VocabularyImage with ID {image_id} not found for Vocab {vocab.id}. Cannot update flag.")
                except Exception as e:
                    print(f"Error updating image flag for vocab {vocab.id}, image {image_id}: {e}")
            else:
                print(f"No specific image ID provided for Vocab '{vocab.word}'. Skipping image flag update.")

            # Acknowledge the callback query
            ack_payload = {'callback_query_id': query['id'], 'text': feedback_text, 'show_alert': True}
            send_telegram_request('answerCallbackQuery', ack_payload)
            # Edit the original message (remove buttons)
            edit_payload = {
                'chat_id': chat_id,
                'message_id': message_id,
                'reply_markup': json.dumps({}) # Remove buttons
            }
            send_telegram_request('editMessageReplyMarkup', edit_payload)

    except UserProfile.DoesNotExist:
        print(f"User with chat_id {chat_id} not found.")
        
    except Vocabulary.DoesNotExist:
        print(f"Vocabulary with ID {vocab_id} not found.")

    except (ValueError, IndexError) as e:
        print(f"Error parsing callback_data '{callback_data}': {e}")
        
    except Exception as e:
        print(f"Unexpected error in handle_callback_query: {type(e).__name__} - {e}")
        ack_payload = {'callback_query_id': query['id'], 'text': 'An error occurred', 'show_alert': True}
        send_telegram_request('answerCallbackQuery', ack_payload)



# Sends a photo with a caption, HTML parse mode, and inline buttons
def send_photo_with_spoiler(chat_id, vocab_image_path, caption, vocab_id, callback_knew, callback_did_not_know):
    if not vocab_image_path or not os.path.exists(vocab_image_path):
        print(f"Error: Image file not found at path: {vocab_image_path}")
        return None

    keyboard = {
        "inline_keyboard": [
            [
                {"text": "یادم بود", "callback_data": callback_knew},
                {"text": "یادم نبود", "callback_data": callback_did_not_know}
            ]
        ]
    }
    data_payload = {
        "chat_id": chat_id,
        "caption": caption,
        "parse_mode": "HTML",
        "reply_markup": json.dumps(keyboard) 
    }
    try:
        with open(vocab_image_path, 'rb') as image_file:
            files_payload = {
                'photo': (os.path.basename(vocab_image_path), image_file)
            }
            response = send_telegram_request("sendPhoto", data_payload, files_payload)
            return response

    except FileNotFoundError:
        print(f"Error: Image file not found when trying to open: {vocab_image_path}")
        return None
    except Exception as e:
        print(f"Error in send_photo_with_spoiler (file handling or request): {e}")
        return None



def send_text_message(chat_id, text):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    send_telegram_request("sendMessage", payload)



# Gets a list of vocabulary words scheduled for review for a given user, 
# prioritizing those due soonest and including some new words. Uses SM2 algorithm.
def get_scheduled_words(user, num_words):
    now = timezone.now()
    # Get overdue words (highest priority)
    overdue_progress = UserVocabularyProgress.objects.filter(
        user=user, next_review__lte=now
    ).order_by('next_review')[:num_words // 2]
    overdue_words = [p.vocabulary for p in overdue_progress]
  
    remaining_slots = num_words - len(overdue_words)
    # Fill remaining slots with new or soon-to-be-due words
    soon_due_progress = UserVocabularyProgress.objects.filter(
        user=user, next_review__gt=now
    ).order_by('next_review')[:remaining_slots // 2]
    soon_due_words = [p.vocabulary for p in soon_due_progress]
  
    new_words = remaining_slots - len(soon_due_words)
    # Get new words (not in UserVocabularyProgress for this user yet)
    # This query needs to find Vocabulary objects that DON'T have a corresponding UserVocabularyProgress entry yet
    existing_progress_vocab_ids = UserVocabularyProgress.objects.filter(user=user).values_list('vocabulary_id', flat=True)

    new_words = Vocabulary.objects.filter(user=user).exclude(
        id__in=existing_progress_vocab_ids
    ).order_by('date_added')[:new_words]
    
    # Combine the words
    words = list(overdue_words) + list(soon_due_words) + list(new_words)

    if not words:
         print(f"No scheduled or new words found for user {user}.")

    random.shuffle(words)
    return words



def send_vocabulary_batch():
    print("Preparing a vocabulary batch...")
    users = UserProfile.objects.all()
    NUM_WORDS_TO_SEND = 5

    if not users.exists():
        print("No users found in UserProfile model")
        return

    for user in users:
        print(f"Processing user: {user} (Chat ID: {user.chat_id})")
        chat_id = user.chat_id
        if not chat_id or chat_id == None:
            print(f"{user} is not connected to the telegram bot. There is no chat_id")
            continue
        words = get_scheduled_words(user, NUM_WORDS_TO_SEND)
        if not words:
            print(f"No words scheduled for review or new words available for user {user}.")
            continue
        for vocab in words:
            image_to_send_obj = None
            # Try to get the first image that has flag=0
            first_flag_zero_image = vocab.images.filter(flag=0, image__isnull=False).first()
            if first_flag_zero_image:
                image_to_send_obj = first_flag_zero_image
                print(f"Found image with flag=0 for '{vocab.word}'.")
            else:
                # If no image with flag=0, try to get any image that has a file
                any_available_image = vocab.images.filter(image__isnull=False).first()
                if any_available_image:
                    image_to_send_obj = any_available_image
                    print(f"No flag=0 image found for '{vocab.word}'. Falling back to first available image.")
                else:
                    print(f"No suitable image found for '{vocab.word}'. Sending default image.")

            vocab_id = vocab.id
            # Using 'none' as a string if no image is sent, so callback data format is consistent
            image_id_for_callback = str(image_to_send_obj.id) if image_to_send_obj else 'none'
            # Construct callback data strings for buttons
            callback_knew = f"knew:{vocab_id}:{image_id_for_callback}"
            callback_did_not_know = f"didnt_know:{vocab_id}:{image_id_for_callback}"

            if image_to_send_obj:
                try:
                    image_path = image_to_send_obj.image.path
                    word_escaped = html.escape(vocab.word)
                    meaning_escaped = html.escape(vocab.meaning)

                    if image_to_send_obj.caption:
                        description_escaped = html.escape(image_to_send_obj.caption)
                    elif vocab.description:
                        description_escaped = html.escape(vocab.description)
                    else:
                        description_escaped = html.escape('')

                    caption = (
                        f"Word: <b>{word_escaped}</b>\n\n"
                        f"Meaning: <tg-spoiler>{meaning_escaped}</tg-spoiler>\n\n"
                        + (f"Description: <tg-spoiler>{description_escaped}</tg-spoiler>" if description_escaped else "")
                    )

                    print(f"Sending Vocab: {vocab.word} (ID: {vocab.id}) with image from path: {image_path}. Callback knew: {callback_knew}")
               
                    send_photo_with_spoiler(chat_id, image_path, caption, vocab_id, callback_knew, callback_did_not_know)

                except AttributeError as e:
                    print(f"Error accessing image path or other attributes for '{vocab.word}': {e}. Check if vocab object is correct.")
                except Exception as e:
                    print(f"Error sending flashcard for '{vocab.word}': {type(e).__name__} - {e}")

            else:
                #sending the vocab with the default image
                print(f"No image for '{vocab.word}'. Sending the default image. Callback knew: {callback_knew}")
                image_path = 'media/img/immg.jpg'
                word_escaped = html.escape(vocab.word)
                meaning_escaped = html.escape(vocab.meaning)
                description_escaped = html.escape(vocab.description)

                caption = (
                        f"Word: <b>{word_escaped}</b>\n\n"
                        f"Meaning: <tg-spoiler>{meaning_escaped}</tg-spoiler>\n\n"
                        + (f"Description: <tg-spoiler>{description_escaped}</tg-spoiler>" if vocab.description else "")
                    )
                send_photo_with_spoiler(chat_id, image_path, caption, vocab_id, callback_knew, callback_did_not_know)

    print("Vocabulary batch processing finished.")









