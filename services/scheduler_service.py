import schedule
import time
import threading
from datetime import date
from sqlalchemy.orm import Session
from config import SessionLocal, get_db
from fastapi import Depends
from services.spotlight_service import SpotlightService
from services.email_service import EmailService
from repositories.user_repository import UserRepository

class SchedulerService:
    def __init__(self):
        self.email_service = EmailService()
    
    def daily_job(self):
        """Runs daily - selects teacher of the day"""
        db = SessionLocal()
        try:
            spotlight_service = SpotlightService(db)
            spotlight_service.select_teacher_of_the_day()
            print("Daily job completed: Teacher of the day selected")
        except Exception as e:
            print(f"Error in daily_job: {e}")
        finally:
            db.close()
    
    def monday_job(self):
        """Runs on Mondays - selects district of the week"""
        db = SessionLocal()
        try:
            spotlight_service = SpotlightService(db)
            spotlight_service.select_district_of_the_week()
            print("Monday job completed: District of the week selected")
        except Exception as e:
            print(f"Error in monday_job: {e}")
        finally:
            db.close()
    
    def first_of_month_job(self):
        """Runs on first of month - selects county of the month"""
        if date.today().day != 1:
            print("Not the first of the month.")
            return
        
        db = SessionLocal()
        try:
            spotlight_service = SpotlightService(db)
            spotlight_service.select_county_of_the_month()
            print("First of month job completed: County of the month selected")
        except Exception as e:
            print(f"Error in first_of_month_job: {e}")
        finally:
            db.close()
    
    def tuesday_job(self, db: Session = Depends(get_db)):
        """Runs on Tuesdays - sends profile creation reminders"""
        try:
            user_repo = UserRepository(db)
            users = user_repo.get_users_without_profile()
            
            if users:
                print(f"Found {len(users)} users who need a profile reminder.")
                for user in users:
                    self.email_service.send_profile_reminder_email(user.email)
                print("Successfully sent all profile creation reminder emails.")
            else:
                print("No users found with a createCount of 0.")
        except Exception as e:
            print(f"Error in tuesday_job: {e}")
    
    def thursday_job(self):
        """Runs on Thursdays - sends validation reminders"""
        db = SessionLocal()
        try:
            user_repo = UserRepository(db)
            users = user_repo.get_all_new_users()
            
            if users:
                print(f"Found {len(users)} new users who need a validation reminder.")
                for user in users:
                    self.email_service.send_validation_reminder_email(user.email)
                print("Successfully sent all validation reminder emails.")
            else:
                print("No new users found.")
        except Exception as e:
            print(f"Error in thursday_job: {e}")
        finally:
            db.close()
    
    def schedule_jobs(self):
        """Set up all scheduled jobs"""
        schedule.every().day.at("10:00").do(self.daily_job)
        schedule.every().tuesday.at("15:00").do(self.tuesday_job)
        schedule.every().thursday.at("15:00").do(self.thursday_job)
        # Uncomment when ready to use:
        # schedule.every().monday.at("10:00").do(self.monday_job)
        # schedule.every().day.at("10:00").do(self.first_of_month_job)
        
        print("Scheduler started with the following jobs:")
        print("- Daily at 10:00: Teacher of the Day")
        print("- Tuesday at 15:00: Profile Creation Reminders")
        print("- Thursday at 15:00: Validation Reminders")
    
    def run_scheduler(self):
        """Run the scheduler in an infinite loop"""
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    def start_scheduler_thread(self):
        """Start the scheduler in a background thread"""
        self.schedule_jobs()
        schedule_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        schedule_thread.start()
        return schedule_thread