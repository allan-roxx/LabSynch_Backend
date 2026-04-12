"""
Management command: seed_data
=============================
Populates the database with realistic initial data for LabSynch:

    - 6 Equipment Categories
    - 30 Equipment items spread across all categories
    - Pricing rules per category (volume discounts at 4+, 8+, 15+ days)
    - 4 School user accounts + SchoolProfile records

Usage::

    python manage.py seed_data
    python manage.py seed_data --clear   # wipe existing seed data first

"""

import logging
from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.equipment.models import Equipment, EquipmentCategory, PricingRule, TransportZone
from apps.users.models import AccountStatus, SchoolProfile, UserType

logger = logging.getLogger(__name__)

User = get_user_model()

# ---------------------------------------------------------------------------
# Seed data definitions
# ---------------------------------------------------------------------------

CATEGORIES = [
    {
        "category_name": "Glassware",
        "description": (
            "Laboratory glassware for measuring, mixing, and containing chemicals. "
            "Includes beakers, flasks, cylinders, and test tubes."
        ),
        "display_order": 1,
    },
    {
        "category_name": "Optical Instruments",
        "description": (
            "Magnification and viewing equipment including microscopes, "
            "spectroscopes, and magnifying glasses."
        ),
        "display_order": 2,
    },
    {
        "category_name": "Measuring Instruments",
        "description": (
            "Precision measurement tools: digital balances, triple-beam balances, "
            "Vernier calipers, thermometers, and measuring tapes."
        ),
        "display_order": 3,
    },
    {
        "category_name": "Chemical Equipment",
        "description": (
            "Apparatus for chemical procedures: separating funnels, burettes, "
            "pipettes, dropper bottles, and retort stands."
        ),
        "display_order": 4,
    },
    {
        "category_name": "Heating Equipment",
        "description": (
            "Devices for heating experiments: Bunsen burners, hot plate stirrers, "
            "water baths, crucibles, and wire gauze."
        ),
        "display_order": 5,
    },
    {
        "category_name": "Safety Equipment",
        "description": (
            "Personal protective equipment and safety apparatus: goggles, "
            "lab coats, gloves, and fire extinguishers."
        ),
        "display_order": 6,
    },
]

