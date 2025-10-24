# TPMB Android Utils Package
"""
Enhanced utilities for TPMB Android with security, time handling, and multi-instance management
"""

from .security_manager import SecurityManager, SecureConfigManager
from .time_handler import ResilientTimeHandler, ResilientScheduler
from .bot_controller import BotController
from .multi_instance_manager import MultiInstanceManager

__version__ = "2.0.0"
__author__ = "pizdziaty-garfild"

__all__ = [
    "SecurityManager",
    "SecureConfigManager", 
    "ResilientTimeHandler",
    "ResilientScheduler",
    "BotController",
    "MultiInstanceManager"
]