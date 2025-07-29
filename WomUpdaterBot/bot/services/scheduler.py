import asyncio
import logging
from datetime import datetime, time
from typing import Callable, Optional
import pytz

class TaskScheduler:
    """Handles automated task scheduling"""
    
    def __init__(self, timezone: str = "Australia/Sydney"):
        self.timezone = pytz.timezone(timezone)
        self.logger = logging.getLogger("wom_bot.scheduler")
        self.scheduled_tasks = {}
        self.running = False
        
    async def schedule_daily_task(self, task_name: str, target_time: time, task_func: Callable, *args, **kwargs):
        """Schedule a task to run daily at specified time"""
        self.logger.info(f"Scheduling daily task '{task_name}' for {target_time} {self.timezone}")
        
        async def task_runner():
            while self.running:
                now = datetime.now(self.timezone)
                target_datetime = datetime.combine(now.date(), target_time).replace(tzinfo=self.timezone)
                
                # If target time has passed today, schedule for tomorrow
                if now >= target_datetime:
                    target_datetime = target_datetime.replace(day=target_datetime.day + 1)
                
                # Calculate seconds until target time
                sleep_seconds = (target_datetime - now).total_seconds()
                self.logger.info(f"Next execution of '{task_name}' in {sleep_seconds:.0f} seconds at {target_datetime}")
                
                try:
                    await asyncio.sleep(sleep_seconds)
                    
                    if self.running:  # Check if still running after sleep
                        self.logger.info(f"Executing scheduled task: {task_name}")
                        await task_func(*args, **kwargs)
                        self.logger.info(f"Completed scheduled task: {task_name}")
                        
                except asyncio.CancelledError:
                    self.logger.info(f"Scheduled task '{task_name}' was cancelled")
                    break
                except Exception as e:
                    self.logger.error(f"Error in scheduled task '{task_name}': {str(e)}")
                    # Continue running despite errors
                    await asyncio.sleep(60)  # Wait 1 minute before retrying
        
        # Start the task runner
        task = asyncio.create_task(task_runner())
        self.scheduled_tasks[task_name] = task
        
    def start_scheduler(self):
        """Start the scheduler"""
        self.running = True
        self.logger.info("Task scheduler started")
        
    async def stop_scheduler(self):
        """Stop the scheduler and cancel all tasks"""
        self.running = False
        self.logger.info("Stopping task scheduler...")
        
        for task_name, task in self.scheduled_tasks.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            self.logger.info(f"Cancelled scheduled task: {task_name}")
        
        self.scheduled_tasks.clear()
        self.logger.info("Task scheduler stopped")
        
    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self.running
        
    def get_scheduled_tasks(self) -> list:
        """Get list of scheduled task names"""
        return list(self.scheduled_tasks.keys())