# Equipment per category. Keys map to EquipmentCategory.category_name.
EQUIPMENT = {
    "Glassware": [
        {
            "equipment_name": "Beaker 250 ml",
            "equipment_code": "EQP-001",
            "description": "Borosilicate glass beaker, 250 ml, graduated.",
            "total_quantity": 50,
            "available_quantity": 50,
            "unit_price_per_day": "40.00",
            "condition": "GOOD",
            "storage_location": "Rack A1",
        },
        {
            "equipment_name": "Beaker 500 ml",
            "equipment_code": "EQP-002",
            "description": "Borosilicate glass beaker, 500 ml, graduated.",
            "total_quantity": 40,
            "available_quantity": 40,
            "unit_price_per_day": "30.00",
            "condition": "GOOD",
            "storage_location": "Rack A1",
        },
        {
            "equipment_name": "Erlenmeyer Flask 250 ml",
            "equipment_code": "EQP-003",
            "description": "Conical flask, 250 ml, narrow neck, borosilicate glass.",
            "total_quantity": 30,
            "available_quantity": 30,
            "unit_price_per_day": "40.00",
            "condition": "GOOD",
            "storage_location": "Rack A2",
        },
        {
            "equipment_name": "Graduated Cylinder 100 ml",
            "equipment_code": "EQP-004",
            "description": "Borosilicate glass graduated cylinder, 100 ml.",
            "total_quantity": 25,
            "available_quantity": 25,
            "unit_price_per_day": "40.00",
            "condition": "GOOD",
            "storage_location": "Rack A2",
        },
        {
            "equipment_name": "Boiling Flask 500 ml",
            "equipment_code": "EQP-005",
            "description": "Round-bottom boiling flask, 500 ml, borosilicate glass.",
            "total_quantity": 20,
            "available_quantity": 20,
            "unit_price_per_day": "50.00",
            "condition": "GOOD",
            "storage_location": "Rack A3",
        },
        {
            "equipment_name": "Test Tubes (pack of 10)",
            "equipment_code": "EQP-006",
            "description": "Borosilicate glass test tubes, 150 × 16 mm — pack of 10.",
            "total_quantity": 60,
            "available_quantity": 60,
            "unit_price_per_day": "80.00",
            "condition": "GOOD",
            "storage_location": "Rack A3",
        },
    ],
    "Optical Instruments": [
        {
            "equipment_name": "Compound Microscope 400×",
            "equipment_code": "EQP-007",
            "description": (
                "Binocular compound microscope, 400× magnification, "
                "LED illuminator, 4× / 10× / 40× objectives."
            ),
            "total_quantity": 15,
            "available_quantity": 15,
            "unit_price_per_day": "120.00",
            "condition": "GOOD",
            "storage_location": "Cabinet B1",
        },
        {
            "equipment_name": "Stereo Microscope 20×",
            "equipment_code": "EQP-008",
            "description": (
                "Stereo / dissecting microscope, 20× magnification, "
                "for low-magnification 3D observation."
            ),
            "total_quantity": 10,
            "available_quantity": 10,
            "unit_price_per_day": "100.00",
            "condition": "GOOD",
            "storage_location": "Cabinet B1",
        },
        {
            "equipment_name": "Hand Magnifying Glass 10×",
            "equipment_code": "EQP-009",
            "description": "Optical glass magnifier, 10× magnification, 75 mm lens diameter.",
            "total_quantity": 30,
            "available_quantity": 30,
            "unit_price_per_day": "30.00",
            "condition": "GOOD",
            "storage_location": "Drawer B2",
        },
        {
            "equipment_name": "Spectroscope",
            "equipment_code": "EQP-010",
            "description": "Direct-view spectroscope for visible light spectrum analysis.",
            "total_quantity": 8,
            "available_quantity": 8,
            "unit_price_per_day": "50.00",
            "condition": "GOOD",
            "storage_location": "Cabinet B2",
        },
    ],
    "Measuring Instruments": [
        {
            "equipment_name": "Digital Analytical Balance 0.1 g",
            "equipment_code": "EQP-011",
            "description": "Electronic balance, capacity 600 g, readability 0.1 g, tare function.",
            "total_quantity": 10,
            "available_quantity": 10,
            "unit_price_per_day": "50.00",
            "condition": "GOOD",
            "storage_location": "Cabinet C1",
        },
        {
            "equipment_name": "Triple Beam Balance",
            "equipment_code": "EQP-012",
            "description": "Mechanical triple-beam balance, 610 g capacity, 0.1 g sensitivity.",
            "total_quantity": 12,
            "available_quantity": 12,
            "unit_price_per_day": "50.00",
            "condition": "GOOD",
            "storage_location": "Cabinet C1",
        },
        {
            "equipment_name": "Vernier Caliper 150 mm",
            "equipment_code": "EQP-013",
            "description": "Stainless steel Vernier caliper, 150 mm range, 0.02 mm resolution.",
            "total_quantity": 20,
            "available_quantity": 20,
            "unit_price_per_day": "50.00",
            "condition": "GOOD",
            "storage_location": "Drawer C2",
        },
        {
            "equipment_name": "Laboratory Thermometer −10 to 110 °C",
            "equipment_code": "EQP-014",
            "description": "Mercury-free glass thermometer, −10 to 110 °C, 1 °C graduation.",
            "total_quantity": 50,
            "available_quantity": 50,
            "unit_price_per_day": "70.00",
            "condition": "GOOD",
            "storage_location": "Drawer C2",
        },
        {
            "equipment_name": "Measuring Tape 5 m",
            "equipment_code": "EQP-015",
            "description": "Steel measuring tape, 5 m, retractable, mm graduation.",
            "total_quantity": 15,
            "available_quantity": 15,
            "unit_price_per_day": "80.00",
            "condition": "GOOD",
            "storage_location": "Drawer C3",
        },
    ],
    "Chemical Equipment": [
        {
            "equipment_name": "Separating Funnel 250 ml",
            "equipment_code": "EQP-016",
            "description": "Pear-shaped separating funnel, 250 ml, PTFE stopcock.",
            "total_quantity": 15,
            "available_quantity": 15,
            "unit_price_per_day": "50.00",
            "condition": "GOOD",
            "storage_location": "Rack D1",
        },
        {
            "equipment_name": "Burette 50 ml",
            "equipment_code": "EQP-017",
            "description": "Glass burette, 50 ml, PTFE stopcock, 0.1 ml graduation.",
            "total_quantity": 20,
            "available_quantity": 20,
            "unit_price_per_day": "50.00",
            "condition": "GOOD",
            "storage_location": "Rack D1",
        },
        {
            "equipment_name": "Pipette 10 ml",
            "equipment_code": "EQP-018",
            "description": "Volumetric glass pipette, 10 ml, Class A calibration.",
            "total_quantity": 40,
            "available_quantity": 40,
            "unit_price_per_day": "40.00",
            "condition": "GOOD",
            "storage_location": "Drawer D2",
        },
        {
            "equipment_name": "Retort Stand with Clamp",
            "equipment_code": "EQP-019",
            "description": "Cast-iron retort stand, 700 mm rod, with boss head and clamp.",
            "total_quantity": 20,
            "available_quantity": 20,
            "unit_price_per_day": "80.00",
            "condition": "GOOD",
            "storage_location": "Rack D2",
        },
        {
            "equipment_name": "Dropper Bottle 100 ml",
            "equipment_code": "EQP-020",
            "description": "Amber glass dropper bottle with glass pipette, 100 ml.",
            "total_quantity": 60,
            "available_quantity": 60,
            "unit_price_per_day": "10.00",
            "condition": "GOOD",
            "storage_location": "Drawer D3",
        },
    ],
    "Heating Equipment": [
        {
            "equipment_name": "Bunsen Burner",
            "equipment_code": "EQP-021",
            "description": "Natural gas / LPG Bunsen burner with air adjustment collar.",
            "total_quantity": 25,
            "available_quantity": 25,
            "unit_price_per_day": "40.00",
            "condition": "GOOD",
            "storage_location": "Cabinet E1",
        },
        {
            "equipment_name": "Hot Plate Magnetic Stirrer",
            "equipment_code": "EQP-022",
            "description": "Combined hot plate and magnetic stirrer, 300 °C max, 1000 rpm.",
            "total_quantity": 8,
            "available_quantity": 8,
            "unit_price_per_day": "90.00",
            "condition": "GOOD",
            "storage_location": "Cabinet E1",
        },
        {
            "equipment_name": "Electric Water Bath 6-hole",
            "equipment_code": "EQP-023",
            "description": "Stainless steel electric water bath, 6 holes, RT to 100 °C.",
            "total_quantity": 6,
            "available_quantity": 6,
            "unit_price_per_day": "150.00",
            "condition": "GOOD",
            "storage_location": "Cabinet E2",
        },
        {
            "equipment_name": "Crucible with Lid (30 ml)",
            "equipment_code": "EQP-024",
            "description": "Porcelain crucible with lid, 30 ml, heat-resistant to 1200 °C.",
            "total_quantity": 30,
            "available_quantity": 30,
            "unit_price_per_day": "50.00",
            "condition": "GOOD",
            "storage_location": "Drawer E2",
        },
        {
            "equipment_name": "Wire Gauze with Ceramic Centre",
            "equipment_code": "EQP-025",
            "description": "150 × 150 mm wire gauze with ceramic centre for even heat distribution.",
            "total_quantity": 30,
            "available_quantity": 30,
            "unit_price_per_day": "10.00",
            "condition": "GOOD",
            "storage_location": "Drawer E3",
        },
    ],
    "Safety Equipment": [
        {
            "equipment_name": "Safety Goggles",
            "equipment_code": "EQP-026",
            "description": "Indirect-vent chemical splash goggles, anti-fog, adjustable strap.",
            "total_quantity": 60,
            "available_quantity": 60,
            "unit_price_per_day": "30.00",
            "condition": "GOOD",
            "storage_location": "Cabinet F1",
        },
        {
            "equipment_name": "Lab Coat Medium",
            "equipment_code": "EQP-027",
            "description": "White cotton/polyester lab coat, size Medium, front-button closure.",
            "total_quantity": 40,
            "available_quantity": 40,
            "unit_price_per_day": "50.00",
            "condition": "GOOD",
            "storage_location": "Cabinet F1",
        },
        {
            "equipment_name": "Lab Coat Large",
            "equipment_code": "EQP-028",
            "description": "White cotton/polyester lab coat, size Large, front-button closure.",
            "total_quantity": 30,
            "available_quantity": 30,
            "unit_price_per_day": "50.00",
            "condition": "GOOD",
            "storage_location": "Cabinet F1",
        },
        {
            "equipment_name": "Chemical Resistant Gloves (pair)",
            "equipment_code": "EQP-029",
            "description": "Nitrile chemical-resistant gloves, 0.4 mm thickness — pair.",
            "total_quantity": 80,
            "available_quantity": 80,
            "unit_price_per_day": "30.00",
            "condition": "NEW",
            "storage_location": "Cabinet F2",
        },
        {
            "equipment_name": "Fire Extinguisher 1 kg CO₂",
            "equipment_code": "EQP-030",
            "description": "Portable 1 kg CO₂ fire extinguisher, suitable for class B/C fires.",
            "total_quantity": 5,
            "available_quantity": 5,
            "unit_price_per_day": "60.00",
            "condition": "GOOD",
            "storage_location": "Cabinet F2",
        },
    ],
}

