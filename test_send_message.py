import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reservation_cite.settings')
django.setup()

from reservations.mobile import send_message_to_all_joueurs
from django.test import RequestFactory
import json

# Créer une requête de test
factory = RequestFactory()
request = factory.post(
    '/send-message-to-all-joueurs/',
    data=json.dumps({'titre': 'Test', 'message': 'Test message'}),
    content_type='application/json'
)

# Tester la fonction
try:
    response = send_message_to_all_joueurs(request)
    print("✅ Succès! Status:", response.status_code)
    print("Contenu:", response.content.decode())
except Exception as e:
    print("❌ Erreur:", type(e).__name__)
    print("Message:", str(e))
    import traceback
    traceback.print_exc()
