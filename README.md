# VocabBot - A Django & Telegram Vocabulary Assistant

VocabBot is a simple yet powerful web application designed to make vocabulary learning consistent and effortless. It connects its learning engine to your Telegram account, turning the chat app into a personal vocabulary coach. 
This transforms lost screenshots and forgotten notes into a powerful, contextual learning system.

## The Core Idea

This project is built on two core ideas:

1.  **Effortless Consistency:** The biggest hurdle in learning is often the initial effort required to start a study session. VocabBot removes this barrier by delivering reviews to Telegram, an app you already use daily.
2.  **The Power of Context:** We encounter new words everywhere—in books, articles, videos, social media applications, etc. We often screenshot them, but these images get lost in our photo galleries, stripped of their original, memorable context.
    VocabBot solves this by allowing you to save each word with an image and a note about *where you found it*. This context is then sent back to you during reviews, creating a powerful memory anchor.

## How It Works

1.  **Capture Words with Context:** When you encounter a new word, add it to the app. You can upload multiple images (like screenshots) and for each one, add a personal description answering, "Where did I see this word?".
2.  **Link Your Account:** After signing up, you'll receive a unique token to connect your account to the Telegram bot.
3.  **Receive Contextual Reviews:** The bot sends you your daily words. Each review includes not just the word, but also one of your saved images and the personal description you wrote, reminding you of the situation where you first learned it.
5.  **Smart Scheduling (SM2 Algorithm):** The words you receive are chosen based on the **SM2 spaced repetition algorithm** for efficient, long-term memorization.
6.  **Interactive Feedback:** Each word comes with two buttons: "✅ I knew it" and "❌ Didn't know".
7.  **Automatic Rescheduling:** Based on your feedback, the app automatically calculates the next optimal time for you to review that word.

## Features

-   **Web Interface:** A clean dashboard to add, search, and manage your vocabulary.
-   **Telegram Integration:** A personal bot that acts as your daily study coach.
-   **Contextual Learning:** Save not just the word, but *where* you found it. The bot sends this context back to you, strengthening your memory.
-   **Multiple Images per Word:** Add several images and descriptions to a single word, each providing a unique contextual clue.
-   **Spaced Repetition:** Implements the SM2 algorithm to maximize learning efficiency.
-   **Interactive Feedback:** Provide instant feedback directly within Telegram to adjust your learning schedule.

## Technology Stack

-   **Backend:** Python, Django
-   **Database:** SQLite (or configurable for PostgreSQL/MySQL)
-   **Telegram Bot:** `python-telegram-bot`
-   **Scheduling & Bot Handling:** A custom management command (`run_scheduler`) that runs as a continuous process. It is responsible for both sending the daily scheduled reviews and listening for real-time user feedback from Telegram.

## Setup and Installation

To run this project locally, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/HamidehGH/VocabBot.git
    cd VocabBot
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Create a `.env` file in the project root and add the following:
    ```
    SECRET_KEY='your-django-secret-key'
    DEBUG=True
    TELEGRAM_BOT_TOKEN='your-telegram-bot-token-from-botfather'
    ```

5.  **Run database migrations:**
    ```bash
    python manage.py migrate
    ```

6.  **Start the development server:**
    Open a terminal and run:
    ```bash
    python manage.py runserver
    ```

7.  **Start the Telegram bot and scheduler:**
    Open a **second, separate terminal** and run:
    ```bash
    python manage.py run_scheduler
    ```
    This command starts the process that listens for bot updates and sends the daily vocabulary reviews. It needs to be running continuously alongside the web server.