# Transport zones — distance-based delivery fees from the central lab in Kiganjo.
TRANSPORT_ZONES = [
    {
        "zone_name": "Kiganjo",
        "description": (
            "Local zone covering Kiganjo and immediate surroundings "
            "in Thika West, Kiambu County. No transport charge."
        ),
        "base_transport_fee": "0.00",
    },
    {
        "zone_name": "Thika Town",
        "description": "Thika Town centre and its immediate environs (~8 km from Kiganjo).",
        "base_transport_fee": "500.00",
    },
    {
        "zone_name": "Juja",
        "description": "Juja constituency including Juja Farm and JKUAT area (~20 km).",
        "base_transport_fee": "1000.00",
    },
    {
        "zone_name": "Ruiru",
        "description": "Ruiru town and surrounding estates in Kiambu County (~28 km).",
        "base_transport_fee": "1300.00",
    },
    {
        "zone_name": "Githunguri",
        "description": "Githunguri constituency and surrounding dairy belt (~35 km).",
        "base_transport_fee": "1500.00",
    },
    {
        "zone_name": "Kiambu Town",
        "description": "Kiambu Town and neighbouring wards in Kiambu constituency (~40 km).",
        "base_transport_fee": "1800.00",
    },
    {
        "zone_name": "Limuru",
        "description": "Limuru and the wider tea belt in south-western Kiambu (~48 km).",
        "base_transport_fee": "2200.00",
    },
    {
        "zone_name": "Nairobi CBD",
        "description": "Nairobi Central Business District and inner Nairobi suburbs (~55 km).",
        "base_transport_fee": "2800.00",
    },
]

