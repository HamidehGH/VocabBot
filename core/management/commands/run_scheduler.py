import json
import schedule
import time
import requests
import traceback
from django.core.management.base import BaseCommand
from core.tasks import get_updates, handle_callback_query, send_vocabulary_batch, handle_message


#Starts the telegram bot scheduler and update poller
class Command(BaseCommand):

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting scheduler and update poller...'))
        schedule.every().day.at("10:00").do(send_vocabulary_batch)
        self.stdout.write(f"Scheduled 'send_vocabulary_batch' to run daily at 10:00 AM.")
        self.stdout.write('Running scheduler and poller loop. Press CTRL+C to exit.')
        update_offset = None
        while True:
            try:
                updates = get_updates(offset=update_offset)
                if updates:
                    self.stdout.write(self.style.NOTICE(f"\n--- NEW UPDATES RECEIVED ---"))
                    for update in updates:
                        if 'callback_query' in update:
                            self.stdout.write(f"Processing callback query update ID: {update['update_id']}")
                            handle_callback_query(update)
                        elif 'message' in update:
                            self.stdout.write(f"Processing message update ID: {update['update_id']}")
                            handle_message(update)
                        else:
                            self.stdout.write(f"Ignoring update type: {list(update.keys())} for update ID: {update.get('update_id', 'Not Available')}")
                        update_offset = update['update_id'] + 1
                else:
                    self.stdout.write(".", ending="") 
                    self.stdout.flush()

                schedule.run_pending()
                time.sleep(0.5)

            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('\nScheduler stopped (KeyboardInterrupt).'))
                break

            except requests.exceptions.ConnectionError as e:
                 self.stderr.write(self.style.ERROR(f"Network Connection Error: {e}. Retrying in 15 seconds..."))
                 time.sleep(15)

            except requests.exceptions.Timeout as e:
                self.stderr.write(self.style.ERROR(f"Request Timed Out: {e}. Retrying in 5 seconds..."))
                time.sleep(5)

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error in main loop: {type(e).__name__} - {e}"))
                self.stderr.write(traceback.format_exc())
                self.stdout.write(self.style.WARNING("Sleeping for 5 seconds..."))
                time.sleep(5)

        self.stdout.write(self.style.SUCCESS('Scheduler finished.'))






















