import asyncio
import json
import os
import signal
import sys
from pathlib import Path
from typing import Dict, List, Optional
import logging
from datetime import datetime

class MultiInstanceManager:
    """
    Advanced multi-instance manager for Android TPMB:
    - Concurrent bot instance management
    - Process isolation and monitoring
    - Resource usage optimization for mobile
    - Instance health checking
    - Graceful shutdown coordination
    - Configuration management per instance
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.instances: Dict[str, dict] = {}
        self.base_dir = Path('instances')
        self.base_dir.mkdir(exist_ok=True)
        
        # Mobile optimization settings
        self.max_concurrent_instances = 5  # Limit for mobile devices
        self.health_check_interval = 300  # 5 minutes
        self.cleanup_interval = 600  # 10 minutes
        
        # Instance registry file
        self.registry_file = self.base_dir / 'registry.json'
        self._load_registry()
        
    def _load_registry(self):
        """Load instance registry from file"""
        try:
            if self.registry_file.exists():
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.instances = data.get('instances', {})
                    self.logger.info(f"Loaded {len(self.instances)} instances from registry")
        except Exception as e:
            self.logger.error(f"Failed to load registry: {e}")
            self.instances = {}
            
    def _save_registry(self):
        """Save instance registry to file"""
        try:
            registry_data = {
                'instances': self.instances,
                'last_updated': datetime.now().isoformat(),
                'manager_version': '2.0'
            }
            
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(registry_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Failed to save registry: {e}")
            
    def create_instance(self, instance_name: str, config: dict = None) -> bool:
        """Create a new bot instance with configuration"""
        try:
            if instance_name in self.instances:
                self.logger.error(f"Instance '{instance_name}' already exists")
                return False
                
            if len(self.instances) >= self.max_concurrent_instances:
                self.logger.error(f"Maximum instances limit reached ({self.max_concurrent_instances})")
                return False
                
            # Validate instance name
            if not self._validate_instance_name(instance_name):
                self.logger.error(f"Invalid instance name: {instance_name}")
                return False
                
            # Create instance directories
            instance_dir = self.base_dir / instance_name
            config_dir = instance_dir / 'config'
            logs_dir = instance_dir / 'logs'
            
            for directory in [instance_dir, config_dir, logs_dir]:
                directory.mkdir(parents=True, exist_ok=True)
                
            # Create default configuration
            default_config = {
                'name': instance_name,
                'created_at': datetime.now().isoformat(),
                'status': 'created',
                'pid': None,
                'auto_start': config.get('auto_start', False) if config else False,
                'interval_minutes': config.get('interval_minutes', 1) if config else 1,
                'admin_ids': config.get('admin_ids', []) if config else [],
                'description': config.get('description', f'Bot instance: {instance_name}') if config else f'Bot instance: {instance_name}'
            }
            
            # Save instance config
            self.instances[instance_name] = default_config
            self._save_registry()
            
            # Create initial configuration files
            self._create_initial_config(config_dir, default_config)
            
            self.logger.info(f"Instance '{instance_name}' created successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create instance '{instance_name}': {e}")
            return False
            
    def _validate_instance_name(self, name: str) -> bool:
        """Validate instance name for filesystem compatibility"""
        if not name or len(name) < 1 or len(name) > 50:
            return False
            
        # Allow alphanumeric, dash, underscore
        import re
        return re.match(r'^[a-zA-Z0-9_-]+$', name) is not None
        
    def _create_initial_config(self, config_dir: Path, instance_config: dict):
        """Create initial configuration files for new instance"""
        try:
            # Create settings.txt
            settings_file = config_dir / 'settings.txt'
            with open(settings_file, 'w', encoding='utf-8') as f:
                f.write(f"interval_minutes={instance_config['interval_minutes']}\n")
                f.write(f"admin_ids={','.join(map(str, instance_config['admin_ids']))}\n")
                
            # Create empty groups.txt
            groups_file = config_dir / 'groups.txt'
            groups_file.touch()
            
            # Create default messages.txt
            messages_file = config_dir / 'messages.txt'
            with open(messages_file, 'w', encoding='utf-8') as f:
                f.write(f"Hello from {instance_config['name']}!\n")
                
        except Exception as e:
            self.logger.error(f"Failed to create initial config: {e}")
            
    def delete_instance(self, instance_name: str, force: bool = False) -> bool:
        """Delete an instance and its data"""
        try:
            if instance_name not in self.instances:
                self.logger.error(f"Instance '{instance_name}' does not exist")
                return False
                
            instance_info = self.instances[instance_name]
            
            # Check if instance is running
            if instance_info.get('status') == 'running' and not force:
                self.logger.error(f"Instance '{instance_name}' is running. Stop it first or use force=True")
                return False
                
            # Stop instance if running
            if instance_info.get('status') == 'running':
                self.stop_instance(instance_name)
                
            # Remove instance directory
            instance_dir = self.base_dir / instance_name
            if instance_dir.exists():
                import shutil
                shutil.rmtree(instance_dir)
                
            # Remove from registry
            del self.instances[instance_name]
            self._save_registry()
            
            self.logger.info(f"Instance '{instance_name}' deleted successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete instance '{instance_name}': {e}")
            return False
            
    def list_instances(self) -> List[dict]:
        """List all instances with their status"""
        instances_list = []
        
        for name, config in self.instances.items():
            instance_info = config.copy()
            instance_info['name'] = name
            
            # Check actual status
            actual_status = self._check_instance_status(name)
            instance_info['actual_status'] = actual_status
            
            # Get resource usage if running
            if actual_status == 'running':
                instance_info['resources'] = self._get_instance_resources(name)
                
            instances_list.append(instance_info)
            
        return instances_list
        
    def _check_instance_status(self, instance_name: str) -> str:
        """Check actual status of instance process"""
        try:
            instance_info = self.instances.get(instance_name)
            if not instance_info:
                return 'unknown'
                
            pid = instance_info.get('pid')
            if not pid:
                return 'stopped'
                
            # Check if process exists
            try:
                os.kill(pid, 0)  # Signal 0 just checks existence
                return 'running'
            except (OSError, ProcessLookupError):
                # Process doesn't exist, update registry
                instance_info['status'] = 'stopped'
                instance_info['pid'] = None
                self._save_registry()
                return 'stopped'
                
        except Exception as e:
            self.logger.error(f"Error checking status for '{instance_name}': {e}")
            return 'error'
            
    def _get_instance_resources(self, instance_name: str) -> dict:
        """Get resource usage for running instance"""
        try:
            instance_info = self.instances.get(instance_name)
            pid = instance_info.get('pid') if instance_info else None
            
            if not pid:
                return {}
                
            # Basic resource info (Android-compatible)
            try:
                import psutil
                process = psutil.Process(pid)
                
                return {
                    'cpu_percent': process.cpu_percent(),
                    'memory_mb': process.memory_info().rss / 1024 / 1024,
                    'threads': process.num_threads(),
                    'status': process.status()
                }
            except ImportError:
                # Fallback without psutil
                return {'status': 'running', 'monitoring': 'limited'}
                
        except Exception as e:
            self.logger.debug(f"Could not get resources for '{instance_name}': {e}")
            return {}
            
    def get_instance_info(self, instance_name: str) -> Optional[dict]:
        """Get detailed information about specific instance"""
        if instance_name not in self.instances:
            return None
            
        info = self.instances[instance_name].copy()
        info['name'] = instance_name
        info['actual_status'] = self._check_instance_status(instance_name)
        
        # Add directory info
        instance_dir = self.base_dir / instance_name
        info['directory'] = str(instance_dir)
        info['directory_exists'] = instance_dir.exists()
        
        # Add log info
        logs_dir = instance_dir / 'logs'
        if logs_dir.exists():
            log_files = list(logs_dir.glob('*.log'))
            info['log_files'] = [str(f) for f in log_files]
            
        return info
        
    def stop_instance(self, instance_name: str) -> bool:
        """Stop a running instance"""
        try:
            instance_info = self.instances.get(instance_name)
            if not instance_info:
                self.logger.error(f"Instance '{instance_name}' does not exist")
                return False
                
            pid = instance_info.get('pid')
            if not pid:
                self.logger.warning(f"Instance '{instance_name}' is not running")
                return True
                
            # Try graceful shutdown first
            try:
                os.kill(pid, signal.SIGTERM)
                
                # Wait for graceful shutdown
                import time
                for _ in range(10):  # Wait up to 10 seconds
                    try:
                        os.kill(pid, 0)
                        time.sleep(1)
                    except (OSError, ProcessLookupError):
                        break
                else:
                    # Force kill if still running
                    self.logger.warning(f"Force killing instance '{instance_name}'")
                    os.kill(pid, signal.SIGKILL)
                    
            except (OSError, ProcessLookupError):
                pass  # Process already dead
                
            # Update registry
            instance_info['status'] = 'stopped'
            instance_info['pid'] = None
            instance_info['stopped_at'] = datetime.now().isoformat()
            self._save_registry()
            
            self.logger.info(f"Instance '{instance_name}' stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop instance '{instance_name}': {e}")
            return False
            
    def stop_all_instances(self) -> int:
        """Stop all running instances"""
        stopped_count = 0
        
        for instance_name in list(self.instances.keys()):
            if self._check_instance_status(instance_name) == 'running':
                if self.stop_instance(instance_name):
                    stopped_count += 1
                    
        self.logger.info(f"Stopped {stopped_count} instances")
        return stopped_count
        
    async def health_check_loop(self):
        """Continuous health monitoring loop"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                for instance_name in list(self.instances.keys()):
                    status = self._check_instance_status(instance_name)
                    
                    if status == 'error':
                        self.logger.warning(f"Instance '{instance_name}' in error state")
                        
                    # Update registry with current status
                    if instance_name in self.instances:
                        self.instances[instance_name]['last_checked'] = datetime.now().isoformat()
                        
                self._save_registry()
                
            except Exception as e:
                self.logger.error(f"Health check error: {e}")
                
    def get_summary(self) -> dict:
        """Get summary of all instances"""
        summary = {
            'total_instances': len(self.instances),
            'running': 0,
            'stopped': 0,
            'error': 0,
            'max_concurrent': self.max_concurrent_instances,
            'available_slots': self.max_concurrent_instances - len(self.instances)
        }
        
        for instance_name in self.instances:
            status = self._check_instance_status(instance_name)
            if status == 'running':
                summary['running'] += 1
            elif status == 'stopped':
                summary['stopped'] += 1
            else:
                summary['error'] += 1
                
        return summary
        
    def cleanup_orphaned_instances(self) -> int:
        """Clean up orphaned instance directories"""
        cleaned_count = 0
        
        try:
            if not self.base_dir.exists():
                return 0
                
            for item in self.base_dir.iterdir():
                if item.is_dir() and item.name not in self.instances:
                    if item.name != 'registry.json':
                        self.logger.info(f"Cleaning orphaned directory: {item.name}")
                        import shutil
                        shutil.rmtree(item)
                        cleaned_count += 1
                        
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
            
        return cleaned_count
