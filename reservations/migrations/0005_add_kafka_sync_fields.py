# Generated migration - Ajout des champs kafka_synced et last_kafka_sync_attempt pour Indisponibilites uniquement

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0004_client_langue_joueurs_langue'),
    ]

    operations = [
        migrations.AddField(
            model_name='indisponibilites',
            name='kafka_synced',
            field=models.BooleanField(db_index=True, default=False, help_text="Indique si l'indisponibilité a été synchronisée avec Kafka"),
        ),
        migrations.AddField(
            model_name='indisponibilites',
            name='last_kafka_sync_attempt',
            field=models.DateTimeField(blank=True, help_text="Dernière tentative de synchronisation Kafka", null=True),
        ),
    ]
