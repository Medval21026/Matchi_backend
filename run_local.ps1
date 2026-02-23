# Script pour lancer le serveur Django localement
Write-Host "Activation de l'environnement virtuel..." -ForegroundColor Green
& .\venv\Scripts\Activate.ps1

Write-Host "Vérification des dépendances..." -ForegroundColor Green
python -m pip install --quiet -r requirements.txt

Write-Host "Démarrage du serveur Django..." -ForegroundColor Green
python manage.py runserver