# Pricing rules applied to every category.
# (min_days, max_days, discount_percentage)
PRICING_TIERS = [
    (1, 3, "0.00"),
    (4, 7, "5.00"),
    (8, 14, "10.00"),
    (15, 30, "15.00"),
]

# School accounts to create.
SCHOOLS = [
    {
        "email": "alpha.high@school.labsynch.co.ke",
        "password": "LabSynch@2025!",
        "full_name": "Alpha High School Administrator",
        "phone_number": "+254711000001",
        "school_name": "Alpha High School Kiganjo",
        "registration_number": "KE/SCHOOLS/2001/0141",
        "physical_address": "Kiganjo, Thika West, Kiambu County",
        "town": "Kiganjo",
        "county": "Kiambu",
        "zone_name": "Kiganjo",
        "contact_person": "James Mwangi",
        "contact_designation": "Head of Science Department",
        "credit_limit": "50000.00",
    },
    {
        "email": "thika.boys@school.labsynch.co.ke",
        "password": "LabSynch@2025!",
        "full_name": "Thika Boys Administrator",
        "phone_number": "+254711000002",
        "school_name": "Thika Boys High School",
        "registration_number": "KE/SCHOOLS/1998/0089",
        "physical_address": "Thika Town, Kiambu County",
        "town": "Thika",
        "county": "Kiambu",
        "zone_name": "Thika Town",
        "contact_person": "Peter Kamau",
        "contact_designation": "Principal",
        "credit_limit": "75000.00",
    },
    {
        "email": "double.impact@school.labsynch.co.ke",
        "password": "LabSynch@2025!",
        "full_name": "Double Impact Secondary Administrator",
        "phone_number": "+254711000003",
        "school_name": "Double Impact Secondary School",
        "registration_number": "KE/SCHOOLS/2005/0257",
        "physical_address": "Kiganjo, Thika West, Kiambu County",
        "town": "Kiganjo",
        "county": "Kiambu",
        "zone_name": "Kiganjo",
        "contact_person": "Grace Wanjiku",
        "contact_designation": "Deputy Principal",
        "credit_limit": "40000.00",
    },
    {
        "email": "kiganjo.secondary@school.labsynch.co.ke",
        "password": "LabSynch@2025!",
        "full_name": "Kiganjo Secondary School Administrator",
        "phone_number": "+254711000004",
        "school_name": "Kiganjo Secondary School",
        "registration_number": "KE/SCHOOLS/1995/0062",
        "physical_address": "Kiganjo, Thika West, Kiambu County",
        "town": "Kiganjo",
        "county": "Kiambu",
        "zone_name": "Kiganjo",
        "contact_person": "Samuel Njoroge",
        "contact_designation": "Head of Science Department",
        "credit_limit": "45000.00",
    },
]


