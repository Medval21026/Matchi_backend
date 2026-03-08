# Generated migration - Suppression du champ UUID de Indisponibles_tous_temps

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0005_add_kafka_sync_fields'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='indisponibles_tous_temps',
            name='uuid',
        ),
    ]
