"""
Notification services.

Email delivery is handled by Celery tasks in tasks.py and dispatched
directly from other app services (bookings, payments, issuances).
This module is reserved for any future shared notification helpers.
"""
