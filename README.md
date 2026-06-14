# PPG

Ce projet contient le backend Django et le frontend statique pour l'application ORIO.

## Structure du projet

- `PPG_backend/` : backend Django
- `PPG_front/` : frontend statique (HTML/CSS/JS)

## Prérequis

- Python 3.14
- Git (optionnel)
- Un environnement virtuel Python (`venv`, `pipenv`, etc.)

## Installation du backend

1. Ouvrir un terminal à la racine du projet : `c:\Users\msi\Desktop\ppg`
2. Activer ou créer un environnement virtuel :

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Installer les dépendances :

   ```powershell
   pip install -r PPG_backend\requirements.txt
   ```

4. Copier le fichier d'exemple `.env` et ajuster si nécessaire :

   ```powershell
   copy PPG_backend\backend\.env.example PPG_backend\backend\.env
   ```

   - `USE_SQLITE=True` permet de démarrer sans configuration PostgreSQL.
   - Si vous utilisez PostgreSQL, mettez `USE_SQLITE=False` et remplissez les variables `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` et `DB_PORT`.

5. Appliquer les migrations Django :

   ```powershell
   cd PPG_backend\backend
   .\.venv\Scripts\python.exe manage.py migrate
   ```

6. (Optionnel) Créer un super utilisateur Django :

   ```powershell
   .\.venv\Scripts\python.exe manage.py createsuperuser
   ```

## Lancer le serveur backend

Depuis `PPG_backend\backend` :

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

Le backend sera accessible sur : `http://127.0.0.1:8000`

## Utiliser le frontend

Le frontend est fourni dans `PPG_front/pages/`.

- Ouvrez directement les pages HTML dans votre navigateur
- Ou utilisez un serveur local simple pour charger le frontend, par exemple :

```powershell
cd PPG_front
python -m http.server 5500
```

Puis ouvrez `http://127.0.0.1:5500/pages/login.html` ou `http://127.0.0.1:5500/pages/index.html`.

## Notes importantes

- Le backend Django lit les variables d'environnement depuis `PPG_backend\backend\.env`.
- La configuration CORS autorise déjà `http://localhost:5500` et `http://127.0.0.1:5500`.
- Par défaut, les e-mails sont envoyés à la console (via `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend`).

## Commandes utiles

- `python manage.py migrate` : appliquer les migrations
- `python manage.py runserver` : démarrer le serveur de développement
- `python manage.py createsuperuser` : créer un utilisateur administrateur
- `python -m http.server 5500` : démarrer un serveur local pour les pages frontend

## Support

Si quelque chose ne fonctionne pas, vérifiez :

- que l'environnement virtuel est activé
- que les dépendances sont installées
- que `PPG_backend\backend\.env` existe et est correct
- que le backend tourne sur `127.0.0.1:8000`
