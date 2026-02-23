import requests

BASE_URL = "http://localhost:8081/api/proprietaires"
HEADERS = {"Content-Type": "application/json"}

def get_all_proprietaires():
    response = requests.get(BASE_URL, headers=HEADERS, timeout=10)
    if response.status_code == 200:
        return response.json()  # liste des dictionnaires
    return []

def get_proprietaire_by_id(proprietaire_id):
    response = requests.get(f"{BASE_URL}/{proprietaire_id}", headers=HEADERS, timeout=10)
    if response.status_code == 200:
        return response.json()
    return None

def create_proprietaire(data):
    response = requests.post(BASE_URL, json=data, headers=HEADERS, timeout=10)
    if response.status_code == 200:
        return response.json()
    else:
        # Essayer de récupérer le message d'erreur de la réponse
        try:
            error_data = response.json()
            error_message = error_data.get('message', error_data.get('error', 'Erreur lors de la création du propriétaire'))
        except:
            error_message = f'Erreur {response.status_code}: {response.text}'
        raise Exception(error_message)

def update_proprietaire(proprietaire_id, data):
    response = requests.put(f"{BASE_URL}/{proprietaire_id}", json=data, headers=HEADERS, timeout=10)
    if response.status_code == 200:
        return response.json()
    else:
        # Essayer de récupérer le message d'erreur de la réponse
        try:
            error_data = response.json()
            error_message = error_data.get('message', error_data.get('error', 'Erreur lors de la mise à jour du propriétaire'))
        except:
            error_message = f'Erreur {response.status_code}: {response.text}'
        raise Exception(error_message)

def delete_proprietaire(proprietaire_id):
    response = requests.delete(f"{BASE_URL}/{proprietaire_id}", headers=HEADERS, timeout=10)
    if response.status_code == 204:
        return True
    else:
        # Essayer de récupérer le message d'erreur de la réponse
        try:
            error_data = response.json()
            error_message = error_data.get('message', error_data.get('error', 'Erreur lors de la suppression du propriétaire'))
        except:
            error_message = f'Erreur {response.status_code}: {response.text}'
        raise Exception(error_message)
