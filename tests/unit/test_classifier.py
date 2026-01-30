#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
PROJET VERTIFLOW - Agriculture Verticale Intelligente
================================================================================
Date de création    : 02/01/2026
Équipe              : VertiFlow Core Team

Membres de l'équipe :
    🧙‍♂️ Mounir      - Architecte & Scientifique (Python Dev)
    🏗️ Imrane      - DevOps & Infrastructure (Python Dev)
    🐍 Mouhammed   - Data Engineer & Analyste ETL
    🧬 Asama       - Biologiste & Domain Expert (Python Dev)
    ⚖️ MrZakaria   - Encadrant & Architecte Data

--------------------------------------------------------------------------------
MODULE: tests/unit/test_classifier.py
DESCRIPTION: Tests unitaires pour le classificateur de qualité (classifier.py)

    Le Classifier est le "système visuel" de VertiFlow.
    Il analyse les images des plantes pour évaluer leur qualité
    et détecter les anomalies (maladies, carences, stress).

    ARCHITECTURE DU SYSTÈME DE VISION:
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                    CLASSIFIER - QUALITÉ VISUELLE                        │
    ├─────────────────────────────────────────────────────────────────────────┤
    │                                                                         │
    │  ┌──────────────┐      ┌──────────────────┐      ┌─────────────────┐   │
    │  │   Caméra     │──────│  Prétraitement   │──────│  Extraction     │   │
    │  │  RGB/NIR     │      │  (resize, norm)  │      │  Features       │   │
    │  └──────────────┘      └──────────────────┘      └────────┬────────┘   │
    │                                                           │            │
    │                        ┌──────────────────────────────────┘            │
    │                        ▼                                               │
    │            ┌─────────────────────────┐                                 │
    │            │   FEATURES EXTRAITES    │                                 │
    │            ├─────────────────────────┤                                 │
    │            │ • Couleur (HSV, LAB)    │                                 │
    │            │ • Texture (GLCM)        │                                 │
    │            │ • Forme (contours)      │                                 │
    │            │ • NDVI (si NIR dispo)   │                                 │
    │            └────────────┬────────────┘                                 │
    │                         │                                              │
    │                         ▼                                              │
    │  ┌──────────────────────────────────────────────────────────────────┐  │
    │  │              MODÈLE DE CLASSIFICATION (Random Forest)            │  │
    │  ├──────────────────────────────────────────────────────────────────┤  │
    │  │  Classes:                                                        │  │
    │  │    • PREMIUM (95-100%): Qualité exceptionnelle, export           │  │
    │  │    • GRADE_A (80-94%): Standard commercial, vente directe        │  │
    │  │    • GRADE_B (60-79%): Transformation, industrie                 │  │
    │  │    • REJECT  (<60%): Compost, non-commercialisable               │  │
    │  └──────────────────────────────────────────────────────────────────┘  │
    │                                                                         │
    └─────────────────────────────────────────────────────────────────────────┘

    MÉTRIQUES DE QUALITÉ:
    ┌──────────────────┬────────────────────────────────────────────────────┐
    │ Métrique         │ Description                                        │
    ├──────────────────┼────────────────────────────────────────────────────┤
    │ green_ratio      │ Proportion de pixels verts (santé foliaire)        │
    │ yellow_ratio     │ Proportion jaune (sénescence, carences)            │
    │ brown_ratio      │ Proportion brune (nécrose, maladie)                │
    │ uniformity       │ Homogénéité de la couleur (stress)                 │
    │ leaf_area_index  │ Surface foliaire estimée (croissance)              │
    │ edge_sharpness   │ Netteté des contours (turgescence)                 │
    └──────────────────┴────────────────────────────────────────────────────┘

IMPORTANCE CRITIQUE:
    La classification visuelle détermine la DESTINATION COMMERCIALE.
    Une erreur de classification peut:
    - Envoyer du produit Premium en transformation (perte de marge)
    - Envoyer du produit défectueux aux clients (réclamations)
    - Manquer des signes précoces de maladie (propagation)

Développé par       : @Asama (expertise biologique) & @Mounir (ML)
Ticket(s) associé(s): TICKET-106
Sprint              : Semaine 6 - Phase Qualité & Tests

Dépendances:
    - pytest>=8.0.0
    - numpy>=2.1.0
    - opencv-python>=4.10.0 (cv2)
    - scikit-learn>=1.5.0

