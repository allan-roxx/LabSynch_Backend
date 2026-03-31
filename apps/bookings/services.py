"""
Booking module business logic for availability, pricing, and lifecycle.
"""

from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.equipment.models import Equipment, PricingRule
from apps.users.models import User, SchoolProfile
from .models import Booking, BookingItem, BookingStatus, Cart, CartItem
from apps.audit.services import log_action
from apps.audit.models import AuditLog


def get_available_quantity(equipment_id: str, start_date: date, end_date: date) -> int:
    """
    Check the real-time availability of an equipment item between two dates.
    Accounts for overlapping confirmed/paid/issued bookings.
    """
    equipment = Equipment.objects.get(id=equipment_id)
    if not equipment.is_active:
        return 0

    # Find overlapping bookings that reserve stock
    overlapping_statuses = [
        BookingStatus.PENDING,
        BookingStatus.CONFIRMED,
        BookingStatus.PAID,
        BookingStatus.ISSUED,
        BookingStatus.OVERDUE,
    ]

    reserved_qty = BookingItem.objects.filter(
        equipment_id=equipment_id,
        booking__status__in=overlapping_statuses,
        booking__pickup_date__lte=end_date,
        booking__return_date__gte=start_date,
    ).aggregate(total=Sum("quantity"))["total"] or 0

    available = equipment.total_quantity - reserved_qty
    return max(0, available)


def calculate_price(equipment: Equipment, quantity: int, duration_days: int) -> Decimal:
    """
    Calculate the price for a single booking item, applying the best active pricing rule.
    """
    base_price = equipment.unit_price_per_day * quantity * duration_days

    # Find applicable pricing rules for this duration
    rules = PricingRule.objects.filter(
        category=equipment.category,
        min_days__lte=duration_days,
        max_days__gte=duration_days,
        is_active=True,
    )
    
    # Apply highest discount percentage
    best_discount_pct = Decimal("0.0")
    for rule in rules:
        if rule.effective_to and rule.effective_to < timezone.now().date():
            continue
        if rule.effective_from > timezone.now().date():
            continue
        if rule.discount_percentage > best_discount_pct:
            best_discount_pct = rule.discount_percentage

    discount_amount = (base_price * best_discount_pct) / Decimal("100.0")
    final_price = base_price - discount_amount

    return final_price


def generate_booking_reference() -> str:
    """Generates a human-readable unique reference."""
    year = timezone.now().year
    count = Booking.objects.filter(created_at__year=year).count() + 1
    return f"BK-{year}-{count:04d}"


@transaction.atomic
def create_booking(
    user: User,
    pickup_date: date,
    return_date: date,
    items_data: list,
    special_instructions: str = "",
) -> Booking:
    """
    Creates a booking and items. Wraps in atomic transaction to prevent overselling.

    Raises ValidationError if any item exceeds availability.
    """
    if return_date <= pickup_date:
        raise ValidationError({"return_date": "Return date must be after pickup date."})

    try:
        school_profile = user.school_profile
    except SchoolProfile.DoesNotExist:
        raise ValidationError({"user": "Only school accounts can make bookings."})

    duration_days = (return_date - pickup_date).days
    total_amount = Decimal("0.0")

    # We must lock the equipment rows we are checking to prevent race conditions
    equipment_ids = [item["equipment"] for item in items_data]
    # lock rows in order to avoid deadlocks
    equipment_ids.sort()
    
    # Select for update to lock the rows until transaction completes
    equipments = Equipment.objects.select_for_update().filter(id__in=equipment_ids)
    equipment_map = {str(eq.id): eq for eq in equipments}

    booking_items_to_create = []

    for item_data in items_data:
        eq_id = str(item_data["equipment"])
        quantity = item_data["quantity"]

        if eq_id not in equipment_map:
            raise ValidationError({f"item_{eq_id}": "Equipment not found or inactive."})
            
        equipment = equipment_map[eq_id]

        available = get_available_quantity(eq_id, pickup_date, return_date)
        if quantity > available:
            raise ValidationError(
                {
                    "quantity": f"Only {available} '{equipment.equipment_name}' available for the selected dates."
                }
            )

        subtotal = calculate_price(equipment, quantity, duration_days)
        total_amount += subtotal

        # Decrease real-time display quantity
        equipment.available_quantity -= quantity
        equipment.save(update_fields=["available_quantity", "updated_at"])

        booking_items_to_create.append(
            BookingItem(
                equipment=equipment,
                quantity=quantity,
                unit_price=equipment.unit_price_per_day,
                subtotal=subtotal,
            )
        )

    # Create Booking
    booking = Booking.objects.create(
        booking_reference=generate_booking_reference(),
        school_profile=school_profile,
        pickup_date=pickup_date,
        return_date=return_date,
        total_amount=total_amount,
        special_instructions=special_instructions,
        status=BookingStatus.PENDING,
    )

    # Attach to items and save in bulk
    for bi in booking_items_to_create:
        bi.booking = booking
    BookingItem.objects.bulk_create(booking_items_to_create)

    log_action(
        action=AuditLog.Action.CREATE,
        instance=booking,
        actor=user,
        changes={"booking_reference": booking.booking_reference, "status": booking.status},
    )

    from apps.notifications.tasks import send_booking_confirmation
    send_booking_confirmation.delay(str(booking.id))

    return booking


