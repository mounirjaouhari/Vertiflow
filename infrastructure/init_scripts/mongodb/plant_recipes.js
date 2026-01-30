// ============================================================================
// PROJET VERTIFLOW - Agriculture Verticale Intelligente
// ============================================================================
// Date de creation    : 04/01/2026
// Equipe              : VertiFlow Core Team
//
// ----------------------------------------------------------------------------
// SCRIPT: plant_recipes.js
// BASE DE DONNEES: MongoDB
// COLLECTION: plant_recipes
// DESCRIPTION: Recettes nutritives et spectrales validees scientifiquement
//              Basees sur Cornell CEA, Fluence, et recherche academique
//
// Sources:
//   - Cornell University CEA Program
//   - Fluence by OSRAM Research
//   - FAO Irrigation Paper 56
//   - Wageningen University LED Research
//
// Developpe par       : @Asama, @Mounir
// Ticket(s) associe(s): TICKET-058
// Sprint              : Semaine 6 - Reference Data
// ============================================================================

// Connexion a la base
db = db.getSiblingDB('vertiflow_metadata');

// Suppression collection existante si necessaire
db.plant_recipes.drop();

// Creation de la collection avec validation de schema
db.createCollection("plant_recipes", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["recipe_id", "crop_type", "growth_stage", "created_at"],
            properties: {
                recipe_id: { bsonType: "string" },
                crop_type: { bsonType: "string" },
                variety: { bsonType: "string" },
                growth_stage: {
                    bsonType: "string",
                    enum: ["germination", "seedling", "vegetative", "flowering", "finishing"]
                }
            }
        }
    }
});

// Index pour recherche rapide
db.plant_recipes.createIndex({ "recipe_id": 1 }, { unique: true });
db.plant_recipes.createIndex({ "crop_type": 1, "growth_stage": 1 });
db.plant_recipes.createIndex({ "spectral_recipe_id": 1 });

print("Inserting plant recipes...");

// ============================================================================
// RECETTES BASILIC (Ocimum basilicum)
// ============================================================================