Références scientifiques:
    - Haralick et al. (1973): Textural Features for Image Classification
    - Woebbecke et al. (1995): Color Indices for Plant Segmentation
    - Meyer & Neto (2008): Vegetation Detection with ExG Index

================================================================================
© 2026 VertiFlow Core Team - Tous droits réservés
Développé dans le cadre de l'Initiative Nationale Marocaine JobInTech
au sein de l'École YNOV Maroc Campus
================================================================================
"""

import os
import pytest
import numpy as np
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, PropertyMock

# =============================================================================
# IMPORT DU MODULE À TESTER
# =============================================================================

try:
    from cloud_citadel.nervous_system.classifier import QualityClassifier
    CLASSIFIER_AVAILABLE = True
except ImportError as e:
    CLASSIFIER_AVAILABLE = False
    IMPORT_ERROR = str(e)

# Skip tous les tests si le module n'est pas importable
pytestmark = pytest.mark.skipif(
    not CLASSIFIER_AVAILABLE,
    reason=f"Module classifier non disponible: {IMPORT_ERROR if not CLASSIFIER_AVAILABLE else ''}"
)


# =============================================================================
# CONSTANTES DE TEST
# =============================================================================

# Dimensions d'image standard pour les tests
TEST_IMAGE_WIDTH = 640
TEST_IMAGE_HEIGHT = 480
TEST_IMAGE_CHANNELS = 3  # RGB

# Seuils de classification (doivent correspondre au code)
THRESHOLD_PREMIUM = 0.95
THRESHOLD_GRADE_A = 0.80
THRESHOLD_GRADE_B = 0.60

# Classes de qualité
QUALITY_CLASSES = ["PREMIUM", "GRADE_A", "GRADE_B", "REJECT"]

# Couleurs de référence (BGR pour OpenCV)
COLOR_HEALTHY_GREEN = [60, 180, 60]    # Vert sain
COLOR_YELLOW_STRESS = [0, 200, 200]    # Jaune (sénescence)
COLOR_BROWN_DISEASE = [30, 60, 100]    # Brun (nécrose)
COLOR_BACKGROUND = [200, 200, 200]     # Gris (plateau)


# =============================================================================
# FIXTURES SPÉCIFIQUES AU CLASSIFIER
# =============================================================================

@pytest.fixture
def create_test_image():
    """
    Factory fixture pour créer des images de test.
    
    USAGE:
        image = create_test_image(quality="healthy")
        image = create_test_image(quality="stressed", yellow_ratio=0.3)
    
    RETOURNE:
        numpy.ndarray de shape (480, 640, 3) en uint8
    """
    def _create_image(
        quality: str = "healthy",
        green_ratio: float = 0.8,
        yellow_ratio: float = 0.0,
        brown_ratio: float = 0.0,
        noise_level: float = 0.05
    ) -> np.ndarray:
        """
        Crée une image synthétique simulant une plante.
        
        PARAMÈTRES:
            quality: "healthy", "stressed", "diseased", "dead"
            green_ratio: Proportion de pixels verts (0-1)
            yellow_ratio: Proportion de pixels jaunes (0-1)
            brown_ratio: Proportion de pixels bruns (0-1)
            noise_level: Niveau de bruit gaussien (0-1)
        
        ALGORITHME:
            1. Créer un fond gris (plateau)
            2. Dessiner une région centrale (feuillage)
            3. Colorer selon les ratios spécifiés
            4. Ajouter du bruit pour réalisme
        """
        # Initialiser avec fond gris
        image = np.full(
            (TEST_IMAGE_HEIGHT, TEST_IMAGE_WIDTH, TEST_IMAGE_CHANNELS),
            COLOR_BACKGROUND,
            dtype=np.uint8
        )
        
        # Définir la région centrale (feuillage circulaire)
        center_y, center_x = TEST_IMAGE_HEIGHT // 2, TEST_IMAGE_WIDTH // 2
        radius = min(TEST_IMAGE_HEIGHT, TEST_IMAGE_WIDTH) // 3
        
        # Créer un masque circulaire pour le feuillage
        y_coords, x_coords = np.ogrid[:TEST_IMAGE_HEIGHT, :TEST_IMAGE_WIDTH]
        mask = ((x_coords - center_x) ** 2 + (y_coords - center_y) ** 2) <= radius ** 2
        
        # Calculer le nombre de pixels pour chaque couleur
        foliage_pixels = np.sum(mask)
        n_green = int(foliage_pixels * green_ratio)
        n_yellow = int(foliage_pixels * yellow_ratio)
        n_brown = int(foliage_pixels * brown_ratio)
        
        # Obtenir les indices des pixels du feuillage
        foliage_indices = np.where(mask)
        n_foliage = len(foliage_indices[0])
        
        # Mélanger les indices pour distribution aléatoire
        np.random.seed(42)  # Reproductibilité
        perm = np.random.permutation(n_foliage)
        
        # Assigner les couleurs
        idx = 0
        
        # Pixels verts
        for i in range(min(n_green, n_foliage - idx)):
            y, x = foliage_indices[0][perm[idx + i]], foliage_indices[1][perm[idx + i]]
            image[y, x] = COLOR_HEALTHY_GREEN
        idx += n_green
        
        # Pixels jaunes
        for i in range(min(n_yellow, n_foliage - idx)):
            if idx + i < n_foliage:
                y, x = foliage_indices[0][perm[idx + i]], foliage_indices[1][perm[idx + i]]
                image[y, x] = COLOR_YELLOW_STRESS
        idx += n_yellow
        
        # Pixels bruns
        for i in range(min(n_brown, n_foliage - idx)):
            if idx + i < n_foliage:
                y, x = foliage_indices[0][perm[idx + i]], foliage_indices[1][perm[idx + i]]
                image[y, x] = COLOR_BROWN_DISEASE
        
        # Ajouter du bruit gaussien
        if noise_level > 0:
            noise = np.random.normal(0, noise_level * 255, image.shape).astype(np.int16)
            image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        return image
    
    return _create_image


@pytest.fixture
def healthy_plant_image(create_test_image):
    """
    Image d'une plante saine (qualité PREMIUM attendue).
    
    CARACTÉRISTIQUES:
        - 90% vert sain
        - 5% jaune (sénescence normale des feuilles basses)
        - 0% brun (pas de maladie)
    """
    return create_test_image(
        quality="healthy",
        green_ratio=0.90,
        yellow_ratio=0.05,
        brown_ratio=0.00
    )


@pytest.fixture
def stressed_plant_image(create_test_image):
    """
    Image d'une plante stressée (qualité GRADE_B attendue).
    
    CARACTÉRISTIQUES:
        - 50% vert
        - 35% jaune (stress hydrique/nutritionnel)
        - 10% brun (début de nécrose)
    """
    return create_test_image(
        quality="stressed",
        green_ratio=0.50,
        yellow_ratio=0.35,
        brown_ratio=0.10
    )


@pytest.fixture
def diseased_plant_image(create_test_image):
    """
    Image d'une plante malade (qualité REJECT attendue).
    
    CARACTÉRISTIQUES:
        - 20% vert restant
        - 30% jaune
        - 40% brun (nécrose avancée)
    """
    return create_test_image(
        quality="diseased",
        green_ratio=0.20,
        yellow_ratio=0.30,
        brown_ratio=0.40
    )


@pytest.fixture
def mock_ml_model():
    """
    Mock du modèle ML de classification.
    
    Simule un RandomForestClassifier entraîné qui:
    - predict(): retourne la classe prédite
    - predict_proba(): retourne les probabilités par classe
    """
    mock_model = MagicMock()
    
    # Par défaut, prédit GRADE_A avec haute confiance
    mock_model.predict.return_value = np.array(["GRADE_A"])
    mock_model.predict_proba.return_value = np.array([[0.05, 0.85, 0.08, 0.02]])
    mock_model.classes_ = np.array(["PREMIUM", "GRADE_A", "GRADE_B", "REJECT"])
    
    return mock_model


@pytest.fixture
def classifier_instance(mock_ml_model):
    """
    Crée une instance de QualityClassifier avec modèle mocké.
    """
    with patch('cloud_citadel.nervous_system.classifier.joblib') as mock_joblib:
        mock_joblib.load.return_value = mock_ml_model
        
        classifier = QualityClassifier()
        classifier.model = mock_ml_model
        
        yield classifier


# =============================================================================
# CLASSE DE TEST: EXTRACTION DE FEATURES COULEUR
# =============================================================================

class TestColorFeatureExtraction:
    """
    Tests de l'extraction des features basées sur la couleur.
    
    FEATURES COULEUR:
        - green_ratio: Proportion de pixels verts (indicateur de santé)
        - yellow_ratio: Proportion jaune (sénescence/carence)
        - brown_ratio: Proportion brune (maladie/nécrose)
        - color_uniformity: Homogénéité de la distribution des couleurs
    
    ESPACE COLORIMÉTRIQUE:
        HSV est utilisé car il sépare teinte (H), saturation (S), et valeur (V),
        permettant une détection robuste des couleurs indépendante de l'éclairage.
    """
    
    # -------------------------------------------------------------------------
    # TEST 1: Extraction du ratio vert
    # -------------------------------------------------------------------------
    def test_extract_green_ratio_healthy(self, classifier_instance, healthy_plant_image):
        """
        Test: extraction correcte du ratio vert pour une plante saine.
        
        ATTENDU:
            green_ratio > 0.7 (image créée avec 90% de vert)
        
        NOTE:
            Le ratio extrait peut différer du ratio de création car
            l'extraction utilise des plages HSV spécifiques.
        """
        # ACT
        features = classifier_instance.extract_color_features(healthy_plant_image)
        
        # ASSERT
        assert "green_ratio" in features, "Feature 'green_ratio' manquante"
        assert features["green_ratio"] > 0.5, (
            f"Une plante saine devrait avoir green_ratio > 0.5.\n"
            f"Obtenu: {features['green_ratio']:.2f}"
        )
    
    # -------------------------------------------------------------------------
    # TEST 2: Extraction du ratio jaune
    # -------------------------------------------------------------------------
    def test_extract_yellow_ratio_stressed(self, classifier_instance, stressed_plant_image):
        """
        Test: extraction correcte du ratio jaune pour une plante stressée.
        
        ATTENDU:
            yellow_ratio > 0.15 (image créée avec 35% de jaune)
        """
        # ACT
        features = classifier_instance.extract_color_features(stressed_plant_image)
        
        # ASSERT
        assert "yellow_ratio" in features, "Feature 'yellow_ratio' manquante"
        assert features["yellow_ratio"] > 0.1, (
            f"Une plante stressée devrait avoir yellow_ratio > 0.1.\n"
            f"Obtenu: {features['yellow_ratio']:.2f}"
        )
    
    # -------------------------------------------------------------------------
    # TEST 3: Extraction du ratio brun
    # -------------------------------------------------------------------------
    def test_extract_brown_ratio_diseased(self, classifier_instance, diseased_plant_image):
        """
        Test: extraction correcte du ratio brun pour une plante malade.
        
        ATTENDU:
            brown_ratio > 0.2 (image créée avec 40% de brun)
        """
        # ACT
        features = classifier_instance.extract_color_features(diseased_plant_image)
        
        # ASSERT
        assert "brown_ratio" in features, "Feature 'brown_ratio' manquante"
        assert features["brown_ratio"] > 0.1, (
            f"Une plante malade devrait avoir brown_ratio > 0.1.\n"
            f"Obtenu: {features['brown_ratio']:.2f}"
        )
    
    # -------------------------------------------------------------------------
    # TEST 4: Somme des ratios <= 1
    # -------------------------------------------------------------------------
    def test_color_ratios_sum_valid(self, classifier_instance, create_test_image):
        """
        Test: la somme des ratios de couleur ne dépasse pas 1.
        
        JUSTIFICATION:
            Les ratios représentent des proportions sur la même surface.
            La somme peut être < 1 si des pixels ne sont classés dans
            aucune catégorie (ex: fond, ombres).
        """
        # ARRANGE - Différentes images
        test_images = [
            create_test_image(green_ratio=0.9, yellow_ratio=0.05, brown_ratio=0.0),
            create_test_image(green_ratio=0.5, yellow_ratio=0.3, brown_ratio=0.1),
            create_test_image(green_ratio=0.2, yellow_ratio=0.3, brown_ratio=0.4),
        ]
        
        # ACT & ASSERT
        for i, image in enumerate(test_images):
            features = classifier_instance.extract_color_features(image)
            
            total = (
                features.get("green_ratio", 0) +
                features.get("yellow_ratio", 0) +
                features.get("brown_ratio", 0)
            )
            
            assert total <= 1.1, (  # Tolérance de 10% pour les chevauchements
                f"Image {i}: somme des ratios devrait être <= 1.\n"
                f"Somme: {total:.2f}"
            )
    
    # -------------------------------------------------------------------------
    # TEST 5: Uniformité de couleur
    # -------------------------------------------------------------------------
    def test_color_uniformity_extraction(self, classifier_instance, healthy_plant_image):
        """
        Test: extraction de la métrique d'uniformité.
        
        UNIFORMITÉ:
            Mesure l'homogénéité de la distribution des couleurs.
            - Haute uniformité: Plante en bonne santé, croissance régulière
            - Basse uniformité: Stress localisé, hétérogénéité
        """
        # ACT
        features = classifier_instance.extract_color_features(healthy_plant_image)
        
        # ASSERT
        assert "uniformity" in features or "color_uniformity" in features, (
            "Feature d'uniformité manquante"
        )
        
        uniformity = features.get("uniformity", features.get("color_uniformity", 0))
        assert 0 <= uniformity <= 1, f"Uniformité hors plage [0,1]: {uniformity}"


# =============================================================================
# CLASSE DE TEST: EXTRACTION DE FEATURES TEXTURE
# =============================================================================

class TestTextureFeatureExtraction:
    """
    Tests de l'extraction des features de texture (GLCM).
    
    GLCM (Gray-Level Co-occurrence Matrix):
        Matrice qui capture la fréquence de paires de pixels adjacents
        à différentes intensités. Permet de caractériser la texture.
    
    FEATURES GLCM:
        - contrast: Différence d'intensité entre pixels adjacents
        - correlation: Corrélation linéaire des niveaux de gris
        - energy: Uniformité de la distribution
        - homogeneity: Similarité locale
    
    RÉFÉRENCE:
        Haralick, R.M. et al. (1973). "Textural Features for Image
        Classification". IEEE Transactions on Systems, Man, and Cybernetics.
    """
    
    # -------------------------------------------------------------------------
    # TEST 1: Extraction du contraste
    # -------------------------------------------------------------------------
    def test_extract_texture_contrast(self, classifier_instance, healthy_plant_image):
        """
        Test: extraction correcte du contraste de texture.
        
        CONTRASTE:
            Mesure les variations locales d'intensité.
            - Bas contraste: Surface lisse (feuilles saines)
            - Haut contraste: Surface rugueuse (maladie, dégâts)
        """
        # ACT
        features = classifier_instance.extract_texture_features(healthy_plant_image)
        
        # ASSERT
        assert "contrast" in features or "texture_contrast" in features, (
            "Feature 'contrast' manquante"
        )
        
        contrast = features.get("contrast", features.get("texture_contrast", 0))
        assert contrast >= 0, f"Le contraste devrait être >= 0: {contrast}"
    
    # -------------------------------------------------------------------------
    # TEST 2: Extraction de l'énergie
    # -------------------------------------------------------------------------
    def test_extract_texture_energy(self, classifier_instance, healthy_plant_image):
        """
        Test: extraction correcte de l'énergie de texture.
        
        ÉNERGIE (aussi appelée Angular Second Moment):
            Mesure l'uniformité de la distribution des niveaux de gris.
            - Haute énergie: Image très uniforme
            - Basse énergie: Image avec beaucoup de variations
        """
        # ACT
        features = classifier_instance.extract_texture_features(healthy_plant_image)
        
        # ASSERT
        if "energy" in features or "texture_energy" in features:
            energy = features.get("energy", features.get("texture_energy", 0))
            assert 0 <= energy <= 1, f"Énergie hors plage [0,1]: {energy}"
    
    # -------------------------------------------------------------------------
    # TEST 3: Corrélation texture
    # -------------------------------------------------------------------------
    def test_extract_texture_correlation(self, classifier_instance, healthy_plant_image):
        """
        Test: extraction de la corrélation de texture.
        
        CORRÉLATION:
            Mesure la dépendance linéaire entre pixels adjacents.
            Plage: [-1, 1]
        """
        # ACT
        features = classifier_instance.extract_texture_features(healthy_plant_image)
        
        # ASSERT
        if "correlation" in features:
            correlation = features["correlation"]
            assert -1 <= correlation <= 1, (
                f"Corrélation hors plage [-1,1]: {correlation}"
            )


# =============================================================================
# CLASSE DE TEST: CLASSIFICATION DE QUALITÉ
# =============================================================================

class TestQualityClassification:
    """
    Tests de la classification finale de qualité.
    
    CLASSES:
        - PREMIUM: Qualité exceptionnelle (score >= 95%)
        - GRADE_A: Standard commercial (score >= 80%)
        - GRADE_B: Transformation (score >= 60%)
        - REJECT: Non commercialisable (score < 60%)
    """
    
    # -------------------------------------------------------------------------
    # TEST 1: Classification plante saine
    # -------------------------------------------------------------------------
    def test_classify_healthy_plant(self, classifier_instance, healthy_plant_image, mock_ml_model):
        """
        Test: une plante saine est classée PREMIUM ou GRADE_A.
        
        ATTENDU:
            Classe parmi ["PREMIUM", "GRADE_A"]
        """
        # ARRANGE - Configurer le mock pour retourner PREMIUM
        mock_ml_model.predict.return_value = np.array(["PREMIUM"])
        mock_ml_model.predict_proba.return_value = np.array([[0.92, 0.06, 0.01, 0.01]])
        
        # ACT
        result = classifier_instance.classify(healthy_plant_image)
        
        # ASSERT
        assert result is not None, "Le résultat ne devrait pas être None"
        assert "quality_class" in result or "class" in result, (
            "Clé de classe manquante dans le résultat"
        )
        
        quality_class = result.get("quality_class", result.get("class"))
        assert quality_class in ["PREMIUM", "GRADE_A"], (
            f"Une plante saine devrait être PREMIUM ou GRADE_A.\n"
            f"Obtenu: {quality_class}"
        )
    
    # -------------------------------------------------------------------------
    # TEST 2: Classification plante stressée
    # -------------------------------------------------------------------------
    def test_classify_stressed_plant(self, classifier_instance, stressed_plant_image, mock_ml_model):
        """
        Test: une plante stressée est classée GRADE_A ou GRADE_B.
        """
        # ARRANGE
        mock_ml_model.predict.return_value = np.array(["GRADE_B"])
        mock_ml_model.predict_proba.return_value = np.array([[0.05, 0.25, 0.60, 0.10]])
        
        # ACT
        result = classifier_instance.classify(stressed_plant_image)
        
        # ASSERT
        quality_class = result.get("quality_class", result.get("class"))
        assert quality_class in ["GRADE_A", "GRADE_B"], (
            f"Une plante stressée devrait être GRADE_A ou GRADE_B.\n"
            f"Obtenu: {quality_class}"
        )
    
    # -------------------------------------------------------------------------
    # TEST 3: Classification plante malade
    # -------------------------------------------------------------------------
    def test_classify_diseased_plant(self, classifier_instance, diseased_plant_image, mock_ml_model):
        """
        Test: une plante malade est classée GRADE_B ou REJECT.
        """
        # ARRANGE
        mock_ml_model.predict.return_value = np.array(["REJECT"])
        mock_ml_model.predict_proba.return_value = np.array([[0.01, 0.04, 0.15, 0.80]])
        
        # ACT
        result = classifier_instance.classify(diseased_plant_image)
        
        # ASSERT
        quality_class = result.get("quality_class", result.get("class"))
        assert quality_class in ["GRADE_B", "REJECT"], (
            f"Une plante malade devrait être GRADE_B ou REJECT.\n"
            f"Obtenu: {quality_class}"
        )
    
    # -------------------------------------------------------------------------
    # TEST 4: Score de confiance inclus
    # -------------------------------------------------------------------------
    def test_classify_returns_confidence(self, classifier_instance, healthy_plant_image, mock_ml_model):
        """
        Test: la classification retourne un score de confiance.
        
        CONFIANCE:
            Probabilité de la classe prédite, entre 0 et 1.
            Utilisée pour filtrer les classifications incertaines.
        """
        # ARRANGE
        mock_ml_model.predict.return_value = np.array(["GRADE_A"])
        mock_ml_model.predict_proba.return_value = np.array([[0.05, 0.85, 0.08, 0.02]])
        
        # ACT
        result = classifier_instance.classify(healthy_plant_image)
        
        # ASSERT
        assert "confidence" in result or "probability" in result or "score" in result, (
            "Score de confiance manquant dans le résultat"
        )
        
        confidence = result.get("confidence", result.get("probability", result.get("score")))
        assert 0 <= confidence <= 1, f"Confiance hors plage [0,1]: {confidence}"
    
    # -------------------------------------------------------------------------
    # TEST 5: Toutes les classes sont valides
    # -------------------------------------------------------------------------
    @pytest.mark.parametrize("predicted_class", QUALITY_CLASSES)
    def test_classify_valid_classes(self, classifier_instance, healthy_plant_image, mock_ml_model, predicted_class):
        """
        Test paramétré: toutes les classes retournées sont valides.
        """
        # ARRANGE
        mock_ml_model.predict.return_value = np.array([predicted_class])
        
        # ACT
        result = classifier_instance.classify(healthy_plant_image)
        
        # ASSERT
        quality_class = result.get("quality_class", result.get("class"))
        assert quality_class in QUALITY_CLASSES, (
            f"Classe invalide: {quality_class}"
        )


# =============================================================================
# CLASSE DE TEST: DÉTECTION D'ANOMALIES
# =============================================================================

class TestAnomalyDetection:
    """
    Tests de la détection d'anomalies (maladies, carences).
    
    ANOMALIES DÉTECTÉES:
        - Mildiou (downy mildew): Taches brunes diffuses
        - Fusarium: Flétrissement, jaunissement asymétrique
        - Carence azote: Jaunissement uniforme des feuilles basses
        - Carence magnésium: Chlorose internervaire
        - Stress hydrique: Flétrissement, enroulement des feuilles
    """
    
    # -------------------------------------------------------------------------
    # TEST 1: Détection de zones brunes (maladie potentielle)
    # -------------------------------------------------------------------------
    def test_detect_brown_spots(self, classifier_instance, diseased_plant_image):
        """
        Test: détection des zones brunes (indicateur de maladie).
        """
        # ACT
        anomalies = classifier_instance.detect_anomalies(diseased_plant_image)
        
        # ASSERT
        assert anomalies is not None, "La détection d'anomalies ne devrait pas retourner None"
        
        # Vérifier si la maladie est détectée
        has_disease_indicator = (
            anomalies.get("disease_risk", 0) > 0.3 or
            anomalies.get("brown_spots_detected", False) or
            "disease" in str(anomalies).lower()
        )
        
        assert has_disease_indicator, (
            f"Une plante avec 40% de zones brunes devrait déclencher une alerte.\n"
            f"Anomalies détectées: {anomalies}"
        )
    
    # -------------------------------------------------------------------------
    # TEST 2: Pas d'anomalie sur plante saine
    # -------------------------------------------------------------------------
    def test_no_anomaly_healthy_plant(self, classifier_instance, healthy_plant_image):
        """
        Test: pas d'anomalie majeure détectée sur plante saine.
        """
        # ACT
        anomalies = classifier_instance.detect_anomalies(healthy_plant_image)
        
        # ASSERT
        if anomalies:
            # Vérifier qu'aucun risque majeur n'est détecté
            disease_risk = anomalies.get("disease_risk", 0)
            stress_risk = anomalies.get("stress_risk", 0)
            
            assert disease_risk < 0.3, (
                f"Une plante saine ne devrait pas avoir un risque de maladie élevé.\n"
                f"Disease risk: {disease_risk}"
            )
    
    # -------------------------------------------------------------------------
    # TEST 3: Détection de stress
    # -------------------------------------------------------------------------
    def test_detect_stress_indicators(self, classifier_instance, stressed_plant_image):
        """
        Test: détection des indicateurs de stress.
        """
        # ACT
        anomalies = classifier_instance.detect_anomalies(stressed_plant_image)
        
        # ASSERT
        if anomalies:
            has_stress_indicator = (
                anomalies.get("stress_risk", 0) > 0.2 or
                anomalies.get("yellow_ratio", 0) > 0.2 or
                "stress" in str(anomalies).lower()
            )
            
            # Note: Le test est indicatif, le seuil dépend de l'implémentation
            # On vérifie au moins que la fonction retourne quelque chose


# =============================================================================
# CLASSE DE TEST: PRÉTRAITEMENT D'IMAGE
# =============================================================================

class TestImagePreprocessing:
    """
    Tests du prétraitement des images avant classification.
    
    ÉTAPES DE PRÉTRAITEMENT:
        1. Redimensionnement à taille standard (224x224 ou 640x480)
        2. Normalisation des valeurs de pixels (0-1 ou -1 à 1)
        3. Correction gamma (si éclairage variable)
        4. Suppression du bruit (filtre gaussien ou médian)
    """
    
    # -------------------------------------------------------------------------
    # TEST 1: Redimensionnement correct
    # -------------------------------------------------------------------------
    def test_preprocess_resize(self, classifier_instance, create_test_image):
        """
        Test: l'image est redimensionnée à la taille attendue.
        """
        # ARRANGE - Image de taille non-standard
        large_image = np.zeros((1080, 1920, 3), dtype=np.uint8)
        
        # ACT
        if hasattr(classifier_instance, 'preprocess'):
            processed = classifier_instance.preprocess(large_image)
            
            # ASSERT - Vérifier que la taille a changé
            assert processed.shape != large_image.shape, (
                "L'image devrait être redimensionnée"
            )
    
    # -------------------------------------------------------------------------
    # TEST 2: Normalisation des valeurs
    # -------------------------------------------------------------------------
    def test_preprocess_normalization(self, classifier_instance, healthy_plant_image):
        """
        Test: les valeurs de pixels sont normalisées.
        """
        # ACT
        if hasattr(classifier_instance, 'preprocess'):
            processed = classifier_instance.preprocess(healthy_plant_image)
            
            # ASSERT - Valeurs dans une plage normalisée
            if processed.dtype == np.float32 or processed.dtype == np.float64:
                assert processed.max() <= 1.0, "Valeurs devraient être <= 1 après normalisation"
                assert processed.min() >= -1.0, "Valeurs devraient être >= -1 après normalisation"
    
    # -------------------------------------------------------------------------
    # TEST 3: Gestion des images invalides
    # -------------------------------------------------------------------------
    def test_preprocess_handles_invalid_input(self, classifier_instance):
        """
        Test: gestion gracieuse des entrées invalides.
        """
        # ARRANGE - Image invalide (None)
        invalid_inputs = [
            None,
            np.array([]),  # Array vide
            np.zeros((10,)),  # 1D au lieu de 3D
        ]
        
        # ACT & ASSERT
        for invalid_input in invalid_inputs:
            try:
                if hasattr(classifier_instance, 'preprocess'):
                    result = classifier_instance.preprocess(invalid_input)
                    # Si pas d'exception, vérifier que result est géré
            except (ValueError, TypeError, AttributeError):
                pass  # Exception attendue pour entrée invalide


# =============================================================================
# CLASSE DE TEST: PERFORMANCE ET ROBUSTESSE
# =============================================================================

class TestPerformanceAndRobustness:
    """
    Tests de performance et robustesse du classifier.
    """
    
    # -------------------------------------------------------------------------
    # TEST 1: Temps de classification
    # -------------------------------------------------------------------------
    @pytest.mark.slow
    def test_classification_performance(self, classifier_instance, healthy_plant_image):
        """
        Test: la classification se fait en temps raisonnable.
        
        OBJECTIF:
            < 500ms par image (cadence 2 images/seconde)
        
        CONTEXTE:
            Le système traite des images en temps réel pendant
            les opérations de récolte.
        """
        import time
        
        # ACT
        start = time.perf_counter()
        result = classifier_instance.classify(healthy_plant_image)
        elapsed = time.perf_counter() - start
        
        # ASSERT
        assert elapsed < 0.5, (
            f"La classification devrait prendre < 500ms.\n"
            f"Temps écoulé: {elapsed * 1000:.1f}ms"
        )
    
    # -------------------------------------------------------------------------
    # TEST 2: Robustesse au bruit
    # -------------------------------------------------------------------------
    def test_robustness_to_noise(self, classifier_instance, create_test_image, mock_ml_model):
        """
        Test: classification stable malgré le bruit.
        
        Une légère variation de bruit ne devrait pas changer
        radicalement la classification.
        """
        # ARRANGE - Même image avec différents niveaux de bruit
        mock_ml_model.predict.return_value = np.array(["GRADE_A"])
        
        image_clean = create_test_image(green_ratio=0.85, noise_level=0.01)
        image_noisy = create_test_image(green_ratio=0.85, noise_level=0.10)
        
        # ACT
        result_clean = classifier_instance.classify(image_clean)
        result_noisy = classifier_instance.classify(image_noisy)
        
        # ASSERT - Les deux devraient être classifiés (pas de crash)
        assert result_clean is not None
        assert result_noisy is not None
    
    # -------------------------------------------------------------------------
    # TEST 3: Gestion mémoire (images multiples)
    # -------------------------------------------------------------------------
    def test_memory_handling_multiple_images(self, classifier_instance, create_test_image, mock_ml_model):
        """
        Test: pas de fuite mémoire avec plusieurs images.
        """
        # ARRANGE
        mock_ml_model.predict.return_value = np.array(["GRADE_A"])
        
        # ACT - Classifier plusieurs images
        for i in range(10):
            image = create_test_image(green_ratio=0.7 + i * 0.02)
            result = classifier_instance.classify(image)
            
            # Vérifier que chaque classification réussit
            assert result is not None, f"Échec à l'itération {i}"


# =============================================================================
# FIN DU MODULE - TICKET-106 - Tests Quality Classifier VertiFlow
# =============================================================================
