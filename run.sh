#!/bin/bash
# Script pour lancer l'application

# Activer l'environnement virtuel si il existe
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Lancer l'application Flask
python app.py