db.plant_recipes.insertMany([
    // --- BASILIC GERMINATION ---
    {
        recipe_id: "BASIL-GERM-001",
        crop_type: "basil",
        variety: "Genovese",
        scientific_name: "Ocimum basilicum 'Genovese'",
        growth_stage: "germination",
        duration_days: { min: 5, max: 7, optimal: 6 },

        // Parametres environnementaux
        environment: {
            temperature_c: { min: 20, max: 25, optimal: 22, night_drop: 2 },
            humidity_pct: { min: 70, max: 85, optimal: 80 },
            co2_ppm: { min: 400, max: 600, optimal: 450 },
            vpd_kpa: { min: 0.4, max: 0.8, optimal: 0.6 },
            air_velocity_ms: { min: 0.1, max: 0.3, optimal: 0.2 }
        },

        // Parametres lumineux (spectre LED)
        lighting: {
            spectral_recipe_id: "SPR-BASIL-GERM",
            ppfd_umol: { min: 100, max: 200, optimal: 150 },
            dli_mol: { min: 6, max: 10, optimal: 8 },
            photoperiod_h: 18,
            spectrum: {
                blue_450nm_pct: 35,
                red_660nm_pct: 45,
                far_red_730nm_pct: 5,
                white_pct: 15
            },
            ratio_red_blue: 1.3,
            light_compensation_point: 20,
            light_saturation_point: 400
        },

        // Solution nutritive
        nutrition: {
            nutrient_recipe_id: "NUT-BASIL-GERM",
            ec_ms: { min: 0.8, max: 1.2, optimal: 1.0 },
            ph: { min: 5.5, max: 6.0, optimal: 5.8 },
            water_temp_c: { min: 18, max: 22, optimal: 20 },

            // Macronutriments (ppm)
            macronutrients: {
                N: { min: 80, max: 120, optimal: 100 },
                P: { min: 25, max: 40, optimal: 30 },
                K: { min: 100, max: 150, optimal: 120 },
                Ca: { min: 60, max: 100, optimal: 80 },
                Mg: { min: 20, max: 35, optimal: 25 },
                S: { min: 25, max: 40, optimal: 30 }
            },

            // Micronutriments (ppm)
            micronutrients: {
                Fe: { optimal: 2.5 },
                Mn: { optimal: 0.5 },
                Zn: { optimal: 0.3 },
                Cu: { optimal: 0.05 },
                B: { optimal: 0.3 },
                Mo: { optimal: 0.05 }
            }
        },

        // Metriques cibles
        targets: {
            germination_rate_pct: 95,
            days_to_emergence: 5,
            root_length_mm: 15
        },

        // Metadata
        source: "Cornell CEA + Internal Calibration",
        validated: true,
        validation_date: new Date("2025-12-01"),
        created_at: new Date(),
        updated_at: new Date()
    },

    // --- BASILIC PLANTULE (Seedling) ---
    {
        recipe_id: "BASIL-SEED-001",
        crop_type: "basil",
        variety: "Genovese",
        scientific_name: "Ocimum basilicum 'Genovese'",
        growth_stage: "seedling",
        duration_days: { min: 7, max: 10, optimal: 8 },

        environment: {
            temperature_c: { min: 20, max: 26, optimal: 23, night_drop: 3 },
            humidity_pct: { min: 60, max: 75, optimal: 68 },
            co2_ppm: { min: 600, max: 900, optimal: 800 },
            vpd_kpa: { min: 0.5, max: 0.9, optimal: 0.7 },
            air_velocity_ms: { min: 0.2, max: 0.5, optimal: 0.3 }
        },

        lighting: {
            spectral_recipe_id: "SPR-BASIL-SEED",
            ppfd_umol: { min: 200, max: 300, optimal: 250 },
            dli_mol: { min: 10, max: 14, optimal: 12 },
            photoperiod_h: 18,
            spectrum: {
                blue_450nm_pct: 30,
                red_660nm_pct: 50,
                far_red_730nm_pct: 6,
                white_pct: 14
            },
            ratio_red_blue: 1.67,
            light_compensation_point: 25,
            light_saturation_point: 600
        },

        nutrition: {
            nutrient_recipe_id: "NUT-BASIL-SEED",
            ec_ms: { min: 1.0, max: 1.4, optimal: 1.2 },
            ph: { min: 5.6, max: 6.2, optimal: 5.9 },
            water_temp_c: { min: 18, max: 22, optimal: 20 },

            macronutrients: {
                N: { min: 100, max: 140, optimal: 120 },
                P: { min: 35, max: 50, optimal: 40 },
                K: { min: 140, max: 180, optimal: 160 },
                Ca: { min: 80, max: 110, optimal: 95 },
                Mg: { min: 28, max: 40, optimal: 32 },
                S: { min: 35, max: 50, optimal: 40 }
            },

            micronutrients: {
                Fe: { optimal: 2.8 },
                Mn: { optimal: 0.6 },
                Zn: { optimal: 0.35 },
                Cu: { optimal: 0.06 },
                B: { optimal: 0.4 },
                Mo: { optimal: 0.06 }
            }
        },

        targets: {
            leaf_count: 4,
            stem_diameter_mm: 2.5,
            plant_height_cm: 5,
            chlorophyll_spad: 35
        },

        source: "Cornell CEA + Internal Calibration",
        validated: true,
        validation_date: new Date("2025-12-01"),
        created_at: new Date(),
        updated_at: new Date()
    },

    // --- BASILIC VEGETATIF ---
    {
        recipe_id: "BASIL-VEG-001",
        crop_type: "basil",
        variety: "Genovese",
        scientific_name: "Ocimum basilicum 'Genovese'",
        growth_stage: "vegetative",
        duration_days: { min: 14, max: 21, optimal: 18 },

        environment: {
            temperature_c: { min: 22, max: 28, optimal: 25, night_drop: 4 },
            humidity_pct: { min: 55, max: 70, optimal: 62 },
            co2_ppm: { min: 800, max: 1200, optimal: 1000 },
            vpd_kpa: { min: 0.7, max: 1.1, optimal: 0.9 },
            air_velocity_ms: { min: 0.3, max: 0.8, optimal: 0.5 }
        },

        lighting: {
            spectral_recipe_id: "SPR-BASIL-VEG",
            ppfd_umol: { min: 300, max: 450, optimal: 380 },
            dli_mol: { min: 15, max: 22, optimal: 18 },
            photoperiod_h: 16,
            spectrum: {
                blue_450nm_pct: 25,
                red_660nm_pct: 55,
                far_red_730nm_pct: 8,
                white_pct: 12
            },
            ratio_red_blue: 2.2,
            light_compensation_point: 30,
            light_saturation_point: 800
        },

        nutrition: {
            nutrient_recipe_id: "NUT-BASIL-VEG",
            ec_ms: { min: 1.4, max: 1.8, optimal: 1.6 },
            ph: { min: 5.8, max: 6.4, optimal: 6.0 },
            water_temp_c: { min: 18, max: 23, optimal: 20 },

            macronutrients: {
                N: { min: 140, max: 180, optimal: 160 },
                P: { min: 45, max: 65, optimal: 55 },
                K: { min: 180, max: 240, optimal: 210 },
                Ca: { min: 100, max: 140, optimal: 120 },
                Mg: { min: 35, max: 50, optimal: 42 },
                S: { min: 45, max: 65, optimal: 55 }
            },

            micronutrients: {
                Fe: { optimal: 3.2 },
                Mn: { optimal: 0.8 },
                Zn: { optimal: 0.4 },
                Cu: { optimal: 0.08 },
                B: { optimal: 0.5 },
                Mo: { optimal: 0.08 }
            }
        },

        targets: {
            leaf_area_index: 3.5,
            fresh_weight_g: 50,
            dry_weight_g: 5,
            relative_growth_rate: 0.15,
            chlorophyll_spad: 42
        },

        source: "Cornell CEA + Wageningen Research",
        validated: true,
        validation_date: new Date("2025-12-01"),
        created_at: new Date(),
        updated_at: new Date()
    },

    // --- BASILIC FINITION ---
    {
        recipe_id: "BASIL-FIN-001",
        crop_type: "basil",
        variety: "Genovese",
        scientific_name: "Ocimum basilicum 'Genovese'",
        growth_stage: "finishing",
        duration_days: { min: 5, max: 7, optimal: 6 },

        environment: {
            temperature_c: { min: 20, max: 24, optimal: 22, night_drop: 5 },
            humidity_pct: { min: 50, max: 65, optimal: 58 },
            co2_ppm: { min: 600, max: 900, optimal: 750 },
            vpd_kpa: { min: 0.9, max: 1.3, optimal: 1.1 },
            air_velocity_ms: { min: 0.5, max: 1.0, optimal: 0.7 }
        },

        lighting: {
            spectral_recipe_id: "SPR-BASIL-FIN",
            ppfd_umol: { min: 400, max: 550, optimal: 480 },
            dli_mol: { min: 18, max: 26, optimal: 22 },
            photoperiod_h: 14,
            spectrum: {
                blue_450nm_pct: 30,
                red_660nm_pct: 50,
                far_red_730nm_pct: 5,
                white_pct: 15
            },
            ratio_red_blue: 1.67,
            light_compensation_point: 35,
            light_saturation_point: 1000
        },

        nutrition: {
            nutrient_recipe_id: "NUT-BASIL-FIN",
            ec_ms: { min: 1.0, max: 1.4, optimal: 1.2 },
            ph: { min: 5.6, max: 6.0, optimal: 5.8 },
            water_temp_c: { min: 17, max: 20, optimal: 18 },

            macronutrients: {
                N: { min: 80, max: 110, optimal: 95 },
                P: { min: 35, max: 50, optimal: 42 },
                K: { min: 150, max: 200, optimal: 175 },
                Ca: { min: 90, max: 120, optimal: 105 },
                Mg: { min: 30, max: 42, optimal: 36 },
                S: { min: 35, max: 50, optimal: 42 }
            },

            micronutrients: {
                Fe: { optimal: 2.5 },
                Mn: { optimal: 0.6 },
                Zn: { optimal: 0.35 },
                Cu: { optimal: 0.06 },
                B: { optimal: 0.4 },
                Mo: { optimal: 0.06 }
            }
        },

        targets: {
            fresh_weight_g: 80,
            essential_oil_pct: 0.8,
            brix_degree: 6,
            aroma_score: 8,
            shelf_life_days: 10
        },

        notes: "Stress hydrique leger et reduction N pour concentration aromes",
        source: "Cornell CEA + Fluence Photomorphogenesis Guide",
        validated: true,
        validation_date: new Date("2025-12-01"),
        created_at: new Date(),
        updated_at: new Date()
    }
]);

