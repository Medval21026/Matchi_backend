# Configuration Cloudflare R2 — Matchi Backend

## Objectif
Stocker toutes les images (terrains, joueurs, académies) sur Cloudflare R2 au lieu du serveur local.
Les URLs des images sont sauvegardées automatiquement en base de données MySQL.

---

## Étapes réalisées

### 1. Installation des packages

```bash
source venv/bin/activate
pip install "django-storages[s3]" boto3
```

Ajouté dans `requirements.txt` :
```
django-storages==1.14.6
boto3==1.42.64
```

---

### 2. Modification de `settings.py`

Ajout du bloc Cloudflare R2 en haut du fichier :

```python
CLOUDFLARE_ACCOUNT_ID = os.getenv('CLOUDFLARE_ACCOUNT_ID', '')
R2_ACCESS_KEY_ID      = os.getenv('R2_ACCESS_KEY_ID', '')
R2_SECRET_ACCESS_KEY  = os.getenv('R2_SECRET_ACCESS_KEY', '')
R2_BUCKET_NAME        = os.getenv('R2_BUCKET_NAME', 'images')
R2_PUBLIC_URL         = os.getenv('R2_PUBLIC_URL', '')

USE_R2 = all([CLOUDFLARE_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_PUBLIC_URL])

if USE_R2:
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
            "OPTIONS": {
                "access_key": R2_ACCESS_KEY_ID,
                "secret_key": R2_SECRET_ACCESS_KEY,
                "bucket_name": R2_BUCKET_NAME,
                "endpoint_url": f"https://{CLOUDFLARE_ACCOUNT_ID}.r2.cloudflarestorage.com",
                "custom_domain": R2_PUBLIC_URL.replace("https://", ""),
                "file_overwrite": False,
                "default_acl": None,
                "querystring_auth": False,
            },
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
    MEDIA_URL = f"{R2_PUBLIC_URL}/"
    MEDIA_ROOT = ""
else:
    # Fallback local (dev sans credentials R2)
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

Ajout de `storages` dans `INSTALLED_APPS` :
```python
INSTALLED_APPS = [
    ...
    'storages',
]
```

---

### 3. Création du fichier `.env`

Fichier `.env` à la racine du projet avec les variables R2 :

```env
CLOUDFLARE_ACCOUNT_ID=your_account_id_here
R2_ACCESS_KEY_ID=your_access_key_id_here
R2_SECRET_ACCESS_KEY=your_secret_access_key_here
R2_BUCKET_NAME=images
R2_PUBLIC_URL=https://pub-xxxxxxx.r2.dev
```

---

## Étape suivante — Remplir les credentials

### Comment obtenir les credentials Cloudflare R2 :

1. **Account ID** → Dashboard Cloudflare → sidebar droite
2. **Access Key ID + Secret Access Key** :
   - Cloudflare Dashboard → R2 → **Manage R2 API Tokens**
   - Cliquer **Create API Token**
   - Permissions : `Object Read & Write` sur le bucket `images`
3. **Public URL** :
   - R2 → bucket `images` → **Settings** → **Public Access**
   - Activer l'accès public
   - Copier l'URL du type `https://pub-xxxxxxx.r2.dev`

---

## Modèles concernés

| Modèle | Champ image | Upload path |
|--------|-------------|-------------|
| `Terrains` | `photo1`, `photo2`, `photo3` | `images/` |
| `Joueurs` | `photo_de_profile` | `images/` |
| `Academie` | `photo` | `images/` |

**Aucune migration de base de données nécessaire** — le type de colonne `ImageField` reste inchangé, seul le backend de stockage change.

---

## Flow de fonctionnement

```
Mobile/Client
     │ envoie l'image (multipart/form-data)
     ▼
Django Server (reçoit en mémoire temporaire)
     │
     │ django-storages intercepte
     │ boto3 upload vers Cloudflare R2
     ▼
Cloudflare R2 Bucket "images"
     │
     │ URL publique générée automatiquement
     ▼
Base de données MySQL
     │ stocke : "images/nom_du_fichier.jpg"
     │ URL complète reconstituée : R2_PUBLIC_URL + "images/nom_du_fichier.jpg"
```

---

## Test de la connexion R2

Une fois les credentials remplis dans `.env`, tester avec :

```bash
source venv/bin/activate
python manage.py shell
```

```python
from django.core.files.storage import default_storage
print(default_storage.bucket_name)  # doit afficher : images
print(default_storage.endpoint_url) # doit afficher l'endpoint R2
```
