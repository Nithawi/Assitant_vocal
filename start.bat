@echo off

:: Vérification de l'environnement virtuel
if not exist venv (
    echo [INFO] Creation de l'environnement virtuel...
    python -m venv venv
)

:: Activer l'environnement virtuel
call venv\Scripts\activate
if errorlevel 1 (
    echo [ERROR] Impossible d'activer l'environnement virtuel !
    pause
    exit /b 1
)

:: Mise à jour de pip
echo [INFO] Mise a jour de pip...
python -m pip install --upgrade pip

:: Installation des dépendances
if exist requirements.txt (
    echo [INFO] Installation des dependances depuis requirements.txt...
    pip install -r requirements.txt -q
) else (
    echo [WARNING] Aucun fichier requirements.txt trouve !
)

:: Lancer le programme
echo [INFO] Lancement de l'assistant vocal...
python cookie.py

:: Garder la fenêtre ouverte si une erreur survient
pause