// ============================================================================
// RECETTES LAITUE BUTTERHEAD
// ============================================================================

db.plant_recipes.insertMany([
    {
        recipe_id: "LETTUCE-BH-VEG-001",
        crop_type: "lettuce",
        variety: "Butterhead",
        scientific_name: "Lactuca sativa var. capitata",
        growth_stage: "vegetative",
        duration_days: { min: 21, max: 28, optimal: 24 },

        environment: {
            temperature_c: { min: 16, max: 22, optimal: 19, night_drop: 4 },
            humidity_pct: { min: 60, max: 75, optimal: 68 },
            co2_ppm: { min: 600, max: 1000, optimal: 800 },
            vpd_kpa: { min: 0.6, max: 1.0, optimal: 0.8 },
            air_velocity_ms: { min: 0.2, max: 0.5, optimal: 0.35 }
        },

        lighting: {
            spectral_recipe_id: "SPR-LETTUCE-VEG",
            ppfd_umol: { min: 200, max: 350, optimal: 280 },
            dli_mol: { min: 12, max: 18, optimal: 15 },
            photoperiod_h: 16,
            spectrum: {
                blue_450nm_pct: 20,
                red_660nm_pct: 60,
                far_red_730nm_pct: 5,
                white_pct: 15
            },
            ratio_red_blue: 3.0,
            light_compensation_point: 20,
            light_saturation_point: 600
        },

        nutrition: {
            nutrient_recipe_id: "NUT-LETTUCE-VEG",
            ec_ms: { min: 1.2, max: 1.6, optimal: 1.4 },
            ph: { min: 5.8, max: 6.4, optimal: 6.1 },
            water_temp_c: { min: 16, max: 20, optimal: 18 },

            macronutrients: {
                N: { min: 120, max: 160, optimal: 140 },
                P: { min: 40, max: 55, optimal: 48 },
                K: { min: 160, max: 220, optimal: 190 },
                Ca: { min: 110, max: 150, optimal: 130 },
                Mg: { min: 35, max: 50, optimal: 42 },
                S: { min: 40, max: 55, optimal: 48 }
            },

            micronutrients: {
                Fe: { optimal: 3.0 },
                Mn: { optimal: 0.7 },
                Zn: { optimal: 0.35 },
                Cu: { optimal: 0.07 },
                B: { optimal: 0.45 },
                Mo: { optimal: 0.07 }
            }
        },

        targets: {
            head_weight_g: 200,
            leaf_count: 25,
            tip_burn_risk: "low",
            nitrate_mg_kg: { max: 2500 }
        },

        source: "Cornell CEA Leafy Greens Protocol",
        validated: true,
        validation_date: new Date("2025-12-01"),
        created_at: new Date(),
        updated_at: new Date()
    }
]);

