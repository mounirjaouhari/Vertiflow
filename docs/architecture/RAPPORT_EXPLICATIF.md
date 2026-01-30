# Rapport Explicatif du Projet VertiFlow

## Introduction
VertiFlow est une plateforme numérique innovante dédiée à l’agriculture verticale intelligente, avec un focus particulier sur la culture du basilic. Ce projet vise à moderniser la production agricole en utilisant des technologies avancées de collecte de données, d’automatisation et d’intelligence artificielle.

## Objectifs du Projet
- Optimiser la croissance du basilic en environnement contrôlé (ferme verticale)
- Automatiser la gestion du climat, de l’arrosage et de la lumière grâce à des capteurs IoT
- Analyser et stocker les données pour améliorer la qualité et la quantité de la production
- Prédire les rendements et détecter les anomalies à l’aide du Machine Learning
- Assurer la traçabilité et la gouvernance des données pour une agriculture durable

## Fonctionnement Global
1. **Collecte de données** : Des capteurs mesurent en temps réel la température, l’humidité, la lumière, le CO2, etc.
2. **Transmission** : Les données sont envoyées via des réseaux sécurisés à la plateforme VertiFlow.
3. **Traitement et stockage** : Les données sont validées, stockées dans des bases adaptées (ClickHouse pour les séries temporelles, MongoDB pour les documents).
4. **Automatisation** : Des algorithmes analysent les données et pilotent automatiquement les équipements (lumières LED, arrosage, ventilation).
5. **Prédiction et optimisation** : Des modèles d’intelligence artificielle prévoient la croissance et optimisent les paramètres pour chaque étape de la vie du basilic.
6. **Visualisation** : Les résultats et indicateurs sont accessibles via des tableaux de bord (Power BI, Grafana).

## Points Clés Techniques
- **Architecture modulaire** : ingestion (NiFi), streaming (Kafka), stockage hybride, microservices Python pour l’intelligence.
- **Automatisation avancée** : moteur de décision (Cortex), prédiction de rendement (Oracle), simulateur bio-physique.
- **Gouvernance des données** : validation stricte, traçabilité, gestion des erreurs (Dead Letter Queue).
- **Infrastructure conteneurisée** : déploiement facile via Docker Compose.
- **Documentation complète** : guides, schémas, tickets, roadmap.

## Bénéfices
- Amélioration du rendement et de la qualité du basilic
- Réduction des ressources utilisées (eau, énergie)
- Production plus écologique et traçable
- Facilité d’adaptation à d’autres cultures à l’avenir

## Conclusion
VertiFlow représente une avancée majeure pour l’agriculture urbaine et durable. Grâce à l’automatisation, à l’analyse de données et à l’intelligence artificielle, il est possible de produire du basilic de haute qualité, toute l’année, avec un suivi précis et une optimisation continue.

---
Pour toute question ou contribution, consultez la documentation du projet ou contactez l’équipe sur GitHub.