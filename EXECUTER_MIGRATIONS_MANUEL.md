# Exécuter les migrations manuellement sur Railway

## Problème
Les migrations ne s'exécutent pas automatiquement. La base de données `cite` n'existe pas ou est vide.

## Solution : Exécuter les migrations manuellement

### Étape 1 : Créer la base de données `cite` sur Railway MySQL-9TbY

1. Allez sur Railway → MySQL-9TbY → Database
2. Cliquez sur **"Connect"** (bouton en haut à droite)
3. Dans le terminal qui s'ouvre, exécutez :

```sql
CREATE DATABASE IF NOT EXISTS cite CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

4. Vérifiez que la base existe :
```sql
SHOW DATABASES;
```

### Étape 2 : Exécuter les migrations via Railway CLI

**Option A : Via Railway CLI (recommandé)**

```powershell
# Se connecter au service Matchi_backend
railway link

# Exécuter les migrations
railway run python manage.py migrate
```

**Option B : Via l'interface Railway**

1. Allez sur Railway → Matchi_backend → Deployments
2. Cliquez sur le dernier déploiement
3. Cliquez sur "View Logs"
4. Cherchez les erreurs de migration

**Option C : Via le terminal Railway (Connect)**

1. Allez sur Railway → Matchi_backend → Settings
2. Cliquez sur "Connect" (terminal)
3. Exécutez :
```bash
python manage.py migrate
```

### Étape 3 : Vérifier que les migrations sont appliquées

```bash
python manage.py showmigrations
```

Vous devriez voir toutes les migrations avec `[X]` (appliquées).

### Étape 4 : Vérifier les tables dans MySQL-9TbY

1. Allez sur Railway → MySQL-9TbY → Database → Data
2. Vous devriez voir les tables Django créées :
   - `django_migrations`
   - `reservations_client`
   - `reservations_terrains`
   - etc.

## Si les migrations échouent

### Erreur : "Unknown database 'cite'"

**Solution** : Créez la base de données (Étape 1)

### Erreur : "Access denied"

**Solution** : Vérifiez les variables d'environnement sur Railway :
- `MYSQLHOST` doit être `mysql-9tby.railway.internal`
- `MYSQLDATABASE` doit être `cite`
- `MYSQLUSER` et `MYSQLPASSWORD` doivent correspondre aux credentials Railway

### Erreur : "Table already exists"

**Solution** : Les migrations ont peut-être été partiellement appliquées. Exécutez :
```bash
python manage.py migrate --fake-initial
```

## Vérifier les variables d'environnement Railway

```powershell
railway variables
```

Assurez-vous que :
- `MYSQLHOST=mysql-9tby.railway.internal`
- `MYSQLDATABASE=cite`
- `MYSQLUSER=root`
- `MYSQLPASSWORD=<votre_mot_de_passe>`
- `MYSQLPORT=3306`