class Command(BaseCommand):
    help = (
        "Seeds the database with equipment categories, equipment items, "
        "pricing rules, and school accounts for development and demo use."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing seed records before inserting (does NOT touch admin users).",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self._clear_seed_data()

        with transaction.atomic():
            category_map = self._seed_categories()
            self._seed_equipment(category_map)
            self._seed_pricing_rules(category_map)
            zone_map = self._seed_transport_zones()
            self._seed_schools(zone_map)

        self.stdout.write(self.style.SUCCESS("\nSeed complete."))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _clear_seed_data(self):
        self.stdout.write("Clearing existing seed data …")
        codes = [item["equipment_code"] for items in EQUIPMENT.values() for item in items]
        deleted_eq, _ = Equipment.objects.filter(equipment_code__in=codes).delete()
        self.stdout.write(f"  Deleted {deleted_eq} equipment item(s).")

        names = [c["category_name"] for c in CATEGORIES]
        deleted_cat, _ = EquipmentCategory.objects.filter(category_name__in=names).delete()
        self.stdout.write(f"  Deleted {deleted_cat} category/categories.")

        emails = [s["email"] for s in SCHOOLS]
        deleted_u, _ = User.objects.filter(email__in=emails).delete()
        self.stdout.write(f"  Deleted {deleted_u} school user(s).")

        zone_names = [z["zone_name"] for z in TRANSPORT_ZONES]
        deleted_z, _ = TransportZone.objects.filter(zone_name__in=zone_names).delete()
        self.stdout.write(f"  Deleted {deleted_z} transport zone(s).")

    def _seed_categories(self):
        self.stdout.write("\nSeeding equipment categories …")
        category_map = {}
        for data in CATEGORIES:
            category, created = EquipmentCategory.objects.get_or_create(
                category_name=data["category_name"],
                defaults={
                    "description": data["description"],
                    "display_order": data["display_order"],
                },
            )
            action = "created" if created else "exists "
            self.stdout.write(f"  [{action}] {category.category_name}")
            category_map[category.category_name] = category
        return category_map

    def _seed_equipment(self, category_map):
        self.stdout.write("\nSeeding equipment …")
        for cat_name, items in EQUIPMENT.items():
            category = category_map[cat_name]
            for data in items:
                equipment, created = Equipment.objects.get_or_create(
                    equipment_code=data["equipment_code"],
                    defaults={
                        "category": category,
                        "equipment_name": data["equipment_name"],
                        "description": data["description"],
                        "total_quantity": data["total_quantity"],
                        "available_quantity": data["available_quantity"],
                        "unit_price_per_day": data["unit_price_per_day"],
                        "condition": data["condition"],
                        "storage_location": data["storage_location"],
                        "is_active": True,
                    },
                )
                action = "created" if created else "exists "
                self.stdout.write(
                    f"  [{action}] {equipment.equipment_code}  {equipment.equipment_name}"
                )

    def _seed_pricing_rules(self, category_map):
        self.stdout.write("\nSeeding pricing rules …")
        today = date.today()
        for category in category_map.values():
            for min_days, max_days, discount in PRICING_TIERS:
                rule, created = PricingRule.objects.get_or_create(
                    category=category,
                    min_days=min_days,
                    max_days=max_days,
                    defaults={
                        "discount_percentage": discount,
                        "effective_from": today,
                        "effective_to": None,
                        "is_active": True,
                    },
                )
                if created:
                    self.stdout.write(
                        f"  [created] {category.category_name} | "
                        f"{min_days}–{max_days} days → {discount}% discount"
                    )

        self.stdout.write(
            f"  Pricing rules ready for {len(category_map)} categories."
        )

    def _seed_transport_zones(self):
        self.stdout.write("\nSeeding transport zones …")
        zone_map = {}
        for data in TRANSPORT_ZONES:
            zone, created = TransportZone.objects.get_or_create(
                zone_name=data["zone_name"],
                defaults={
                    "description": data["description"],
                    "base_transport_fee": data["base_transport_fee"],
                    "is_active": True,
                },
            )
            action = "created" if created else "exists "
            self.stdout.write(
                f"  [{action}] {zone.zone_name}  (KES {zone.base_transport_fee})"
            )
            zone_map[zone.zone_name] = zone
        return zone_map

    def _seed_schools(self, zone_map):
        self.stdout.write("\nSeeding school accounts …")
        for data in SCHOOLS:
            user, created = User.objects.get_or_create(
                email=data["email"],
                defaults={
                    "full_name": data["full_name"],
                    "phone_number": data["phone_number"],
                    "user_type": UserType.SCHOOL,
                    "is_verified": True,
                    "email_verified_at": timezone.now(),
                    "is_active": True,
                },
            )
            if created:
                user.set_password(data["password"])
                user.save(update_fields=["password"])

            profile, p_created = SchoolProfile.objects.get_or_create(
                user=user,
                defaults={
                    "school_name": data["school_name"],
                    "registration_number": data["registration_number"],
                    "physical_address": data["physical_address"],
                    "town": data.get("town", ""),
                    "county": data["county"],
                    "transport_zone": zone_map.get(data.get("zone_name")),
                    "contact_person": data["contact_person"],
                    "contact_designation": data["contact_designation"],
                    "credit_limit": data["credit_limit"],
                    "account_status": AccountStatus.ACTIVE,
                },
            )

            u_action = "created" if created else "exists "
            p_action = "created" if p_created else "exists "
            zone_label = data.get("zone_name", "—")
            self.stdout.write(
                f"  [user {u_action}] [profile {p_action}] "
                f"{data['school_name']}  ({data['email']})  zone: {zone_label}"
            )

        self.stdout.write(
            "\n  Default password for all school accounts: LabSynch@2025!"
        )
        self.stdout.write(
            "  IMPORTANT: Change passwords before using in production.\n"
        )
