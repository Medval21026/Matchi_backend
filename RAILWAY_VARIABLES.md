# 🔧 Configuration des Variables d'Environnement MySQL sur Railway

## 📋 Variables à configurer dans votre service Django "Matchi_backend"

### Étapes sur Railway :

1. **Allez dans votre service Django "Matchi_backend"**
2. **Cliquez sur l'onglet "Variables"**
3. **Ajoutez ces variables une par une :**

### Variables MySQL (valeurs à copier-coller) :

**1. MYSQLDATABASE**
```
cite
```

**2. MYSQLUSER**
```
root
```

**3. MYSQLPASSWORD**
```
lpQPTCliNnBaGBUFJsPMrJVFvFxyaCic
```

**4. MYSQLHOST** ⚠️ **À RÉCUPÉRER DEPUIS LE SERVICE MYSQL**
```
<voir instructions ci-dessous>
```

**5. MYSQLPORT**
```
3306
```

### 🔍 Comment récupérer MYSQLHOST ?

1. **Allez dans votre service MySQL** (pas Django)
2. **Cliquez sur l'onglet "Variables"**
3. **Cherchez la variable `MYSQLHOST`** ou `MYSQL_HOST`
4. **Copiez sa valeur** (elle ressemble à quelque chose comme `containers-us-west-xxx.railway.app` ou une IP)
5. **Collez-la dans les variables de votre service Django**

**OU** si Railway fournit `MYSQL_URL` ou `MYSQL_PUBLIC_URL` dans le service MySQL :
- Copiez cette URL complète
- Ajoutez-la comme variable `MYSQL_URL` dans votre service Django

### Variables Django supplémentaires (recommandées) :

```
DEBUG=False
```

```
SECRET_KEY=<générez une nouvelle clé secrète>
```

Pour générer une SECRET_KEY :
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

```
ALLOWED_HOSTS=*.railway.app
```

## ✅ Vérification

Après avoir ajouté toutes les variables :
1. Redéployez votre service (Railway le fera automatiquement)
2. Vérifiez les logs de déploiement
3. Si tout est OK, votre application devrait démarrer correctement

## ⚠️ Important

- Ne commitez JAMAIS les mots de passe dans le code
- Utilisez toujours les variables d'environnement Railway
- Le fichier `.env` est déjà dans `.gitignore`
