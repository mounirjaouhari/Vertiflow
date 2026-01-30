#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
PROJET VERTIFLOW - Agriculture Verticale Intelligente
================================================================================
Date de création    : 25/12/2025
Équipe              : VertiFlow Core Team

Membres de l'équipe :
    🧙‍♂️ Mounir      - Architecte & Scientifique
    🏗️ Imrane      - DevOps & Infrastructure
    🐍 Mouhammed   - Data Engineer & Analyste ETL
    🧬 Asama       - Biologiste & Domain Expert
    ⚖️ MrZakaria    - Encadrant & Architecte Data

--------------------------------------------------------------------------------
MODULE: download_nasa_power.py
DESCRIPTION: Connecteur API pour les données météorologiques NASA POWER

Fonctionnalités principales:
    - Récupération des données T° et Humidité pour Casablanca
    - Formatage JSON compatible avec l'ingestion NiFi
    - Gestion de l'historique (J-1) et du temps réel

Développé par        : @Asama & @Mouhammed
Ticket(s) associé(s): TICKET-042
Sprint              : Semaine 3 - Données Externes

================================================================================
© 2025 VertiFlow Core Team - Tous droits réservés
Développé dans le cadre de l'Initiative Nationale Marocaine JobInTech
au sein de l'École YNOV Maroc Campus
================================================================================
"""

import requests
import json
import os
from datetime import datetime, timedelta

# Configuration : Casablanca, Maroc
LAT = 33.5731
LON = -7.5898
OUTPUT_DIR = "./data_ingestion/nasa_weather"

def fetch_nasa_data():
    # Paramètres : Température, Humidité, Rayonnement Solaire
    params = "T2M,RH2M,ALLSKY_SFC_SW_DWN"
    base_url = "https://power.larc.nasa.gov/api/temporal/hourly/point"
    
    # Période : Hier et Aujourd'hui
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=2)).strftime("%Y%m%d")
    
    url = f"{base_url}?parameters={params}&community=AG&longitude={LON}&latitude={LAT}&start={start_date}&end={end_date}&format=JSON"
    
    print(f"🌍 Appel API NASA POWER...")
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        
        # Sauvegarde
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
            
        filename = f"{OUTPUT_DIR}/nasa_weather_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
            
        print(f"✅ Données météo sauvegardées : {filename}")
    else:
        print(f"❌ Erreur API NASA : {response.status_code}")

if __name__ == "__main__":
    fetch_nasa_data()