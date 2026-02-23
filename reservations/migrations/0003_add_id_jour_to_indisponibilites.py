# Generated migration - Ajout du champ id_jour (ForeignKey vers Joueurs) dans Indisponibilites

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0002_recreate_indisponibilites_with_uuid'),
    ]

    operations = [
        migrations.AddField(
            model_name='indisponibilites',
            name='id_jour',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='indisponibilites',
                to='reservations.joueurs'
            ),
        ),
    ]
