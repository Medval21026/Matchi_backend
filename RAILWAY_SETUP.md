# Configuration Django avec MySQL sur Railway

## 📋 Étapes pour connecter votre backend Django au MySQL Railway

### 1. **Récupérer les variables d'environnement depuis Railway**

Dans votre dashboard Railway (comme sur les images) :

1. Allez dans votre projet **"refreshing-dream"**
2. Cliquez sur le service **MySQL**
3. Allez dans l'onglet **"Variables"**
4. Vous verrez les variables suivantes :
   - `MYSQL_DATABASE` ou `MYSQLDATABASE`
   - `MYSQL_ROOT_PASSWORD` ou `MYSQLPASSWORD`
   - `MYSQLHOST`
   - `MYSQLPORT`
   - `MYSQLUSER`
   - `MYSQL_URL` ou `MYSQL_PUBLIC_URL` (si disponible)

### 2. **Option A : Utiliser MYSQL_URL (Recommandé)**

Si Railway fournit `MYSQL_URL` ou `MYSQL_PUBLIC_URL`, c'est la méthode la plus simple :

```bash
# Dans votre terminal local (pour test)
export MYSQL_URL="mysql://user:password@host:port/database"

# Ou créez un fichier .env
echo "MYSQL_URL=mysql://user:password@host:port/database" > .env
```

### 3. **Option B : Utiliser les variables individuelles**

Créez un fichier `.env` à la racine du projet :

```env
MYSQLDATABASE=cite
MYSQLUSER=root
MYSQLPASSWORD=votre_mot_de_passe_railway
MYSQLHOST=host_railway
MYSQLPORT=3306
```

**Important :** Remplacez les valeurs par celles de votre Railway MySQL.

### 4. **Installer python-dotenv (pour charger le .env)**

```bash
pip install python-dotenv
```

Puis ajoutez dans `settings.py` au début (après les imports) :

```python
from dotenv import load_dotenv
load_dotenv()
```

### 5. **Tester la connexion**

```bash
python manage.py migrate
python manage.py runserver
```

Si tout fonctionne, vous verrez les migrations s'exécuter et le serveur démarrer.

## 🚀 Pour déployer sur Railway

### Créer un nouveau service Django sur Railway

1. Dans Railway, cliquez sur **"Create"** (le bouton +)
2. Sélectionnez **"New Service"**
3. Choisissez **"GitHub Repo"** ou **"Empty Project"**
4. Configurez les variables d'environnement :
   - Railway détectera automatiquement les variables du service MySQL
   - Vous pouvez les référencer dans votre service Django

### Variables d'environnement à configurer dans Railway

Dans votre service Django sur Railway, ajoutez ces variables (elles seront automatiquement disponibles si MySQL est dans le même projet) :

- `MYSQLDATABASE` → Référence au service MySQL
- `MYSQLUSER` → Référence au service MySQL  
- `MYSQLPASSWORD` → Référence au service MySQL
- `MYSQLHOST` → Référence au service MySQL
- `MYSQLPORT` → Référence au service MySQL

Railway peut aussi fournir `MYSQL_URL` automatiquement.

## ⚠️ Notes importantes

1. **Sécurité** : Ne commitez jamais le fichier `.env` (il est déjà dans `.gitignore`)
2. **Production** : Utilisez les variables d'environnement Railway directement
3. **Local** : Utilisez le fichier `.env` pour le développement local

## 🔍 Vérification

Pour vérifier que la connexion fonctionne :

```python
python manage.py shell
>>> from django.db import connection
>>> connection.ensure_connection()
>>> print("✅ Connexion réussie !")
```