// ============================================================================
// RECETTES SPECTRALES (reference croisee)
// ============================================================================

db.spectral_recipes.drop();
db.createCollection("spectral_recipes");
db.spectral_recipes.createIndex({ "spectral_recipe_id": 1 }, { unique: true });

db.spectral_recipes.insertMany([
    {
        spectral_recipe_id: "SPR-BASIL-GERM",
        name: "Basil Germination Spectrum",
        description: "Blue-dominant spectrum for germination - promotes compact growth",
        ppfd_range: { min: 100, max: 200 },
        spectrum: {
            blue_450nm: { pct: 35, wavelength_nm: 450 },
            red_660nm: { pct: 45, wavelength_nm: 660 },
            far_red_730nm: { pct: 5, wavelength_nm: 730 },
            white: { pct: 15, cct_kelvin: 4000 }
        },
        ratio_red_blue: 1.29,
        phytochrome_ratio: 0.85,
        application: ["germination", "seedling"],
        created_at: new Date()
    },
    {
        spectral_recipe_id: "SPR-BASIL-VEG",
        name: "Basil Vegetative Spectrum",
        description: "Balanced spectrum for vegetative growth",
        ppfd_range: { min: 300, max: 450 },
        spectrum: {
            blue_450nm: { pct: 25, wavelength_nm: 450 },
            red_660nm: { pct: 55, wavelength_nm: 660 },
            far_red_730nm: { pct: 8, wavelength_nm: 730 },
            white: { pct: 12, cct_kelvin: 4000 }
        },
        ratio_red_blue: 2.2,
        phytochrome_ratio: 0.80,
        application: ["vegetative"],
        created_at: new Date()
    },
    {
        spectral_recipe_id: "SPR-BASIL-FIN",
        name: "Basil Finishing Spectrum",
        description: "High-blue spectrum for aroma concentration",
        ppfd_range: { min: 400, max: 550 },
        spectrum: {
            blue_450nm: { pct: 30, wavelength_nm: 450 },
            red_660nm: { pct: 50, wavelength_nm: 660 },
            far_red_730nm: { pct: 5, wavelength_nm: 730 },
            white: { pct: 15, cct_kelvin: 5000 }
        },
        ratio_red_blue: 1.67,
        phytochrome_ratio: 0.88,
        application: ["finishing", "pre-harvest"],
        notes: "Increased blue promotes secondary metabolite production",
        created_at: new Date()
    },
    {
        spectral_recipe_id: "SPR-LETTUCE-VEG",
        name: "Lettuce Vegetative Spectrum",
        description: "Red-dominant spectrum for leaf expansion",
        ppfd_range: { min: 200, max: 350 },
        spectrum: {
            blue_450nm: { pct: 20, wavelength_nm: 450 },
            red_660nm: { pct: 60, wavelength_nm: 660 },
            far_red_730nm: { pct: 5, wavelength_nm: 730 },
            white: { pct: 15, cct_kelvin: 4000 }
        },
        ratio_red_blue: 3.0,
        phytochrome_ratio: 0.82,
        application: ["vegetative"],
        created_at: new Date()
    }
]);

