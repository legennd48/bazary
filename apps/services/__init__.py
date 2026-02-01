"""
Services Domain App.

This app handles service offerings:
- Service catalog with pricing and duration
- Service categories
- Provider/staff assignment
- Service policies and terms
- Availability configuration (integrates with bookings)

Services are "what can be offered" - separate from bookings
which are "time reservations."
"""

default_app_config = "apps.services.apps.ServicesConfig"
