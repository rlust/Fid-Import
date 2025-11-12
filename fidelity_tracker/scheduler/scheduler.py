"""
Task Scheduler for automated portfolio syncs and enrichment
Uses APScheduler for flexible scheduling
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from loguru import logger
from datetime import datetime
from pathlib import Path
import json


class PortfolioScheduler:
    """
    Manages scheduled tasks for portfolio data collection and enrichment
    """

    def __init__(self, config):
        """
        Initialize scheduler with configuration

        Args:
            config: Config object with scheduler settings
        """
        self.config = config
        self.scheduler = BackgroundScheduler()
        self.state_file = Path("scheduler_state.json")

        # Setup event listeners
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )

    def _job_executed_listener(self, event):
        """Log job execution events"""
        if event.exception:
            logger.error(f"Job {event.job_id} failed: {event.exception}")
        else:
            logger.info(f"Job {event.job_id} executed successfully")

    def add_sync_job(self, sync_func):
        """
        Add portfolio sync job to scheduler

        Args:
            sync_func: Function to call for syncing (should handle all sync logic)
        """
        schedule = self.config.get('sync.schedule', '0 18 * * *')

        try:
            self.scheduler.add_job(
                func=sync_func,
                trigger=CronTrigger.from_crontab(schedule),
                id='portfolio_sync',
                name='Portfolio Data Sync',
                replace_existing=True,
                misfire_grace_time=3600  # Allow 1 hour grace period
            )
            logger.info(f"Sync job scheduled: {schedule}")
        except Exception as e:
            logger.error(f"Failed to add sync job: {e}")
            raise

    def add_enrichment_job(self, enrich_func):
        """
        Add enrichment job to scheduler

        Args:
            enrich_func: Function to call for enrichment
        """
        schedule = self.config.get('sync.enrichment_schedule', '0 19 * * 0')

        try:
            self.scheduler.add_job(
                func=enrich_func,
                trigger=CronTrigger.from_crontab(schedule),
                id='portfolio_enrichment',
                name='Portfolio Data Enrichment',
                replace_existing=True,
                misfire_grace_time=7200  # Allow 2 hour grace period
            )
            logger.info(f"Enrichment job scheduled: {schedule}")
        except Exception as e:
            logger.error(f"Failed to add enrichment job: {e}")
            raise

    def add_cleanup_job(self, cleanup_func):
        """
        Add cleanup job to scheduler

        Args:
            cleanup_func: Function to call for cleanup
        """
        # Run cleanup weekly on Sunday at 2 AM
        schedule = '0 2 * * 0'

        try:
            self.scheduler.add_job(
                func=cleanup_func,
                trigger=CronTrigger.from_crontab(schedule),
                id='portfolio_cleanup',
                name='Portfolio Data Cleanup',
                replace_existing=True,
                misfire_grace_time=3600
            )
            logger.info(f"Cleanup job scheduled: {schedule}")
        except Exception as e:
            logger.error(f"Failed to add cleanup job: {e}")
            raise

    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            self._save_state('running')
            logger.info("Scheduler started")
        else:
            logger.warning("Scheduler is already running")

    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            self._save_state('stopped')
            logger.info("Scheduler stopped")
        else:
            logger.warning("Scheduler is not running")

    def pause(self):
        """Pause all scheduled jobs"""
        if self.scheduler.running:
            self.scheduler.pause()
            self._save_state('paused')
            logger.info("Scheduler paused")

    def resume(self):
        """Resume all scheduled jobs"""
        if self.scheduler.running:
            self.scheduler.resume()
            self._save_state('running')
            logger.info("Scheduler resumed")

    def is_running(self):
        """Check if scheduler is running"""
        return self.scheduler.running

    def get_jobs(self):
        """Get list of scheduled jobs"""
        return self.scheduler.get_jobs()

    def get_job_status(self, job_id):
        """Get status of a specific job"""
        job = self.scheduler.get_job(job_id)
        if job:
            return {
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            }
        return None

    def get_all_job_status(self):
        """Get status of all jobs"""
        return [
            {
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            }
            for job in self.get_jobs()
        ]

    def run_job_now(self, job_id):
        """
        Trigger a job to run immediately

        Args:
            job_id: ID of the job to run
        """
        job = self.scheduler.get_job(job_id)
        if job:
            job.modify(next_run_time=datetime.now())
            logger.info(f"Triggered job {job_id} to run now")
        else:
            logger.error(f"Job {job_id} not found")
            raise ValueError(f"Job {job_id} not found")

    def remove_job(self, job_id):
        """Remove a job from the scheduler"""
        self.scheduler.remove_job(job_id)
        logger.info(f"Removed job {job_id}")

    def _save_state(self, state):
        """Save scheduler state to file"""
        try:
            state_data = {
                'state': state,
                'timestamp': datetime.now().isoformat(),
                'jobs': self.get_all_job_status()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save scheduler state: {e}")

    def load_state(self):
        """Load scheduler state from file"""
        try:
            if self.state_file.exists():
                with open(self.state_file) as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load scheduler state: {e}")
        return None

    def get_next_run_times(self):
        """Get next run times for all jobs"""
        return {
            job.id: job.next_run_time.isoformat() if job.next_run_time else None
            for job in self.get_jobs()
        }

    def reschedule_job(self, job_id, new_schedule):
        """
        Reschedule a job with new cron expression

        Args:
            job_id: ID of the job to reschedule
            new_schedule: New cron expression
        """
        try:
            self.scheduler.reschedule_job(
                job_id,
                trigger=CronTrigger.from_crontab(new_schedule)
            )
            logger.info(f"Rescheduled job {job_id} to: {new_schedule}")
        except Exception as e:
            logger.error(f"Failed to reschedule job {job_id}: {e}")
            raise
