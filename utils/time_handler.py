import ntplib
import time
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_MISSED
import socket

class ResilientTimeHandler:
    """
    Ultra-resilient time handler for Android with:
    - Multi-server NTP synchronization with fallbacks
    - DST (Daylight Saving Time) awareness and handling
    - Network interruption tolerance
    - Mobile network optimization
    - Time drift correction
    - Timezone management for Poland/Europe
    """
    
    def __init__(self, timezone: str = 'Europe/Warsaw'):
        self.logger = logging.getLogger(__name__)
        
        # Comprehensive NTP server list optimized for Poland/Europe
        self.ntp_servers = [
            "0.pl.pool.ntp.org",
            "1.pl.pool.ntp.org", 
            "2.pl.pool.ntp.org",
            "3.pl.pool.ntp.org",
            "0.europe.pool.ntp.org",
            "1.europe.pool.ntp.org",
            "pool.ntp.org",
            "time.google.com",
            "time.cloudflare.com",
            "time.nist.gov",
            "tempus1.gum.gov.pl",  # Polish National Time Server
            "tempus2.gum.gov.pl"
        ]
        
        self.last_sync: Optional[datetime] = None
        self.offset: float = 0.0
        self.timezone = pytz.timezone(timezone)
        self.sync_interval = 3600  # 1 hour
        self.max_retries = 2  # Reduced for mobile
        self.timeout = 8  # Reduced timeout for mobile networks
        self.drift_tolerance = 5.0  # seconds
        
        # Mobile network optimizations
        self.mobile_mode = True
        self.last_network_check = 0
        self.network_available = True
        
    def _check_network_connectivity(self) -> bool:
        """Quick network connectivity check optimized for mobile"""
        current_time = time.time()
        
        # Cache network status for 30 seconds to reduce battery usage
        if current_time - self.last_network_check < 30:
            return self.network_available
            
        try:
            # Quick DNS lookup test
            socket.gethostbyname('google.com')
            self.network_available = True
            self.logger.debug("Network connectivity: OK")
        except (socket.gaierror, socket.timeout):
            self.network_available = False
            self.logger.warning("Network connectivity: FAILED")
            
        self.last_network_check = current_time
        return self.network_available
        
    async def get_ntp_time(self) -> Optional[float]:
        """Get NTP time with mobile-optimized fallback strategy"""
        if not self._check_network_connectivity():
            self.logger.warning("No network - skipping NTP sync")
            return None
            
        # Try servers in order, but with mobile-friendly timeouts
        for i, server in enumerate(self.ntp_servers[:8]):  # Limit to first 8 servers
            for attempt in range(self.max_retries):
                try:
                    self.logger.debug(f"Attempting NTP sync with {server} (attempt {attempt+1})")
                    
                    loop = asyncio.get_event_loop()
                    client = ntplib.NTPClient()
                    
                    # Shorter timeout for mobile networks
                    timeout = self.timeout if attempt == 0 else self.timeout * 2
                    
                    resp = await loop.run_in_executor(
                        None,
                        lambda: client.request(server, timeout=timeout, version=3)
                    )
                    
                    # Validate response
                    if resp.offset is None or abs(resp.offset) > 3600:  # > 1 hour is suspicious
                        self.logger.warning(f"Suspicious NTP response from {server}: offset={resp.offset}")
                        continue
                        
                    self.logger.info(f"NTP sync successful: {server} (offset: {resp.offset:.3f}s)")
                    return resp.tx_time
                    
                except (socket.timeout, socket.gaierror, ntplib.NTPException) as e:
                    self.logger.debug(f"NTP attempt failed {server}: {e}")
                    if attempt < self.max_retries - 1:
                        # Exponential backoff with jitter for mobile
                        await asyncio.sleep(min(2 ** attempt + 0.1 * i, 5))
                except Exception as e:
                    self.logger.warning(f"Unexpected NTP error {server}: {e}")
                    break  # Don't retry on unexpected errors
                    
        self.logger.error("All NTP servers failed - using local time")
        return None
        
    async def sync_time(self) -> bool:
        """Synchronize time with enhanced error handling"""
        try:
            ntp_time = await self.get_ntp_time()
            if ntp_time is None:
                return False
                
            current_local = time.time()
            self.offset = ntp_time - current_local
            
            # Detect significant time drift (potential DST change or system issue)
            if abs(self.offset) > self.drift_tolerance:
                self.logger.warning(
                    f"Significant time drift detected: {self.offset:.2f}s "
                    f"(tolerance: {self.drift_tolerance}s)"
                )
                
                # Check for DST transition
                if self._is_dst_transition_period():
                    self.logger.info("Time drift may be due to DST transition")
                    
            self.last_sync = datetime.now(self.timezone)
            
            self.logger.info(
                f"Time synchronized successfully: offset={self.offset:.3f}s, "
                f"local_time={datetime.fromtimestamp(current_local, self.timezone)}, "
                f"ntp_time={datetime.fromtimestamp(ntp_time, self.timezone)}"
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Time synchronization failed: {e}")
            return False
            
    def _is_dst_transition_period(self) -> bool:
        """Check if we're in a DST transition period"""
        try:
            now = datetime.now(self.timezone)
            
            # Check if we're within a week of DST transitions (spring/fall)
            # DST typically starts last Sunday in March, ends last Sunday in October in Europe
            
            if now.month == 3:  # March - spring transition
                return now.day >= 25
            elif now.month == 10:  # October - fall transition  
                return now.day >= 25
            elif now.month in [2, 4, 9, 11]:  # Adjacent months
                return True
                
            return False
            
        except Exception:
            return False
            
    def get_current_time(self) -> datetime:
        """Get corrected current time with fallback to system time"""
        try:
            if self.last_sync is None:
                # No sync yet - use system time but log warning
                self.logger.debug("Using system time - no NTP sync available")
                return datetime.now(self.timezone)
                
            # Apply NTP correction to system time
            corrected_timestamp = time.time() + self.offset
            return datetime.fromtimestamp(corrected_timestamp, self.timezone)
            
        except Exception as e:
            self.logger.error(f"Error getting corrected time: {e}")
            return datetime.now(self.timezone)
            
    def is_sync_needed(self) -> bool:
        """Determine if time synchronization is needed"""
        if self.last_sync is None:
            return True
            
        # More frequent sync during DST transition periods
        interval = self.sync_interval // 2 if self._is_dst_transition_period() else self.sync_interval
        
        time_since_sync = datetime.now(self.timezone) - self.last_sync
        return time_since_sync > timedelta(seconds=interval)
        
    def get_sync_status(self) -> dict:
        """Get detailed synchronization status"""
        return {
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'offset_seconds': self.offset,
            'timezone': str(self.timezone),
            'network_available': self.network_available,
            'sync_needed': self.is_sync_needed(),
            'dst_transition_period': self._is_dst_transition_period()
        }

class ResilientScheduler:
    """
    Ultra-resilient scheduler for Android TPMB with:
    - Automatic recovery from crashes and interruptions
    - NTP time synchronization integration
    - Mobile-friendly job management
    - DST-aware scheduling
    - Network interruption handling
    """
    
    def __init__(self, timezone: str = 'Europe/Warsaw'):
        self.timezone = pytz.timezone(timezone)
        self.time_handler = ResilientTimeHandler(timezone)
        self.scheduler = None
        self.logger = logging.getLogger(__name__)
        self._running = False
        self._jobs_config = {}  # Store job configurations for recovery
        
    async def initialize(self):
        """Initialize scheduler with time synchronization"""
        try:
            # Perform initial time sync
            sync_success = await self.time_handler.sync_time()
            if sync_success:
                self.logger.info("Initial time synchronization successful")
            else:
                self.logger.warning("Initial time sync failed - continuing with system time")
                
            # Configure scheduler with Android-friendly settings
            self.scheduler = AsyncIOScheduler(
                timezone=self.timezone,
                job_defaults={
                    'coalesce': True,      # Combine missed jobs
                    'max_instances': 1,    # One instance per job
                    'misfire_grace_time': 300,  # 5min tolerance for missed jobs
                    'replace_existing': True
                },
                # Reduce memory usage on mobile
                executors={
                    'default': {'type': 'asyncio', 'max_workers': 2}
                }
            )
            
            # Add event listeners for monitoring
            self.scheduler.add_listener(self._job_error_listener, EVENT_JOB_ERROR)
            self.scheduler.add_listener(self._job_missed_listener, EVENT_JOB_MISSED)
            
            # Add periodic time synchronization job
            self.scheduler.add_job(
                self._periodic_time_sync,
                'interval',
                seconds=3600,  # Every hour
                id='time_sync_job',
                name='NTP Time Synchronization',
                replace_existing=True
            )
            
            self.logger.info("Resilient scheduler initialized")
            
        except Exception as e:
            self.logger.error(f"Scheduler initialization failed: {e}")
            raise
            
    async def _periodic_time_sync(self):
        """Periodic time synchronization with error handling"""
        try:
            if self.time_handler.is_sync_needed():
                self.logger.debug("Performing scheduled time synchronization")
                await self.time_handler.sync_time()
            else:
                self.logger.debug("Time sync not needed")
                
        except Exception as e:
            self.logger.error(f"Periodic time sync failed: {e}")
            
    def _job_error_listener(self, event):
        """Handle job execution errors"""
        self.logger.error(
            f"Job {event.job_id} crashed: {event.exception}\n"
            f"Traceback: {event.traceback}"
        )
        
    def _job_missed_listener(self, event):
        """Handle missed jobs (e.g., due to network interruption)"""
        self.logger.warning(
            f"Job {event.job_id} missed scheduled time: "
            f"scheduled={event.scheduled_run_time}, "
            f"attempted={datetime.now(self.timezone)}"
        )
        
    async def start(self):
        """Start scheduler with recovery mechanism"""
        if not self.scheduler:
            await self.initialize()
            
        try:
            self.scheduler.start()
            self._running = True
            self.logger.info("Resilient scheduler started")
            
            # Log scheduler status
            status = self.time_handler.get_sync_status()
            self.logger.info(f"Time sync status: {status}")
            
        except Exception as e:
            self.logger.error(f"Scheduler start failed: {e}")
            # Auto-retry after delay
            await asyncio.sleep(10)
            await self.start()
            
    def add_job(self, func, trigger, **kwargs):
        """Add job with automatic error recovery wrapping"""
        if not self.scheduler:
            raise RuntimeError("Scheduler not initialized")
            
        job_id = kwargs.get('id', f"job_{len(self._jobs_config)}")
        kwargs['id'] = job_id
        
        # Store job config for potential recovery
        self._jobs_config[job_id] = {
            'func': func,
            'trigger': trigger,
            'kwargs': kwargs
        }
        
        async def wrapped_func(*args, **func_kwargs):
            """Wrapper with comprehensive error handling and time checking"""
            try:
                # Check time synchronization before critical jobs
                if self.time_handler.is_sync_needed():
                    self.logger.debug(f"Syncing time before job {job_id}")
                    await self.time_handler.sync_time()
                    
                # Execute the actual function
                await func(*args, **func_kwargs)
                
            except asyncio.CancelledError:
                self.logger.info(f"Job {job_id} was cancelled")
                raise
            except Exception as e:
                self.logger.error(f"Job {job_id} failed: {e}")
                
                # Implement retry logic for critical jobs
                if kwargs.get('retry_on_failure', False):
                    retry_count = getattr(wrapped_func, '_retry_count', 0)
                    if retry_count < 3:
                        wrapped_func._retry_count = retry_count + 1
                        self.logger.info(f"Retrying job {job_id} (attempt {retry_count + 1})")
                        await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                        await wrapped_func(*args, **func_kwargs)
                    else:
                        self.logger.error(f"Job {job_id} failed after 3 retries")
                        
        return self.scheduler.add_job(wrapped_func, trigger, **kwargs)
        
    def remove_job(self, job_id: str):
        """Remove job and clean up configuration"""
        if self.scheduler:
            try:
                self.scheduler.remove_job(job_id)
            except:
                pass
                
        if job_id in self._jobs_config:
            del self._jobs_config[job_id]
            
    def get_job(self, job_id: str):
        """Get job by ID"""
        if self.scheduler:
            return self.scheduler.get_job(job_id)
        return None
        
    def shutdown(self):
        """Graceful shutdown of scheduler"""
        if self.scheduler and self._running:
            try:
                self.scheduler.shutdown(wait=False)  # Non-blocking for mobile
                self._running = False
                self.logger.info("Resilient scheduler shutdown completed")
            except Exception as e:
                self.logger.error(f"Scheduler shutdown error: {e}")
                
    def get_status(self) -> dict:
        """Get comprehensive scheduler status"""
        status = {
            'running': self._running,
            'jobs_count': len(self._jobs_config),
            'time_sync': self.time_handler.get_sync_status()
        }
        
        if self.scheduler:
            status['active_jobs'] = [
                {
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None
                }
                for job in self.scheduler.get_jobs()
            ]
            
        return status
