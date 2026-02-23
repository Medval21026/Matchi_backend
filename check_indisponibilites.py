"""
Script pour vérifier les indisponibilités créées dans Django
"""
import sys
import os
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reservation_cite.settings')
django.setup()

from reservations.models import Indisponibilites

print("=" * 60)
print("VERIFICATION DES INDISPONIBILITES DANS DJANGO")
print("=" * 60)

count = Indisponibilites.objects.count()
print(f"\nNombre total d'indisponibilites: {count}")

if count > 0:
    print("\nDernieres indisponibilites:")
    for ind in Indisponibilites.objects.all()[:10]:
        print(f"  - UUID: {ind.uuid}")
        print(f"    Terrain ID: {ind.terrain.id}")
        print(f"    Date: {ind.date_indisponibilite}")
        print(f"    Heure: {ind.heure_debut} - {ind.heure_fin}")
        print()
else:
    print("\nAucune indisponibilite trouvee dans Django.")
    print("Le consumer consomme les messages mais peut-etre qu'ils sont tous ignores (source=django)")

print("=" * 60)