// ============================================================================
// FAO KC COEFFICIENTS (Coefficients culturaux)
// ============================================================================

db.fao_kc_coefficients.drop();
db.createCollection("fao_kc_coefficients");

db.fao_kc_coefficients.insertMany([
    {
        crop: "basil",
        source: "FAO Irrigation Paper 56",
        stages: {
            initial: { kc: 0.35, duration_pct: 15 },
            development: { kc: 0.70, duration_pct: 25 },
            mid_season: { kc: 1.05, duration_pct: 40 },
            late_season: { kc: 0.90, duration_pct: 20 }
        },
        notes: "Adjusted for controlled environment",
        created_at: new Date()
    },
    {
        crop: "lettuce",
        source: "FAO Irrigation Paper 56",
        stages: {
            initial: { kc: 0.45, duration_pct: 20 },
            development: { kc: 0.60, duration_pct: 30 },
            mid_season: { kc: 1.00, duration_pct: 35 },
            late_season: { kc: 0.95, duration_pct: 15 }
        },
        notes: "Butterhead variety",
        created_at: new Date()
    }
]);

print("");
print("=".repeat(70));
print("MongoDB plant_recipes initialized successfully!");
print("=".repeat(70));
print("Collections created:");
print("  - plant_recipes: " + db.plant_recipes.countDocuments() + " documents");
print("  - spectral_recipes: " + db.spectral_recipes.countDocuments() + " documents");
print("  - fao_kc_coefficients: " + db.fao_kc_coefficients.countDocuments() + " documents");
print("");
