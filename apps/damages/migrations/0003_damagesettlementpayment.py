import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("damages", "0002_damagereport_amount_paid_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="DamageSettlementPayment",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("transaction_ref", models.CharField(db_index=True, max_length=50, unique=True)),
                ("amount_paid", models.DecimalField(decimal_places=2, max_digits=12)),
                ("mpesa_phone_number", models.CharField(blank=True, max_length=20, null=True)),
                ("mpesa_transaction_id", models.CharField(blank=True, max_length=50, null=True, unique=True)),
                ("mpesa_checkout_request_id", models.CharField(blank=True, max_length=100, null=True, unique=True)),
                (
                    "payment_status",
                    models.CharField(
                        choices=[("PENDING", "Pending"), ("SUCCESS", "Success"), ("FAILED", "Failed")],
                        default="PENDING",
                        max_length=20,
                    ),
                ),
                ("initiated_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("callback_response", models.JSONField(blank=True, null=True)),
                (
                    "damage_report",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="settlement_payments",
                        to="damages.damagereport",
                    ),
                ),
            ],
            options={
                "verbose_name": "Damage Settlement Payment",
                "verbose_name_plural": "Damage Settlement Payments",
                "ordering": ["-initiated_at"],
            },
        ),
    ]