@transaction.atomic
def cancel_booking(booking: Booking, user: User) -> Booking:
    """
    Cancels a PENDING or CONFIRMED booking and restores availability.
    """
    if booking.school_profile.user != user and user.user_type != "ADMIN":
        raise ValidationError({"detail": "You do not have permission to cancel this booking."})

    if booking.status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
        raise ValidationError(
            {"status": f"Cannot cancel booking in {booking.status} state."}
        )

    booking.status = BookingStatus.CANCELLED
    booking.save(update_fields=["status", "updated_at"])

    log_action(
        action=AuditLog.Action.CANCEL,
        instance=booking,
        actor=user,
        changes={"status": ["PENDING/CONFIRMED", BookingStatus.CANCELLED]},
    )

    # Restore quantities
    equipment_ids = [str(item.equipment_id) for item in booking.booking_items.all()]
    equipment_ids.sort()
    
    equipments = Equipment.objects.select_for_update().filter(id__in=equipment_ids)
    eq_map = {str(eq.id): eq for eq in equipments}

    for item in booking.booking_items.all():
        eq = eq_map.get(str(item.equipment_id))
        if eq:
            eq.available_quantity += item.quantity
            eq.save(update_fields=["available_quantity", "updated_at"])

    return booking


# ---------------------------------------------------------------------------
# Cart services
# ---------------------------------------------------------------------------

def get_or_create_cart(user: User) -> Cart:
    """Return the user's existing cart or create an empty one."""
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def add_or_update_cart_item(user: User, equipment_id: str, quantity: int) -> CartItem:
    """
    Add an equipment item to the cart. If it already exists, update quantity.
    Raises ValidationError if equipment is not found or inactive.
    """
    try:
        equipment = Equipment.objects.get(id=equipment_id, is_active=True)
    except Equipment.DoesNotExist:
        raise ValidationError("Equipment not found or is not available.")

    cart = get_or_create_cart(user)
    item, created = CartItem.objects.get_or_create(
        cart=cart,
        equipment=equipment,
        defaults={"quantity": quantity},
    )
    if not created:
        item.quantity = quantity
        item.save(update_fields=["quantity", "updated_at"])

    return item


def update_cart_item_quantity(user: User, item_id: str, quantity: int) -> CartItem:
    """
    Change the quantity of an existing cart item owned by the user.
    Raises ValidationError if the item is not found.
    """
    try:
        item = CartItem.objects.select_related("cart").get(id=item_id, cart__user=user)
    except CartItem.DoesNotExist:
        raise ValidationError("Cart item not found.")

    item.quantity = quantity
    item.save(update_fields=["quantity", "updated_at"])
    return item


def remove_cart_item(user: User, item_id: str) -> None:
    """Remove a single item from the user's cart."""
    CartItem.objects.filter(id=item_id, cart__user=user).delete()


def set_cart_dates(
    user: User,
    pickup_date=None,
    return_date=None,
    special_instructions=None,
) -> Cart:
    """Set or update the pickup/return dates on the cart."""
    cart = get_or_create_cart(user)
    update_fields = ["updated_at"]

    if pickup_date is not None:
        cart.pickup_date = pickup_date
        update_fields.append("pickup_date")
    if return_date is not None:
        cart.return_date = return_date
        update_fields.append("return_date")
    if special_instructions is not None:
        cart.special_instructions = special_instructions
        update_fields.append("special_instructions")

    cart.save(update_fields=update_fields)
    return cart


def clear_cart(user: User) -> None:
    """Remove all items from the cart (keeps the cart row itself)."""
    try:
        cart = Cart.objects.get(user=user)
        cart.items.all().delete()
        cart.pickup_date = None
        cart.return_date = None
        cart.special_instructions = ""
        cart.save(update_fields=["pickup_date", "return_date", "special_instructions", "updated_at"])
    except Cart.DoesNotExist:
        pass


@transaction.atomic
def checkout_cart(user: User) -> Booking:
    """
    Convert the user's cart into a Booking.
    Validates dates, checks equipment availability, then calls create_booking.
    Clears the cart on success.
    Raises ValidationError on any constraint violation.
    """
    try:
        cart = Cart.objects.prefetch_related("items__equipment").get(user=user)
    except Cart.DoesNotExist:
        raise ValidationError("Your cart is empty.")

    if not cart.items.exists():
        raise ValidationError("Your cart is empty.")

    if not cart.pickup_date or not cart.return_date:
        raise ValidationError(
            "Please set pickup and return dates before checking out."
        )

    items_data = [
        {"equipment_id": str(item.equipment_id), "quantity": item.quantity}
        for item in cart.items.select_related("equipment").all()
    ]

    booking = create_booking(
        user=user,
        pickup_date=cart.pickup_date,
        return_date=cart.return_date,
        items_data=items_data,
        special_instructions=cart.special_instructions,
    )

    # Clear cart after successful booking
    cart.items.all().delete()
    cart.pickup_date = None
    cart.return_date = None
    cart.special_instructions = ""
    cart.save(update_fields=["pickup_date", "return_date", "special_instructions", "updated_at"])

    return booking
