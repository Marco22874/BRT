"""
Services package for BRT Shipping Management Application
Contains background services like update checker
"""

from .updater import UpdateDownloader, UpdateChecker

__all__ = ['UpdateDownloader', 'UpdateChecker']
