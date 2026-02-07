# 🚀 Guide de Déploiement Django sur Railway

## ✅ Fichiers créés pour Railway

1. **`Procfile`** - Commande de démarrage avec Gunicorn
2. **`railway.json`** - Configuration Railway
3. **`runtime.txt`** - Version Python
4. **`requirements.txt`** - Mis à jour avec `gunicorn` et `python-dotenv`

## 📋 Étapes de déploiement

### 1. **Vérifier les fichiers**

Assurez-vous que ces fichiers sont dans votre repo :
- ✅ `Procfile`
- ✅ `railway.json`
- ✅ `runtime.txt`
- ✅ `requirements.txt` (avec gunicorn et python-dotenv)
- ✅ `manage.py`
- ✅ `reservation_cite/settings.py`

### 2. **Configurer les variables d'environnement sur Railway**

Dans votre service **Matchi_backend** sur Railway :

1. Allez dans l'onglet **"Variables"**
2. Ajoutez ces variables :

#### Variables de base de données MySQL
```
MYSQLDATABASE=cite
MYSQLUSER=root
MYSQLPASSWORD=<votre_mot_de_passe_mysql>
MYSQLHOST=<host_mysql_railway>
MYSQLPORT=3306
```

**OU** si Railway fournit `MYSQL_URL` :
```
MYSQL_URL=mysql://user:password@host:port/database
```

#### Variables Django
```
DEBUG=False
SECRET_KEY=<générez_une_nouvelle_clé_secrète>
ALLOWED_HOSTS=*.railway.app,votre-domaine.com
```

#### Variables optionnelles
```
DJANGO_SETTINGS_MODULE=reservation_cite.settings
PORT=8000
```

### 3. **Générer une nouvelle SECRET_KEY**

```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Ajoutez cette clé dans les variables d'environnement Railway.

### 4. **Configurer les migrations**

Railway exécutera automatiquement les migrations si vous ajoutez dans `railway.json` :

```json
{
  "deploy": {
    "startCommand": "python manage.py migrate && gunicorn reservation_cite.wsgi:application --bind 0.0.0.0:$PORT"
  }
}
```

**OU** créez un script `build.sh` :

```bash
#!/bin/bash
python manage.py collectstatic --noinput
python manage.py migrate
```

### 5. **Configurer les fichiers statiques**

Dans `settings.py`, ajoutez :

```python
# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

### 6. **Redéployer**

1. Commitez tous les fichiers :
   ```bash
   git add .
   git commit -m "Configure Railway deployment"
   git push
   ```

2. Railway détectera automatiquement le push et redéploiera

## 🔧 Résolution des problèmes

### Erreur "Error creating build plan with Railpack"

✅ **Résolu** avec les fichiers :
- `Procfile`
- `railway.json`
- `runtime.txt`

### Erreur de connexion MySQL

Vérifiez que :
- Les variables d'environnement MySQL sont correctement configurées
- Le service MySQL est démarré sur Railway
- Le service Django est dans le même projet que MySQL

### Erreur "Module not found"

Vérifiez que `requirements.txt` contient toutes les dépendances nécessaires.

## 📝 Notes importantes

1. **SECRET_KEY** : Ne jamais commiter la clé secrète, utilisez les variables d'environnement
2. **DEBUG** : Toujours mettre `False` en production
3. **ALLOWED_HOSTS** : Inclure le domaine Railway (`*.railway.app`)
4. **Migrations** : S'exécutent automatiquement au démarrage si configuré

## 🎯 Prochaines étapes

1. ✅ Commitez les fichiers de configuration
2. ✅ Configurez les variables d'environnement sur Railway
3. ✅ Redéployez
4. ✅ Vérifiez les logs si erreur
