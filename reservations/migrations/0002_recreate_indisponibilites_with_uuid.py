# Generated manually - Recréation de la table Indisponibilites avec UUID

import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0001_initial'),
    ]

    operations = [
        # Supprimer l'ancienne table si elle existe (gestion d'erreur silencieuse)
        migrations.RunSQL(
            """
            SET @exist := (SELECT COUNT(*) FROM information_schema.tables 
                          WHERE table_schema = DATABASE() 
                          AND table_name = 'reservations_indisponibilites');
            SET @sqlstmt := IF(@exist > 0, 'DROP TABLE reservations_indisponibilites', 'SELECT 1');
            PREPARE stmt FROM @sqlstmt;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            """
            SET @exist := (SELECT COUNT(*) FROM information_schema.tables 
                          WHERE table_schema = DATABASE() 
                          AND table_name = 'reservations_indisponibles_tous_temps');
            SET @sqlstmt := IF(@exist > 0, 'DROP TABLE reservations_indisponibles_tous_temps', 'SELECT 1');
            PREPARE stmt FROM @sqlstmt;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        # Recréer Indisponibilites avec UUID
        migrations.CreateModel(
            name='Indisponibilites',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)),
                ('date_indisponibilite', models.DateField()),
                ('heure_debut', models.TimeField()),
                ('heure_fin', models.TimeField()),
                ('terrain', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='reservations.terrains')),
            ],
            options={
                'unique_together': {('terrain', 'date_indisponibilite', 'heure_debut', 'heure_fin')},
            },
        ),
        # Recréer Indisponibles_tous_temps avec UUID
        migrations.CreateModel(
            name='Indisponibles_tous_temps',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)),
                ('heure_debut', models.TimeField()),
                ('heure_fin', models.TimeField()),
                ('terrain', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='heures_indisponibles', to='reservations.terrains')),
            ],
            options={
                'unique_together': {('terrain', 'heure_debut', 'heure_fin')},
            },
        ),
    ]
