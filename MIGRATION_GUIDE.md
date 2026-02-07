# 🗄️ Guide des Migrations Django vers MySQL Railway

## ⚠️ Important : Tables existantes vs Tables Django

Les tables que vous voyez dans MySQL Railway (`abonnement`, `client_abonne`, `indisponible`, `proprietaire`, etc.) **ne sont PAS** les tables Django. Ce sont probablement des tables de votre application Spring Boot.

Django créera ses **propres tables** avec le préfixe `reservations_` (nom de votre app Django).

## 📋 Tables que Django va créer

D'après vos modèles Django, voici les tables qui seront créées :

| Table Django | Modèle correspondant |
|--------------|---------------------|
| `reservations_client` | Client |
| `reservations_wilaye` | Wilaye |
| `reservations_moughataa` | Moughataa |
| `reservations_terrains` | Terrains |
| `reservations_joueurs` | Joueurs |
| `reservations_reservations` | Reservations |
| `reservations_indisponibilites` | Indisponibilites |
| `reservations_evaluation` | Evaluation |
| `reservations_academie` | Academie |
| `reservations_demandereservation` | DemandeReservation |
| `reservations_inscription` | Inscription |
| `reservations_reservationmanuel` | reservationmanuel |
| `reservations_periode` | Periode |
| `reservations_indisponibles_tous_temps` | Indisponibles_tous_temps |
| `reservations_versionclient` | VersionClient |
| `reservations_version` | Version |
| `django_migrations` | (table système Django) |
| `django_session` | (table système Django) |
| `django_content_type` | (table système Django) |
| `auth_*` | (tables système Django auth) |

## ✅ Les deux bases peuvent coexister

- **Tables Spring Boot** : `abonnement`, `proprietaire`, etc. (ne seront pas touchées)
- **Tables Django** : `reservations_*` (seront créées par les migrations)

## 🚀 Comment faire les migrations

### Méthode 1 : Automatique (déjà configuré)

Votre `Procfile` et `railway.json` sont déjà configurés pour exécuter les migrations automatiquement.

**Vérifiez dans les logs de déploiement** que vous voyez :
```
Running migrations...
Operations to perform:
  Apply all migrations: reservations
```

### Méthode 2 : Manuelle via Railway CLI

```bash
# 1. Installer Railway CLI
npm i -g @railway/cli

# 2. Se connecter
railway login

# 3. Lier le projet
railway link

# 4. Voir l'état des migrations
railway run python manage.py showmigrations

# 5. Appliquer les migrations
railway run python manage.py migrate
```

### Méthode 3 : Via l'interface Railway

1. Allez dans votre service **"Matchi_backend"**
2. Cliquez sur **"Settings"** → **"Deploy"**
3. Utilisez le terminal Railway (si disponible)
4. Exécutez : `python manage.py migrate`

## 🔍 Vérifier les migrations

### Voir l'état des migrations :
```bash
python manage.py showmigrations
```

### Voir quelles tables seront créées :
```bash
python manage.py migrate --plan
```

### Vérifier les tables dans MySQL Railway :

Après les migrations, dans l'onglet **"Database"** de MySQL, vous devriez voir :
- ✅ Les anciennes tables (Spring Boot) : `abonnement`, `proprietaire`, etc.
- ✅ Les nouvelles tables Django : `reservations_client`, `reservations_terrains`, etc.

## ⚠️ Points importants

1. **Pas de conflit** : Django ne touchera pas aux tables existantes
2. **Base de données partagée** : Les deux applications (Spring Boot et Django) peuvent utiliser la même base MySQL
3. **Préfixe** : Toutes les tables Django commencent par `reservations_`
4. **Variables MySQL** : Assurez-vous qu'elles sont configurées AVANT les migrations

## 📝 Checklist

- [ ] Variables MySQL configurées sur Railway ✅
- [ ] `pymysql` dans `requirements.txt` ✅
- [ ] `Procfile` avec `release: python manage.py migrate --noinput` ✅
- [ ] `railway.json` mis à jour ✅
- [ ] Migrations dans le repo ✅
- [ ] Prêt à déployer !

## 🎯 Après le déploiement

Vérifiez dans MySQL Railway que les nouvelles tables Django sont créées :
- `reservations_client`
- `reservations_terrains`
- `reservations_joueurs`
- etc.

Les anciennes tables Spring Boot resteront intactes.
