from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vending', '0018_masteritem_add_maximum_heating'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='qr_used',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='order',
            name='fulfillment_attempts',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[
                    ('DRAFT', 'Draft'),
                    ('PENDING', 'Pending'),
                    ('CONFIRMED', 'Confirmed'),
                    ('PREPARING', 'Preparing'),
                    ('READY', 'Ready'),
                    ('COMPLETED', 'Completed'),
                    ('CANCELLED', 'Cancelled'),
                    ('PENDING_FULFILLMENT', 'Pending Fulfillment'),
                ],
                default='DRAFT',
                max_length=30,
            ),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='status',
            field=models.CharField(
                blank=True,
                choices=[
                    ('DRAFT', 'Draft'),
                    ('PENDING', 'Pending'),
                    ('CONFIRMED', 'Confirmed'),
                    ('PREPARING', 'Preparing'),
                    ('READY', 'Ready'),
                    ('COMPLETED', 'Completed'),
                    ('CANCELLED', 'Cancelled'),
                    ('PENDING_FULFILLMENT', 'Pending Fulfillment'),
                ],
                default='PENDING',
                max_length=30,
                null=True,
            ),
        ),
    ]
