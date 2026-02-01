"""
Booking Services.

Business logic for availability checking and booking operations.
"""

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.services.models import Service, ServiceProvider

from .models import (
    AvailabilitySchedule,
    AvailabilitySlot,
    BlockedTime,
    Booking,
    BookingStatus,
    BookingStatusHistory,
)


class SlotInfo:
    """Represents an available time slot."""
    
    def __init__(
        self,
        start_datetime: datetime,
        end_datetime: datetime,
        provider: Optional[ServiceProvider] = None,
    ):
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.provider = provider
    
    def to_dict(self) -> Dict:
        return {
            "start": self.start_datetime.isoformat(),
            "end": self.end_datetime.isoformat(),
            "provider_id": str(self.provider.id) if self.provider else None,
            "provider_name": (
                self.provider.user.get_full_name() if self.provider else None
            ),
        }


class AvailabilityEngine:
    """
    Engine for calculating available booking slots.
    
    Handles:
    - Provider availability schedules
    - Blocked times (vacations, breaks)
    - Existing bookings
    - Service duration and buffer times
    """
    
    def __init__(self, service: Service):
        self.service = service
    
    def get_available_slots(
        self,
        start_date: date,
        end_date: date,
        provider: Optional[ServiceProvider] = None,
        slot_interval_minutes: int = 30,
    ) -> List[SlotInfo]:
        """
        Get available booking slots for a date range.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            provider: Specific provider (optional)
            slot_interval_minutes: Interval between slot starts
        
        Returns:
            List of available SlotInfo objects
        """
        slots = []
        
        # Get providers to check
        providers = self._get_providers(provider)
        
        # For each day in range
        current_date = start_date
        while current_date <= end_date:
            for prov in providers:
                day_slots = self._get_day_slots(
                    current_date,
                    prov,
                    slot_interval_minutes,
                )
                slots.extend(day_slots)
            
            current_date += timedelta(days=1)
        
        return slots
    
    def _get_providers(
        self,
        provider: Optional[ServiceProvider],
    ) -> List[Optional[ServiceProvider]]:
        """Get list of providers to check availability for."""
        if provider:
            return [provider]
        
        # If service has providers, use them
        providers = list(
            self.service.providers.filter(is_active=True).select_related("user")
        )
        
        # If no providers, service itself handles booking
        return providers if providers else [None]
    
    def _get_day_slots(
        self,
        check_date: date,
        provider: Optional[ServiceProvider],
        interval_minutes: int,
    ) -> List[SlotInfo]:
        """Get available slots for a specific day and provider."""
        slots = []
        
        # Get availability windows for this day
        windows = self._get_availability_windows(check_date, provider)
        
        if not windows:
            return slots
        
        # Get blocked times
        blocked = self._get_blocked_times(check_date, provider)
        
        # Get existing bookings
        bookings = self._get_existing_bookings(check_date, provider)
        
        # Calculate service duration including buffers
        duration = self.service.total_duration_minutes
        
        # For each availability window
        for window_start, window_end in windows:
            # Generate potential slot start times
            current = window_start
            
            while current + timedelta(minutes=duration) <= window_end:
                slot_start = current
                slot_end = current + timedelta(minutes=duration)
                
                # Check if slot conflicts with blocked times or bookings
                if not self._has_conflict(slot_start, slot_end, blocked, bookings):
                    # Check advance booking limits
                    if self._is_bookable(slot_start):
                        slots.append(SlotInfo(slot_start, slot_end, provider))
                
                current += timedelta(minutes=interval_minutes)
        
        return slots
    
    def _get_availability_windows(
        self,
        check_date: date,
        provider: Optional[ServiceProvider],
    ) -> List[Tuple[datetime, datetime]]:
        """Get availability windows for a day."""
        windows = []
        
        # Get day of week (ISO: 1=Monday)
        day_of_week = check_date.isoweekday()
        
        # Find applicable schedules
        schedules = AvailabilitySchedule.objects.filter(
            is_active=True,
        ).prefetch_related("slots")
        
        if provider:
            schedules = schedules.filter(provider=provider)
        else:
            schedules = schedules.filter(service=self.service, provider__isnull=True)
        
        for schedule in schedules:
            if not schedule.is_effective_on(check_date):
                continue
            
            # Get slots for this day
            for slot in schedule.slots.filter(day_of_week=day_of_week):
                start = timezone.make_aware(
                    datetime.combine(check_date, slot.start_time)
                )
                end = timezone.make_aware(
                    datetime.combine(check_date, slot.end_time)
                )
                windows.append((start, end))
        
        return windows
    
    def _get_blocked_times(
        self,
        check_date: date,
        provider: Optional[ServiceProvider],
    ) -> List[Tuple[datetime, datetime]]:
        """Get blocked time periods for a day."""
        day_start = timezone.make_aware(datetime.combine(check_date, time.min))
        day_end = timezone.make_aware(datetime.combine(check_date, time.max))
        
        blocked = []
        
        query = Q(start_datetime__lt=day_end, end_datetime__gt=day_start)
        
        if provider:
            query &= Q(provider=provider)
        else:
            query &= Q(service=self.service, provider__isnull=True)
        
        for block in BlockedTime.objects.filter(query):
            blocked.append((block.start_datetime, block.end_datetime))
        
        return blocked
    
    def _get_existing_bookings(
        self,
        check_date: date,
        provider: Optional[ServiceProvider],
    ) -> List[Tuple[datetime, datetime]]:
        """Get existing bookings for a day."""
        day_start = timezone.make_aware(datetime.combine(check_date, time.min))
        day_end = timezone.make_aware(datetime.combine(check_date, time.max))
        
        bookings = []
        
        query = Q(
            service=self.service,
            start_datetime__lt=day_end,
            end_datetime__gt=day_start,
            status__in=[
                BookingStatus.PENDING,
                BookingStatus.CONFIRMED,
                BookingStatus.IN_PROGRESS,
            ],
        )
        
        if provider:
            query &= Q(provider=provider)
        
        for booking in Booking.objects.filter(query):
            # Include buffer times
            buffer_before = timedelta(minutes=self.service.buffer_before_minutes)
            buffer_after = timedelta(minutes=self.service.buffer_after_minutes)
            
            bookings.append((
                booking.start_datetime - buffer_before,
                booking.end_datetime + buffer_after,
            ))
        
        return bookings
    
    def _has_conflict(
        self,
        slot_start: datetime,
        slot_end: datetime,
        blocked: List[Tuple[datetime, datetime]],
        bookings: List[Tuple[datetime, datetime]],
    ) -> bool:
        """Check if slot conflicts with blocked times or bookings."""
        for block_start, block_end in blocked:
            if slot_start < block_end and slot_end > block_start:
                return True
        
        for book_start, book_end in bookings:
            if slot_start < book_end and slot_end > book_start:
                return True
        
        return False
    
    def _is_bookable(self, slot_start: datetime) -> bool:
        """Check if slot meets booking requirements."""
        now = timezone.now()
        
        # Minimum notice
        min_notice = timedelta(hours=self.service.min_notice_hours)
        if slot_start < now + min_notice:
            return False
        
        # Maximum advance booking
        max_advance = timedelta(days=self.service.advance_booking_days)
        if slot_start > now + max_advance:
            return False
        
        return True
    
    def check_slot_available(
        self,
        start_datetime: datetime,
        end_datetime: datetime,
        provider: Optional[ServiceProvider] = None,
        exclude_booking_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a specific slot is available.
        
        Returns:
            Tuple of (is_available, reason_if_not)
        """
        check_date = start_datetime.date()
        
        # Check availability windows
        windows = self._get_availability_windows(check_date, provider)
        in_window = any(
            window_start <= start_datetime and end_datetime <= window_end
            for window_start, window_end in windows
        )
        
        if not in_window:
            return False, "Slot is outside availability hours"
        
        # Check blocked times
        blocked = self._get_blocked_times(check_date, provider)
        for block_start, block_end in blocked:
            if start_datetime < block_end and end_datetime > block_start:
                return False, "Slot is blocked"
        
        # Check existing bookings
        query = Q(
            service=self.service,
            start_datetime__lt=end_datetime,
            end_datetime__gt=start_datetime,
            status__in=[
                BookingStatus.PENDING,
                BookingStatus.CONFIRMED,
                BookingStatus.IN_PROGRESS,
            ],
        )
        
        if provider:
            query &= Q(provider=provider)
        
        if exclude_booking_id:
            query &= ~Q(id=exclude_booking_id)
        
        if Booking.objects.filter(query).exists():
            return False, "Slot conflicts with existing booking"
        
        # Check booking requirements
        if not self._is_bookable(start_datetime):
            return False, "Slot does not meet booking requirements"
        
        return True, None


class BookingService:
    """
    Business logic for booking operations.
    """
    
    @staticmethod
    @transaction.atomic
    def create_booking(
        service: Service,
        customer,
        start_datetime: datetime,
        provider: Optional[ServiceProvider] = None,
        attendee_count: int = 1,
        attendee_names: Optional[List[str]] = None,
        addon_ids: Optional[List[str]] = None,
        customer_notes: str = "",
    ) -> Booking:
        """
        Create a new booking.
        
        Args:
            service: Service to book
            customer: Customer user
            start_datetime: Booking start time
            provider: Optional specific provider
            attendee_count: Number of attendees
            attendee_names: Names of attendees
            addon_ids: List of addon IDs
            customer_notes: Customer notes
        
        Returns:
            Created Booking instance
        
        Raises:
            ValueError: If slot is not available or validation fails
        """
        # Calculate end time
        duration = service.total_duration_minutes
        end_datetime = start_datetime + timedelta(minutes=duration)
        
        # Check availability
        engine = AvailabilityEngine(service)
        available, reason = engine.check_slot_available(
            start_datetime,
            end_datetime,
            provider,
        )
        
        if not available:
            raise ValueError(f"Slot not available: {reason}")
        
        # Validate attendee count
        if attendee_count < service.min_attendees:
            raise ValueError(
                f"Minimum {service.min_attendees} attendees required"
            )
        if attendee_count > service.max_attendees:
            raise ValueError(
                f"Maximum {service.max_attendees} attendees allowed"
            )
        
        # Calculate pricing
        if provider:
            unit_price = provider.effective_price
        else:
            unit_price = service.price
        
        # Process addons
        addons_data = []
        addon_total = Decimal("0.00")
        
        if addon_ids:
            from apps.services.models import ServiceAddon
            addons = ServiceAddon.objects.filter(
                id__in=addon_ids,
                service=service,
                is_active=True,
            )
            
            for addon in addons:
                addons_data.append({
                    "id": str(addon.id),
                    "name": addon.name,
                    "price": str(addon.price),
                    "duration_minutes": addon.duration_minutes,
                })
                addon_total += addon.price
        
        total_price = (unit_price * attendee_count) + addon_total
        
        # Create booking
        booking = Booking.objects.create(
            service=service,
            provider=provider,
            customer=customer,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            attendee_count=attendee_count,
            attendee_names=attendee_names or [],
            unit_price=unit_price,
            total_price=total_price,
            currency=service.currency,
            addons=addons_data,
            customer_notes=customer_notes,
            status=BookingStatus.PENDING,
        )
        
        # Record status history
        BookingStatusHistory.objects.create(
            booking=booking,
            from_status="",
            to_status=BookingStatus.PENDING,
            notes="Booking created",
        )
        
        return booking
    
    @staticmethod
    @transaction.atomic
    def confirm_booking(booking: Booking, user=None) -> Booking:
        """Confirm a pending booking."""
        if booking.status != BookingStatus.PENDING:
            raise ValueError(
                f"Cannot confirm booking in {booking.status} status"
            )
        
        old_status = booking.status
        booking.confirm(user)
        
        BookingStatusHistory.objects.create(
            booking=booking,
            from_status=old_status,
            to_status=BookingStatus.CONFIRMED,
            changed_by=user,
            notes="Booking confirmed",
        )
        
        return booking
    
    @staticmethod
    @transaction.atomic
    def cancel_booking(
        booking: Booking,
        user=None,
        reason: str = "",
        notes: str = "",
    ) -> Booking:
        """Cancel a booking."""
        if not booking.is_cancellable:
            raise ValueError("Booking cannot be cancelled")
        
        old_status = booking.status
        booking.cancel(user, reason, notes)
        
        BookingStatusHistory.objects.create(
            booking=booking,
            from_status=old_status,
            to_status=BookingStatus.CANCELLED,
            changed_by=user,
            notes=f"Cancelled: {reason}. {notes}".strip(),
        )
        
        return booking
    
    @staticmethod
    @transaction.atomic
    def reschedule_booking(
        booking: Booking,
        new_start_datetime: datetime,
        new_provider: Optional[ServiceProvider] = None,
        user=None,
    ) -> Booking:
        """
        Reschedule a booking to a new time.
        
        Creates a new booking and marks old one as rescheduled.
        """
        if booking.status in [
            BookingStatus.CANCELLED,
            BookingStatus.COMPLETED,
            BookingStatus.NO_SHOW,
        ]:
            raise ValueError(
                f"Cannot reschedule booking in {booking.status} status"
            )
        
        # Create new booking
        new_booking = BookingService.create_booking(
            service=booking.service,
            customer=booking.customer,
            start_datetime=new_start_datetime,
            provider=new_provider or booking.provider,
            attendee_count=booking.attendee_count,
            attendee_names=booking.attendee_names,
            addon_ids=[a["id"] for a in booking.addons],
            customer_notes=booking.customer_notes,
        )
        
        # Link to original
        new_booking.rescheduled_from = booking
        new_booking.save(update_fields=["rescheduled_from"])
        
        # Mark original as rescheduled
        old_status = booking.status
        booking.status = BookingStatus.RESCHEDULED
        booking.save(update_fields=["status", "updated_at"])
        
        BookingStatusHistory.objects.create(
            booking=booking,
            from_status=old_status,
            to_status=BookingStatus.RESCHEDULED,
            changed_by=user,
            notes=f"Rescheduled to {new_booking.reference}",
        )
        
        return new_booking
    
    @staticmethod
    @transaction.atomic
    def complete_booking(booking: Booking) -> Booking:
        """Mark booking as completed."""
        if booking.status != BookingStatus.CONFIRMED:
            raise ValueError(
                f"Cannot complete booking in {booking.status} status"
            )
        
        old_status = booking.status
        booking.complete()
        
        BookingStatusHistory.objects.create(
            booking=booking,
            from_status=old_status,
            to_status=BookingStatus.COMPLETED,
            notes="Booking completed",
        )
        
        return booking
    
    @staticmethod
    @transaction.atomic
    def mark_no_show(booking: Booking, user=None) -> Booking:
        """Mark customer as no-show."""
        if booking.status != BookingStatus.CONFIRMED:
            raise ValueError(
                f"Cannot mark no-show for booking in {booking.status} status"
            )
        
        old_status = booking.status
        booking.mark_no_show()
        
        BookingStatusHistory.objects.create(
            booking=booking,
            from_status=old_status,
            to_status=BookingStatus.NO_SHOW,
            changed_by=user,
            notes="Customer did not show up",
        )
        
        return booking
