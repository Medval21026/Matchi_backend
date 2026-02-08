# Diagnostic du problème de base de données

## Problème identifié

Les migrations s'exécutent avec succès (26 tables créées), mais l'interface Railway montre "You have no tables".

### Cause probable

Le problème vient de `MYSQL_URL` qui écrase `MYSQLDATABASE=cite`. 

Sur Railway, quand vous connectez un service MySQL, Railway crée automatiquement une variable `MYSQL_URL` qui pointe vers la base de données **par défaut** (souvent "railway" au lieu de "cite").

Le code dans `settings.py` utilise `MYSQL_URL` s'il est défini, ce qui peut écraser `MYSQLDATABASE=cite`.

## Solution appliquée

J'ai modifié `settings.py` pour **forcer l'utilisation de `MYSQLDATABASE=cite`** même si `MYSQL_URL` est défini.

## Vérification sur Railway

### 1. Vérifier les variables d'environnement

Allez sur Railway → Matchi_backend → Variables

Assurez-vous que :
- `MYSQLDATABASE=cite` ✅ (déjà configuré)
- `MYSQLHOST=mysql-9tby.railway.internal`
- `MYSQLUSER=root`
- `MYSQLPASSWORD=<votre_mot_de_passe>`
- `MYSQLPORT=3306`

### 2. Vérifier MYSQL_URL

Si `MYSQL_URL` est défini, vérifiez quelle base de données il contient :
- Si c'est `mysql://...@...:3306/railway` → C'est le problème !
- La base devrait être `cite`

### 3. Options de correction

**Option A : Supprimer ou modifier MYSQL_URL (recommandé)**

1. Allez sur Railway → Matchi_backend → Variables
2. Trouvez `MYSQL_URL` ou `MYSQL_PUBLIC_URL`
3. Soit supprimez-la, soit modifiez-la pour pointer vers `cite`

**Option B : Forcer MYSQLDATABASE (déjà fait dans le code)**

Le code a été modifié pour forcer `cite` même si `MYSQL_URL` est défini.

## Vérification après déploiement

Après le prochain déploiement, les logs devraient montrer :

```
🔧 Étape 4 : Vérification de la base de données Django...
   📊 Configuration Django réelle:
      Database: cite          ← Doit être 'cite', pas 'railway'
      Host: mysql-9tby.railway.internal
      User: root
      Port: 3306

🔧 Étape 5 : Liste des tables créées...
   📊 Base de données actuelle: cite    ← Doit être 'cite'
   ✅ 26 table(s) trouvée(s):
      - reservations_client
      - reservations_terrains
      ...
```

## Si le problème persiste

1. **Vérifiez quelle base de données est réellement utilisée** :
   - Les logs afficheront maintenant la base de données réelle
   - Si c'est "railway" au lieu de "cite", le problème est confirmé

2. **Créez la base 'cite' manuellement** :
   - Allez sur Railway → MySQL-9TbY → Database → Connect
   - Exécutez :
   ```sql
   CREATE DATABASE IF NOT EXISTS cite CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   USE cite;
   SHOW TABLES;
   ```

3. **Vérifiez dans l'interface Railway** :
   - Allez sur Railway → MySQL-9TbY → Database → Data
   - **Changez la base de données** dans le sélecteur en haut (si disponible)
   - Sélectionnez "cite" au lieu de "railway" ou la base par défaut

## Note importante

L'interface Railway peut afficher une base de données par défaut. Assurez-vous de **sélectionner la base 'cite'** dans l'interface si un sélecteur est disponible.
