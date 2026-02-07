# 🚀 Exécuter les Migrations via Railway CLI

## ⚠️ Important

Le nom d'hôte `mysql.railway.internal` fonctionne **uniquement** depuis les services Railway, pas depuis votre machine locale.

## ✅ Solution : Utiliser Railway CLI

### 1. Installer Railway CLI

```bash
npm i -g @railway/cli
```

### 2. Se connecter à Railway

```bash
railway login
```

### 3. Lier votre projet

```bash
cd C:\Users\HP\Desktop\matchi_web_admin
railway link
```

Sélectionnez :
- Projet : `refreshing-dream`
- Service : `Matchi_backend`

### 4. Exécuter les migrations

```bash
railway run python manage.py migrate
```

### 5. Vérifier les migrations

```bash
railway run python manage.py showmigrations
```

## 🔍 Alternative : Utiliser l'URL publique MySQL

Si Railway fournit une URL publique pour MySQL, vous pouvez l'utiliser dans `.env` :

```env
MYSQLHOST=<host_public_railway>
```

Pour trouver l'URL publique :
1. Allez dans votre service MySQL sur Railway
2. Onglet "Settings" → "Networking"
3. Cherchez l'URL publique ou le host public

## 📝 Note

Le fichier `.env` que nous avons créé sera utilisé **uniquement sur Railway** (via les variables d'environnement). Pour les migrations locales, utilisez Railway CLI.
