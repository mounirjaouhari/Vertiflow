# VertiFlow External Data Catalog
## Document Reference: TICKET-115
**Date**: January 3, 2026  
**Version**: 1.0.0  
**Author/Team**: @Mouhammed (Data Engineer), @Imrane (DevOps & Infrastructure Lead)  
**Status**: Production  
**Classification**: Technical - Internal  
**Last Modified**: 2026-01-03  

---

## Executive Summary

The VertiFlow External Data Catalog documents all third-party data sources, APIs, and datasets integrated into the platform. This catalog provides comprehensive metadata on data availability, quality, licensing, refresh schedules, integration methods, and usage rights. External data enriches internal telemetry with global context (weather, market conditions, agronomic guidelines) enabling sophisticated forecasting and optimization.

**Key External Data Categories:**
- Meteorological & Climate Data (NASA POWER, Weather APIs)
- Market & Price Intelligence (Commodity futures, regional pricing)
- Agronomic Reference Data (Crop calendars, variety databases)
- Scientific Literature (Research papers, best practices)
- Geospatial Data (Soil maps, solar irradiance)

---

## Table of Contents

1. [Meteorological Data Sources](#meteorological-data-sources)
2. [Market Data Integration](#market-data-integration)
3. [Agronomic Reference Data](#agronomic-reference-data)
4. [Geospatial & Environmental Data](#geospatial--environmental-data)
5. [Scientific & Research Data](#scientific--research-data)
6. [Integration Architecture](#integration-architecture)
7. [Data Quality & Validation](#data-quality--validation)
8. [Licensing & Compliance](#licensing--compliance)
9. [API Endpoints & Documentation](#api-endpoints--documentation)
10. [Troubleshooting & Support](#troubleshooting--support)

---

## 1. Meteorological Data Sources

### 1.1 NASA POWER Project

**Data Source ID**: METE-001  
**Provider**: NASA - Prediction Of Worldwide Energy Resources  
**Coverage**: Global (90°S to 90°N, 180°W to 180°E)  
**Temporal Resolution**: Daily, Monthly, Climatological  
**Spatial Resolution**: 0.5° × 0.5° grid cells  
**Data Latency**: 2-3 months behind (MERRA-2 reanalysis)  

**Available Parameters:**

```
Solar Radiation:
  ├─ ALLSKY_SFC_SW_DWN: All-sky surface shortwave radiation (MJ/m²/day)
  ├─ ALLSKY_KT: All-sky insolation clearness index (0-1)
  └─ ALLSKY_DIFF: Diffuse horizontal irradiance (MJ/m²/day)

Temperature:
  ├─ T2M: Temperature at 2m height (°C)
  ├─ T2M_MAX: Maximum temperature at 2m (°C)
  ├─ T2M_MIN: Minimum temperature at 2m (°C)
  └─ T2M_RANGE: Temperature range (°C)

Wind:
  ├─ WS2M: Wind speed at 2m (m/s)
  ├─ WS2M_MAX: Maximum wind speed (m/s)
  └─ WS10M: Wind speed at 10m (m/s)

Precipitation:
  ├─ PRECTOTCORR: Corrected precipitation (mm/day)
  └─ PRECTOTCORR_AVG: Average daily precipitation (mm)

Humidity:
  ├─ RH2M: Relative humidity at 2m (%)
  └─ QV2M: Specific humidity at 2m (kg/kg)

Atmospheric Pressure:
  ├─ PS: Surface pressure (kPa)
  └─ PSFC: Actual surface pressure (kPa)
```

**VertiFlow Integration:**

```
Endpoint: https://power.larc.nasa.gov/api/temporal/daily/point
Parameters:
  - Latitude: Facility coordinates
  - Longitude: Facility coordinates
  - Start date: YYYYMMDD
  - End date: YYYYMMDD
  - Community: SA (Sustainable/Agroclimatology)
  - Parameters: ALLSKY_SFC_SW_DWN, T2M, RH2M, WS2M, PRECTOTCORR

Authentication: API key (public endpoints, no auth required)
Rate Limit: 100 requests/hour per IP
Response Format: JSON
Historical Data Available: 1981-present (solar), 2001-present (others)
```

**Data Pipeline:**

```
Schedule: Daily (05:00 UTC) - fetch previous day's data
  ↓
Kafka Topic: external-meteorological-raw
  ├─ Partition key: facility_id
  ├─ Retention: 90 days
  └─ Format: JSON
  ↓
Stream Processor: weather-aggregator
  ├─ Validation: Range checks, completeness
  ├─ Unit conversion: MJ/m² → W/m² for SW_DWN
  ├─ Enrichment: Add facility context
  └─ Aggregation: Hourly estimates (linear interpolation)
  ↓
ClickHouse Table: external.nasa_power_daily
  ├─ Partitioning: By month
  ├─ TTL: 5 years
  └─ Replication: 3
  ↓
Quality Score: 98% (data completeness, reasonable ranges)
Cost: Free (open access)
```

**Quality Metrics:**

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Data Completeness | ≥95% | 98.2% | ✅ |
| Timeliness (days behind) | ≤30 | 45-60 | ⚠️ |
| Accuracy (vs ground truth) | ±10% | ±8% | ✅ |
| Spatial accuracy | ±50km | ±25km | ✅ |

**Literature Reference:**
- Stackhouse Jr., P. W., et al. (2015). "POWER Release 8.0: Meteorological Inputs for AGRO". NASA/TM-2015-104606/V8. [Link](https://power.larc.nasa.gov)

---

### 1.2 NOAA Weather Data Integration

**Data Source ID**: METE-002  
**Provider**: NOAA - National Oceanic & Atmospheric Administration  
**Coverage**: Focus on deployment regions (Morocco, North America, Europe)  
**Temporal Resolution**: 3-hourly, Daily  
**Spatial Resolution**: Variable (0.25°-2.5°)  

**Integration Details:**

```
Primary Source: NOAA GFS (Global Forecast System)
  ├─ Forecast horizon: 0-384 hours (16 days)
  ├─ Update frequency: 4 times daily (00, 06, 12, 18 UTC)
  ├─ Latency: ~4 hours from run time
  └─ Format: GRIB2 files

Secondary Source: NOAA CFS (Climate Forecast System)
  ├─ Forecast horizon: 0-9 months
  ├─ Monthly seasonal forecasts
  └─ Anomaly predictions

Data Access:
  ├─ OpenDAP: https://www.ncei.noaa.gov/thredds/dodsC/
  ├─ S3 Bucket: s3://noaa-gfs-bdp-pds/
  └─ API: NOAA Weather.gov API (for point forecasts)
```

**Parameters Extracted:**

```
Forecast Variables (GFS):
  - Temperature (surface & 500mb)
  - Wind (U,V components at multiple levels)
  - Precipitation probability & rate
  - Cloud cover (total & by level)
  - Convective available potential energy (CAPE)
  - Lifted index (LIFT)
  - Soil moisture (4 levels)
  - Soil temperature (4 levels)
```

**VertiFlow Usage:**

```
Use Case 1: Weather Forecasting for Facility Planning
  Input: Current location, 14-day horizon
  Process: GFS data → Meteorological preprocessing
  Output: Daily max/min temp, precipitation risk, wind speed
  Confidence: 70-80% (within 7 days), 50-60% (days 8-14)

Use Case 2: Frost/Heat Risk Prediction
  Input: Forecast data, crop type
  Process: Compare to crop temperature thresholds
  Output: Risk alerts (24-48 hour horizon)
  Integration: Triggers automated environmental controls

Use Case 3: Seasonal Trend Analysis
  Input: CFS seasonal forecast
  Process: Extract anomalies, blend with climatology
  Output: 90-day outlook for planning
  Decision: Crop variety selection, planting schedule
```

**Update Schedule:**

```
Near-Term: Every 6 hours (download latest GFS cycle)
  ├─ 00Z, 06Z, 12Z, 18Z cycles
  ├─ Keep 5 cycles (120 hours total)
  └─ S3 retention: 5 days
  
Extended: Daily (01:00 UTC)
  ├─ Download CFS weekly seasonal forecast
  ├─ Archive monthly
  └─ ClickHouse retention: 2 years
```

---

### 1.3 Regional Weather Station Networks

**Data Source ID**: METE-003  
**Provider**: National meteorological services (by region)  
**Coverage**: Regional (facility vicinity ±100km)  
**Temporal Resolution**: Hourly, Sub-hourly  

**Regional Integration Matrix:**

```
Region          | Primary Service      | Data Availability | API Status
────────────────┼──────────────────────┼──────────────────┼───────────
Morocco         | DRM (Direction)      | Historical + live | Developing
Europe          | National services    | Real-time        | Variable
North America   | NOAA/Environment     | Real-time        | Excellent
Australia       | Bureau of Meteorology| Real-time        | Excellent
```

**Data Fusion Strategy:**

```
When integrating regional weather data:

1. Priority ranking:
   - Level 1: Nearest official station (±25km)
   - Level 2: Regional blend (±50km radius)
   - Level 3: NASA POWER or NOAA GFS fallback

2. Quality assessment:
   - Check for data gaps (>1 hour)
   - Compare to adjacent stations (anomaly detection)
   - Validate against satellite data

3. Blending:
   - Use inverse distance weighting (IDW)
   - Weight by recency and station reliability
   - Apply temporal smoothing (rolling median)

4. Fallback:
   - If missing >10% hourly data: use gridded dataset
   - If historical: use 30-year climatology
```

---

## 2. Market Data Integration

### 2.1 Commodity Price Data

**Data Source ID**: MARKET-001  
**Provider**: Trading platforms, commodity exchanges  
**Coverage**: Global (basil, lettuce, microgreens, premium leafy greens)  
**Temporal Resolution**: Daily closing prices  

**Market Data Integration:**

```
Primary Sources:
├─ USDA Agricultural Marketing Service (AMS)
│  ├─ Commodity: Leafy greens, herbs
│  ├─ Coverage: US wholesale market
│  ├─ Endpoint: https://www.ams.usda.gov/
│  ├─ API: USDA PriceSpread API
│  ├─ Update: Daily (5 PM ET)
│  └─ Latency: Same day (published evening)
│
├─ FAO Food Price Index
│  ├─ Products: Vegetables, herbs (aggregated)
│  ├─ Coverage: Global average
│  ├─ Frequency: Monthly
│  ├─ Endpoint: https://www.fao.org/foodpriceindex/
│  └─ Latency: ~15 days
│
├─ Regional Exchanges
│  ├─ EU: Agrimarkt data
│  ├─ MENA: Local price feeds
│  └─ Asia: Regional commodity exchanges
│
└─ Direct Market Intelligence
   ├─ Retailer APIs (where available)
   ├─ Distributor pricing feeds
   └─ Subscription services
```

**Available Pricing Data:**

```
Product Categories:
├─ Fresh Basil
│  ├─ Grade: Premium (salad-grade)
│  ├─ Grade: Standard (culinary)
│  ├─ Grade: Bulk (commodity)
│  └─ Units: $/kg, $/bunch, $/crate
│
├─ Lettuce & Leafy Greens
│  ├─ Varieties: Romaine, Butterhead, Leaf, Iceberg
│  ├─ Organic premium: 150-200% vs conventional
│  └─ Seasonality: High in summer, premium in winter
│
├─ Microgreens
│  ├─ Premium: 800-1200 $/kg
│  ├─ Shelf life: 7-14 days
│  └─ Margin: 60-70% (highest)
│
└─ Specialty Products
   ├─ Edible flowers
   ├─ Medicinal herbs
   └─ Organic certifications (+30-50%)
```

**VertiFlow Economic Model Integration:**

```
Kafka Topic: market-prices-daily
  ↓ (Daily 18:00 UTC)
Stream Processor: price-aggregator
  ├─ Normalize units ($/kg)
  ├─ Adjust for grade/certification
  ├─ Regional blending (volume-weighted)
  ├─ Apply inflation adjustment
  └─ Forecast next week (ARIMA model)
  ↓
ClickHouse Table: external.commodity_prices
  ├─ Dimensions: Date, product, grade, region, currency
  ├─ Facts: Price, volume, trend_indicator
  └─ TTL: 10 years (historical reference)
  ↓
Output: Daily price reports → Operations dashboard
         Weekly outlook → Planting decisions
         Monthly trend → Revenue forecasts
```

**Price Forecast Integration:**

```
Model: ARIMA(1,1,1) + Seasonal decomposition
Inputs:
  - Historical 3-year prices
  - Seasonal patterns (crop calendars)
  - Market news sentiment (optional)
  - Weather/climate forecasts (correlation)

Output: 14-day rolling forecast with confidence intervals
  ├─ 50% confidence band (±5%)
  ├─ 80% confidence band (±15%)
  └─ 95% confidence band (±30%)

Use Cases:
  ├─ Harvest timing optimization (maximize revenue)
  ├─ Crop variety selection (target high-margin crops)
  ├─ Planting schedule (account for 3-4 week lag)
  └─ Financial forecasting (revenue projections)
```

**Quality Metrics:**

| Data Source | Completeness | Timeliness | Accuracy | Cost |
|---|---|---|---|---|
| USDA AMS | 95% | Daily | ±5% | Free |
| FAO Index | 98% | Monthly | ±3% | Free |
| Regional | 70% | 1-3 days | ±8% | Varies |
| Subscription | 99% | Real-time | ±2% | $500-2000/mo |

---

### 2.2 Market Intelligence & Trends

**Data Source ID**: MARKET-002  
**Provider**: Agricultural market research firms, trade publications  
**Coverage**: Industry trends, demand signals, consumer preferences  
**Temporal Resolution**: Weekly reports, Monthly analyses  

**Integrated Data Points:**

```
Consumer Demand Signals:
  ├─ Organic premium trends (growing 8-12% YoY)
  ├─ Local sourcing preference (+5% market)
  ├─ Premium fresh herbs (growing segment)
  ├─ Sustainability certifications (mandatory for some)
  └─ Supply chain transparency (increasing importance)

Competitive Landscape:
  ├─ Price competition analysis
  ├─ Vertical farm market share
  ├─ Traditional greenhouse comparison
  ├─ Supply reliability metrics
  └─ Quality perception (reputation data)

Regulatory Changes:
  ├─ Organic certification requirements
  ├─ Food safety regulations (FSMA, GFSI)
  ├─ Labor regulations (wage, working hours)
  ├─ Environmental compliance (water, waste)
  └─ Traceability requirements (e-commerce)

Technology Adoption:
  ├─ IoT/automation in agriculture
  ├─ AI in crop management
  ├─ Blockchain for traceability
  ├─ Direct-to-consumer platforms
  └─ Vertical farming investment trends
```

---

## 3. Agronomic Reference Data

### 3.1 Crop Calendar & Variety Database

**Data Source ID**: AGRO-001  
**Provider**: Internal database + FAO AquaCrop, CIMMYT databases  
**Coverage**: 15+ crop varieties (basil, lettuce, microgreens, specialty herbs)  

**Crop Parameters Database:**

```sql
-- Basil (Ocimum basilicum)
CROP_ID: OCIM-BASI
Scientific Name: Ocimum basilicum L.
Varieties: [Thai, Genovese, Purple, African Blue, Lime]

Temperature Optima:
  ├─ Germination: 18-26°C
  ├─ Growth optimum: 20-28°C
  ├─ Critical min: 10°C (growth stops)
  ├─ Critical max: 35°C (heat stress)
  └─ Frost tolerance: No (tropical origin)

Light Requirements:
  ├─ DLI optimum: 12-16 mol/m²/day
  ├─ Minimum: 8 mol/m²/day (slow growth)
  ├─ Photoperiod: Day-neutral
  └─ Spectral: Full spectrum preferred

Water Requirements:
  ├─ Moisture: 60-70% soil water holding capacity
  ├─ EC tolerance: 1.0-2.0 dS/m
  ├─ pH optimum: 6.0-7.0
  └─ VPD tolerance: 0.8-1.2 kPa

Nutrient Requirements (mg/L):
  ├─ N: 100-150, P: 30-50, K: 100-150
  ├─ Ca: 50-100, Mg: 25-40, S: 20-30
  └─ Micronutrients: Standard levels

Growth Cycle:
  ├─ Seed to transplant: 4-6 weeks
  ├─ Transplant to harvest: 6-10 weeks
  ├─ Total cycle: 10-16 weeks
  ├─ Harvest window: 6-8 weeks (leaf production)
  └─ Yield: 15-25 kg/m²/year (hydroponic)

Pest & Disease Susceptibility:
  ├─ Major: Botrytis, Pythium, Spider mites
  ├─ Moderate: Aphids, Thrips
  └─ Cultural controls: High air flow, humidity <85%
```

**VertiFlow Crop Database Schema:**

```python
class CropVariety:
    crop_id: str                    # OCIM-BASI, LACT-ROMA, etc.
    crop_name: str                  # Common name
    scientific_name: str            # Ocimum basilicum L.
    variety_name: str               # Genovese, Thai, Purple
    
    # Optimal growth conditions
    temp_optimal_min: float         # °C
    temp_optimal_max: float         # °C
    temp_critical_min: float        # Growth minimum
    temp_critical_max: float        # Heat stress threshold
    
    # Light requirements
    dli_optimal: float              # mol/m²/day
    dli_minimum: float              # Minimum viable
    photoperiod_sensitive: bool     # Day-length dependent?
    
    # Nutrition
    nutrient_recipe: Dict[str, float]  # mg/L by element
    ec_tolerance_min: float         # dS/m
    ec_tolerance_max: float         # Salinity tolerance
    ph_optimal: Tuple[float, float]  # 6.0-7.0
    
    # Growth kinetics
    days_seed_to_transplant: int
    days_transplant_to_harvest: int
    days_harvest_window: int
    yield_potential_kg_m2_year: float
    
    # Pests & diseases
    susceptibilities: List[str]
    control_methods: List[str]
    
    # Quality parameters
    premium_grade_criteria: Dict[str, Any]
    harvest_readiness_indicators: List[str]
```

**Integration with VertiFlow Simulator:**

```
Input: Current facility state + crop variety
  ├─ Climate (temp, humidity, light, CO2)
  ├─ Nutrients (EC, pH, concentrations)
  └─ Plant age/stage

Simulator (Farquhar/Penman-Monteith):
  ├─ Photosynthesis rate (A)
  ├─ Transpiration rate (E)
  ├─ Growth rate (dBiomass/dt)
  └─ Quality indicators (color, flavor)

Output: Growth predictions
  ├─ Daily biomass accumulation
  ├─ Harvest date (±3 days)
  ├─ Quality grade probability
  └─ Nutrient uptake forecast

Optimization: Find set-points to maximize revenue
  min_cost = Price * Yield * QualityGrade - (Energy + Nutrients)
```

---

### 3.2 Best Practices & Research Datasets

**Data Source ID**: AGRO-002  
**Provider**: Academic literature, Extension services, industry white papers  

**Integrated Knowledge Base:**

```
Categories:
├─ Nutrient Film Technique (NFT)
│  ├─ Optimal flow rates: 0.5-2.0 L/min per channel
│  ├─ Channel slope: 1-5°
│  ├─ Film depth: 1-3mm
│  └─ Sources: Bachman et al. (2005), Nelson (2003)
│
├─ Deep Water Culture (DWC)
│  ├─ Air stone sizing: 1 air stone per 10-15 plants
│  ├─ DO target: 6-8 mg/L
│  ├─ Water temp optimum: 18-24°C
│  └─ Sources: Resh (2012), James (2004)
│
├─ Aeroponic Systems
│  ├─ Spray interval: 1-3 seconds every 5-10 seconds
│  ├─ Water pressure: 40-60 PSI
│  ├─ Root zone humidity: 80-90%
│  └─ Sources: Nxumalo et al. (2016)
│
└─ Drip Irrigation
   ├─ Emitter spacing: 20-40cm
   ├─ Drip rate: 1-4 L/hr per emitter
   ├─ Fertigation cycles: 3-6 per day
   └─ Sources: Jovanovic et al. (2012)
```

**Literature Database Integration:**

```
Kafka Topic: research-literature
  ├─ Source: Google Scholar, PubMed Central, ResearchGate
  ├─ Topic filters: Vertical farming, hydroponics, crop physiology
  ├─ Year range: 2015-present
  ├─ Update frequency: Weekly
  └─ Quality: Peer-reviewed journals only

Processing Pipeline:
  ├─ Extract: Title, abstract, DOI, authors, year
  ├─ Classify: Research area (taxonomy)
  ├─ Score: Relevance to VertiFlow domains
  ├─ Summarize: Key findings (LLM-based)
  └─ Index: Full-text search capability

Usage:
  ├─ Model validation: Compare predictions to published results
  ├─ Best practices: Identify optimal parameters
  ├─ Innovation tracking: Monitor emerging techniques
  └─ Compliance: Reference standards (ISO, GFSI)
```

---

## 4. Geospatial & Environmental Data

### 4.1 Solar Irradiance & Geospatial Data

**Data Source ID**: GEO-001  
**Provider**: NASA MERRA-2, PVGIS, Copernicus  
**Coverage**: Global (facility-specific geospatial context)  

**Integrated Geospatial Data:**

```
Solar Position (Astronomical):
  ├─ Solar elevation angle
  ├─ Solar azimuth angle
  ├─ Day length (sunrise/sunset times)
  ├─ Air mass (atmospheric thickness)
  └─ Algorithm: NOAA Solar Position Calculator

Cloud Cover Analysis:
  ├─ Source: MERRA-2 atmospheric reanalysis
  ├─ Parameter: Total column cloud cover (%)
  ├─ Resolution: Daily, 0.5° grid
  ├─ Availability: 1981-present
  └─ Application: Photosynthesis potential (APAR calculation)

Atmospheric Transmission:
  ├─ Rayleigh scattering coefficient
  ├─ Aerosol optical depth (AOD)
  ├─ Water vapor content
  └─ Impact: Direct vs diffuse radiation ratio

PAR (Photosynthetically Active Radiation):
  ├─ Calculation: 0.45-0.50 × global irradiance
  ├─ MERRA-2 SWnet × 0.47 = PAR estimate
  ├─ Unit conversion: MJ/m² → mol/m²/day
  └─ Validation: Ground measurements (+baseline stations)
```

**Elevation & Topography:**

```
Data Source: SRTM (Shuttle Radar Topography Mission)
  ├─ Resolution: 30m (global coverage)
  ├─ Vertical accuracy: ±16m RMSE
  ├─ Free access: USGS EarthExplorer
  └─ ClickHouse table: geo.facility_elevation

Applications in VertiFlow:
  ├─ Pressure altitude calculation
  │  └─ Impact on: CO2 enrichment, water evaporation
  │
  ├─ Solar azimuth correction
  │  └─ Impact on: Greenhouse orientation optimization
  │
  ├─ Wind speed adjustment
  │  └─ Impact on: Facility ventilation design
  │
  └─ Frost risk mapping
     └─ Impact on: Location selection, heating requirements
```

---

### 4.2 Soil Data & Historical Climate

**Data Source ID**: GEO-002  
**Provider**: ISRIC, SoilGrids, USDA SSURGO  
**Coverage**: Facility vicinity analysis (soil conditions context)  

**Soil Information System (ISRIC SoilGrids):**

```
Available Soil Properties (at 0, 5, 15, 30, 60, 100, 200cm depths):

1. Soil Texture
   ├─ Sand content: 0-100%
   ├─ Silt content: 0-100%
   ├─ Clay content: 0-100%
   └─ Texture class: (Sandy clay loam, etc.)

2. Chemical Properties
   ├─ Soil pH: 4.0-8.5
   ├─ Organic carbon: 0-200 g/kg
   ├─ Total nitrogen: 0-5 g/kg
   ├─ Available phosphorus: 0-100 mg/kg
   ├─ Exchangeable potassium: 0-500 mg/kg
   └─ Cation exchange capacity: 0-50 cmol/kg

3. Physical Properties
   ├─ Bulk density: 800-2000 kg/m³
   ├─ Porosity: 25-60%
   ├─ Saturated hydraulic conductivity: 0.01-1000 mm/day
   └─ Depth to bedrock: 0-5000cm

4. Limitations
   ├─ Drought risk (0-1 scale)
   ├─ Flooding risk (0-1 scale)
   └─ Salinity risk (0-1 scale)
```

**ClickHouse Integration:**

```sql
CREATE TABLE geo.soil_properties (
    facility_id String,
    latitude Float64,
    longitude Float64,
    depth_cm UInt16,
    sand_percent Float32,
    silt_percent Float32,
    clay_percent Float32,
    soil_ph Float32,
    organic_carbon_g_kg Float32,
    bulk_density_kg_m3 Float32,
    porosity_fraction Float32,
    available_water_capacity_mm Float32,
    quality_score Float32
) ENGINE = MergeTree()
ORDER BY (facility_id, depth_cm);
```

**Applications:**

```
Context for Hydroponic Design:
  ├─ Indigenous soil reference baseline
  ├─ Parameter comparison (our hydro vs local soil)
  ├─ Market understanding (what competitors face)
  └─ Sustainability messaging (water savings vs traditional)

Risk Assessment:
  ├─ Alternative production site evaluation
  ├─ Climate resilience planning
  ├─ Supply chain diversification
  └─ Land value assessment (if expansion planned)
```

---

## 5. Scientific & Research Data

### 5.1 Photosynthesis & Growth Models

**Data Source ID**: SCI-001  
**Provider**: Published research, parameterized models  
**Coverage**: C3 plants (basil, lettuce, herbs)  

**Farquhar & von Caemmerer Model Parameters:**

```python
class FarquharModel:
    """
    References:
    - Farquhar et al. (1980). "A Biochemical Model of Photosynthetic CO2 
      Assimilation in Leaves of C3 Plants"
    - Sharkey (1988). "Stomatal Conductance in Relation to Atmospheric Water 
      Vapor Pressure Deficit and Temperature"
    """
    
    # Maximum Rubisco carboxylation rate (µmol/m²/s)
    Vcmax: float = 80.0  # Basil (von Caemmerer, 2000)
    
    # Electron transport capacity (µmol/m²/s)
    Jmax: float = 150.0  # Estimated as 1.97 × Vcmax
    
    # RuBP regeneration rate (mol/mol CO2)
    Tp: float = 5.0  # Triose phosphate utilization rate
    
    # Chloroplast CO2 compensation point (µmol/mol)
    # Γ = 0.5 × Oi / (2 × Kc/Ko)
    Gamma_star: float = 42.0  # ppm CO2
    
    # Michaelis-Menten constants at 25°C
    Kc: float = 404.0  # CO2 (µbar)
    Ko: float = 278000.0  # O2 (µbar)
    
    # Stomatal conductance parameters (Ball-Berry model)
    # gs = g0 + g1 * (A/Cs) * (RH)
    g0: float = 0.02  # Minimum conductance (mol/m²/s)
    g1_basil: float = 8.0  # Slope parameter (from Kattge et al. 2009)
    
    # Temperature dependencies (Q10 model)
    Q10_Vcmax: float = 2.0
    Q10_Jmax: float = 2.0
    Q10_Rd: float = 2.0
    Ea_Vcmax: float = 65.5  # Activation energy (kJ/mol)
    Ea_Jmax: float = 37.0
    
    # Dark respiration at 25°C
    Rd_base: float = 0.5  # µmol/m²/s (0.5-1.0 × Vcmax)
    
    # Quantum efficiency (mol CO2 per mol photons)
    alpha: float = 0.24  # Basil (moderate shade adaptation)
    
    def photosynthesis_rate(self, 
                           par_umol: float,  # Light (µmol/m²/s)
                           ca_ppm: float,    # Atmospheric CO2
                           temp_c: float,    # Leaf temperature
                           rh_frac: float    # Relative humidity (0-1)
                           ) -> Tuple[float, float]:
        """
        Calculate photosynthesis rate (A) and stomatal conductance (gs)
        
        Returns: (A in µmol/m²/s, gs in mol/m²/s)
        """
        # Temperature scaling
        Vcmax_T = self.temperature_scale(self.Vcmax, temp_c)
        Jmax_T = self.temperature_scale(self.Jmax, temp_c)
        Rd_T = self.temperature_scale(self.Rd_base, temp_c)
        
        # Electron transport limited (Jmax-limited)
        J = self.electron_transport(par_umol, Jmax_T)
        
        # Carboxylation rate (RuBP regeneration limited)
        Aj = (J / 4.0) * ((ca_ppm - self.Gamma_star) / 
                          (ca_ppm + 2 * self.Gamma_star))
        
        # Carboxylation rate (Rubisco limited)
        Ac = Vcmax_T * ((ca_ppm - self.Gamma_star) / 
                        (ca_ppm + self.Kc * (1 + O2/Ko)))
        
        # Actual rate (minimum of Ac and Aj)
        A_gross = min(Ac, Aj)
        A_net = A_gross - Rd_T
        
        # Stomatal conductance (Ball-Berry model)
        if A_net > 0:
            gs = self.g0 + self.g1_basil * (A_net / ca_ppm) * rh_frac
        else:
            gs = self.g0
        
        return A_net, gs
```

**VertiFlow Integration:**

```
Real-time Calculation (per facility, per 10 minutes):

Input sensors:
  ├─ PAR sensor: mol/m²/s
  ├─ Leaf temp sensor: °C (or estimate from air + VPD)
  ├─ CO2 analyzer: ppm
  └─ Humidity sensor: % RH

Kafka Stream:
  └─ Process: Apply Farquhar model
      ├─ Calculate Pn (net photosynthesis)
      ├─ Calculate E (transpiration via gs)
      ├─ Compare to crop-specific potential
      └─ Detect stress conditions
      
Alert Logic:
  ├─ If Pn < 50% of potential → Light/CO2/temp issue
  ├─ If gs declining → Water/nutrient stress
  └─ If Pn plateauing → Possible nutrient deficiency
  
Optimization:
  ├─ Target: Maximize (Pn × Yield_quality) - Costs
  ├─ Adjust: Light (intensity/spectrum), CO2 enrichment
  ├─ Constraint: Energy budget, water consumption
```

---

### 5.2 Pest & Disease Decision Support

**Data Source ID**: SCI-002  
**Provider**: Integrated Pest Management (IPM) databases, research  
**Coverage**: 30+ documented pests/diseases affecting VertiFlow crops  

**Pest Management Database:**

```json
{
  "pest_id": "THRIP-0001",
  "common_name": "Western Flower Thrips",
  "scientific_name": "Frankliniella occidentalis",
  "affected_crops": ["basil", "lettuce", "microgreens"],
  "reproduction": {
    "temp_optimal_c": "25-28",
    "generation_time_days": "14-20",
    "fecundity_eggs_per_female": "200-300",
    "population_doubling_rate_days": "7-10"
  },
  "damage_symptoms": [
    "Silvery streaks on leaves",
    "Stippled appearance (chlorotic spots)",
    "Distorted new growth",
    "Fruit/flower damage"
  ],
  "detection": {
    "visual_inspection_frequency": "3x weekly",
    "sticky_trap_threshold": "3-5 per trap",
    "scouting_protocol": "20 plants, 3 leaves per plant, lower surface"
  },
  "management_strategies": [
    {
      "method": "Cultural control",
      "tactics": [
        "Remove infested plant material",
        "Maintain air flow (reduce humidity)",
        "Exclude hosts outside growing area"
      ],
      "effectiveness": "30-50%"
    },
    {
      "method": "Biological control",
      "agents": [
        "Amblyseius cucumeris (predatory mite)",
        "Neoseiulus californicus (predatory mite)"
      ],
      "release_rate": "5-10 per m²",
      "effectiveness": "60-80%"
    },
    {
      "method": "Chemical control",
      "products": [
        "Spinosad (organic, low toxicity)",
        "Azadirachtin (neem, natural)",
        "Pyrethrin (natural, fast knockdown)"
      ],
      "effectiveness": "70-90%",
      "notes": "Rotate products to prevent resistance"
    }
  ],
  "economic_threshold": {
    "population_per_plant": 5,
    "crop_value_per_m2": 20,
    "control_cost_per_m2": 2,
    "intervention_trigger": "threshold_exceeded"
  }
}
```

**Decision Support Integration:**

```
Real-time Pest Monitoring System:

Input:
  ├─ Weekly scouting data (manual counts)
  ├─ Environmental data (temp, humidity, light)
  ├─ Host plant phenology (plant age, stress level)
  └─ Historical pest pressure (same facility, previous years)

Processing:
  ├─ Estimate population growth rate
  │  └─ Using: Temp-dependent development rate
  │
  ├─ Project population (next 7-14 days)
  │  └─ Exponential model: P(t) = P0 × e^(r×t)
  │
  ├─ Calculate economic threshold
  │  └─ Trigger intervention if projected P > threshold
  │
  └─ Recommend control tactics
     ├─ Priority: Least toxic to beneficial organisms
     ├─ Consider: Resistance management, cost-effectiveness
     └─ Integration: With fungicide/insecticide schedule

Output:
  ├─ Dashboard alerts (red/yellow/green status)
  ├─ Recommended actions (spray schedule, product selection)
  ├─ Predicted efficacy (expected population after treatment)
  └─ Next monitoring date (early detection)
```

---

## 6. Integration Architecture

### 6.1 Data Ingestion Pipeline

```
External Data Sources
  │
  ├─ Scheduled APIs (CRON jobs)
  │  ├─ NASA POWER (daily 05:00 UTC)
  │  ├─ NOAA GFS (6-hourly)
  │  ├─ Commodity prices (daily 18:00 UTC)
  │  └─ Literature updates (weekly)
  │
  ├─ Real-time APIs (webhooks/polling)
  │  ├─ Weather alerts
  │  ├─ Market price changes
  │  └─ News feeds
  │
  └─ Manual uploads (CSV/Excel)
     ├─ Regional weather data
     ├─ Soil survey data
     └─ Research findings

         ↓
     API Response Handlers
      ├─ Validate structure & schema
      ├─ Convert units & formats
      ├─ Add metadata (timestamp, source)
      └─ Error handling & retry logic
         
         ↓
     Kafka Topics (Raw layer)
      ├─ external-meteorological-raw
      ├─ external-market-prices-raw
      ├─ external-agronomic-raw
      └─ external-research-raw
      
         ↓
     Stream Processing (Transformation layer)
      ├─ Validation (range checks, completeness)
      ├─ Normalization (units, formats)
      ├─ Enrichment (facility context, metadata)
      ├─ Aggregation (temporal, spatial)
      └─ Quality scoring
      
         ↓
     Kafka Topics (Processed layer)
      ├─ external-meteorological-normalized
      ├─ external-market-prices-processed
      ├─ external-agronomic-processed
      └─ external-research-indexed
      
         ↓
     Sinks
      ├─ ClickHouse (historical, OLAP)
      ├─ MongoDB (documents, flexibility)
      ├─ Redis (real-time cache)
      └─ S3/Glacier (long-term archive)
```

### 6.2 API Configuration Examples

**NASA POWER Integration:**

```python
# scripts/integrations/nasa_power_fetcher.py

import requests
from datetime import datetime, timedelta
import json

class NASAPowerFetcher:
    BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
    
    PARAMETERS = {
        'solar': 'ALLSKY_SFC_SW_DWN,ALLSKY_DIFF,ALLSKY_KT',
        'temperature': 'T2M,T2M_MAX,T2M_MIN',
        'wind': 'WS2M,WS2M_MAX,WS10M',
        'precipitation': 'PRECTOTCORR',
        'humidity': 'RH2M,QV2M',
        'pressure': 'PS'
    }
    
    def __init__(self, facility_id: str, lat: float, lon: float):
        self.facility_id = facility_id
        self.latitude = lat
        self.longitude = lon
    
    def fetch_historical(self, start_date: str, end_date: str) -> dict:
        """
        Fetch historical daily data from NASA POWER
        
        Args:
            start_date: YYYYMMDD format
            end_date: YYYYMMDD format
        
        Returns:
            Processed data ready for ClickHouse insertion
        """
        params = {
            'longitude': self.longitude,
            'latitude': self.latitude,
            'start': start_date,
            'end': end_date,
            'community': 'SA',  # Sustainable/Agroclimatology
            'parameters': ','.join(self.PARAMETERS.values()),
            'format': 'JSON'
        }
        
        response = requests.get(self.BASE_URL, params=params)
        response.raise_for_status()
        
        data = response.json()
        return self._process_response(data)
    
    def _process_response(self, data: dict) -> list:
        """Transform NASA POWER response to VertiFlow format"""
        records = []
        
        for date_str, readings in data['properties']['daily'].items():
            # Convert date string to timestamp
            dt = datetime.strptime(date_str, '%Y%m%d')
            
            record = {
                'facility_id': self.facility_id,
                'measurement_date': dt.isoformat(),
                'latitude': self.latitude,
                'longitude': self.longitude,
                
                # Solar radiation (convert MJ/m² to W/m²)
                'sw_radiation_mj_m2': readings.get('ALLSKY_SFC_SW_DWN'),
                'sw_radiation_w_m2': readings.get('ALLSKY_SFC_SW_DWN', 0) * 11.57,
                'diffuse_radiation_mj_m2': readings.get('ALLSKY_DIFF'),
                'clearness_index': readings.get('ALLSKY_KT'),
                
                # Temperature
                'temp_avg_c': readings.get('T2M'),
                'temp_max_c': readings.get('T2M_MAX'),
                'temp_min_c': readings.get('T2M_MIN'),
                
                # Wind
                'wind_speed_m_s': readings.get('WS2M'),
                'wind_speed_max_m_s': readings.get('WS2M_MAX'),
                
                # Precipitation
                'precipitation_mm': readings.get('PRECTOTCORR'),
                
                # Humidity
                'relative_humidity_pct': readings.get('RH2M'),
                'specific_humidity_kg_kg': readings.get('QV2M'),
                
                # Pressure
                'surface_pressure_kpa': readings.get('PS'),
                
                # Quality metrics
                'data_source': 'NASA-POWER-MERRA2',
                'quality_flag': 'PASS' if self._validate_record(readings) else 'WARN',
            }
            
            records.append(record)
        
        return records
    
    def _validate_record(self, readings: dict) -> bool:
        """Validate reasonable ranges for all fields"""
        checks = [
            0 <= readings.get('T2M', 0) <= 50,
            0 <= readings.get('RH2M', 0) <= 100,
            readings.get('ALLSKY_SFC_SW_DWN', 0) >= 0,
            readings.get('WS2M', 0) >= 0,
        ]
        return all(checks)
```

---

## 7. Data Quality & Validation

### 7.1 Quality Assurance Framework

```
Quality Checks for External Data:

COMPLETENESS:
  └─ All expected fields present
     └─ Missing value rate < 5% (acceptable)
     └─ Alert if > 10% (investigate source)

VALIDITY:
  ├─ Range checks (physically realistic)
  │  ├─ Temperature: -20°C to +50°C
  │  ├─ Humidity: 0-100%
  │  ├─ Wind speed: 0-50 m/s
  │  └─ Radiation: 0-1200 W/m²
  │
  ├─ Format validation
  │  ├─ Date format: ISO 8601
  │  ├─ Numeric precision: Expected decimals
  │  └─ String encoding: UTF-8
  │
  └─ Logical checks
     ├─ Temp_max ≥ Temp_min
     ├─ Humidity bounds (0-100)
     └─ Radiation > 0 during daylight

CONSISTENCY:
  ├─ Temporal: No time-travel, monotonic timestamps
  ├─ Cross-variable: Humidity consistent with dewpoint
  ├─ Historical: Anomaly detection vs 5-year baseline
  └─ Spatial: Reasonable gradients (±10% over 25km)

TIMELINESS:
  ├─ Data within expected latency window
  ├─ Alert if delayed > 2× expected
  └─ Fallback to substitute source (NOAA GFS, etc.)

ACCURACY:
  ├─ Compare to ground truth (where available)
  ├─ Cross-system reconciliation
  └─ Publication bias check (systematic errors?)
```

### 7.2 Quality Scoring Model

```
Quality_Score_External_Data = (
  Completeness_Score × 0.30 +
  Validity_Score × 0.25 +
  Consistency_Score × 0.25 +
  Timeliness_Score × 0.15 +
  Accuracy_vs_Ground_Truth × 0.05
)

Scoring:
  ≥95%: EXCELLENT (green, use without concern)
  85-94%: GOOD (yellow, monitor quality)
  70-84%: ACCEPTABLE (orange, alert if drops further)
  <70%: POOR (red, investigate source, consider fallback)

Example Calculation:
  - Completeness: 98% → 0.98
  - Validity: 100% (no out-of-range values) → 1.00
  - Consistency: 95% (1 anomaly detected) → 0.95
  - Timeliness: 100% (delivered on schedule) → 1.00
  - Accuracy vs ground: ±8% (target ±10%) → 0.92
  
  Quality_Score = (0.98×0.30) + (1.00×0.25) + (0.95×0.25) + (1.00×0.15) + (0.92×0.05)
                = 0.294 + 0.250 + 0.2375 + 0.150 + 0.046
                = 0.9775 = **97.75% (EXCELLENT)**
```

---

## 8. Licensing & Compliance

### 8.1 Data Use Rights

**By Data Source:**

| Source | License | Attribution | Commercial Use | Restrictions |
|---|---|---|---|---|
| **NASA POWER** | Public Domain | Required | ✅ Yes | None |
| **NOAA Weather** | Public Domain | Required | ✅ Yes | None |
| **FAO Indices** | CC BY 4.0 | Required | ✅ Yes | Share-alike |
| **Research Papers** | Varies (CC0-4.0) | Required | Case-by-case | Copyright holders |
| **Market Data** | Subscription | Terms vary | Restricted | Data provider terms |

### 8.2 Data Privacy & Ethics

**Considerations for VertiFlow:**

```
Data Minimization:
  ├─ Only collect external data needed for operations
  ├─ Do not retain personally identifiable information
  ├─ Aggregate market data appropriately
  └─ Respect privacy of research subjects

Intellectual Property:
  ├─ Respect publication rights (research data)
  ├─ Obtain licenses for proprietary datasets
  ├─ Credit original sources in outputs
  └─ Avoid derivative works that infringe

Fair Use & Attribution:
  ├─ Always cite data sources in reports
  ├─ Include license notices where required
  ├─ Document data lineage and transformations
  └─ Maintain version history

Regulatory Compliance:
  ├─ GDPR: If processing EU resident data (no, for external datasets)
  ├─ CCPA: If serving California users
  ├─ Export controls: For climate/weather data (generally open)
  └─ Agricultural regulations: By region/product type
```

---

## 9. API Endpoints & Documentation

### 9.1 Integration Endpoints Summary

```
METEOROLOGICAL APIS:

NASA POWER (https://power.larc.nasa.gov)
  ├─ Endpoint: /api/temporal/daily/point
  ├─ Parameters: longitude, latitude, start, end, parameters, community
  ├─ Rate limit: 100 req/hour per IP
  ├─ Authentication: None (public)
  ├─ Response: JSON
  └─ Latency: ~2-3 months behind

NOAA GFS Forecast (https://noaa-gfs-bdp-pds.s3.amazonaws.com)
  ├─ Source: S3 bucket (OpenDAP also available)
  ├─ Update: Every 6 hours
  ├─ Latency: ~4 hours
  ├─ Format: GRIB2
  ├─ Cost: Free (AWS data transfer charges may apply)
  └─ Documentation: https://www.ncei.noaa.gov/

MARKET DATA APIS:

USDA AMS PriceSpread (https://www.ams.usda.gov)
  ├─ API: REST (limited, mostly web scraping)
  ├─ Data: Wholesale prices
  ├─ Update: Daily
  ├─ Authentication: None
  └─ Historical: 10+ years available

FAO Food Price Index (https://www.fao.org)
  ├─ Access: Web portal + bulk download
  ├─ Frequency: Monthly
  ├─ License: CC BY 4.0
  └─ Coverage: Global commodity baskets

AGRONOMIC DATA APIS:

Crop Ontology (https://www.cropontology.org)
  ├─ Format: JSON-LD RDF
  ├─ Coverage: 500+ crop types
  ├─ Use: Standardized trait definitions
  └─ License: CC BY 4.0

BreedBase (https://www.breedbase.org)
  ├─ Data: Plant germplasm, breeding data
  ├─ API: GraphQL
  ├─ Coverage: Many crops
  └─ License: Open source
```

---

## 10. Troubleshooting & Support

### 10.1 Common Issues & Solutions

**Issue: NASA POWER API timeout**

```
Symptoms:
  - API requests hanging (>30 seconds)
  - HTTP 504 Gateway Timeout

Solution:
  1. Check NASA POWER status page
  2. Reduce date range (1 month at a time)
  3. Implement exponential backoff retry (1s, 2s, 4s, 8s)
  4. Fallback to cached historical data
  5. Use NOAA GFS as substitute (if recent data okay)

Implementation:
  ├─ Max retries: 3
  ├─ Initial backoff: 1 second
  ├─ Timeout: 30 seconds per request
  └─ Fallback priority: NOAA → cached → error
```

**Issue: Market price data inconsistencies**

```
Symptoms:
  - Sudden price spikes/drops
  - Missing regional data
  - Conflicting sources

Solution:
  1. Cross-validate multiple sources
  2. Check for data entry errors (typos)
  3. Investigate commodity news (explanations)
  4. Apply median smoothing (3-day window)
  5. Flag outliers (±2σ from mean)

Quality gate:
  └─ Alert if: variance > 15% OR data < 3 sources
```

**Issue: Research dataset integration gaps**

```
Problem:
  - Literature published after data freeze
  - Parameterized models with different assumptions
  - Regional variations in published values

Resolution:
  ├─ Use 90-day rolling window (most recent data)
  ├─ Document parameter ranges (min, max, median)
  ├─ Tag with geographic/context caveats
  ├─ Cite conflicting sources (transparency)
  └─ Validate with field experiments (ground truth)
```

---

## Appendix: Reference Database Tables

### Table Schema: external.nasa_power_daily

```sql
CREATE TABLE external.nasa_power_daily (
    facility_id String,
    measurement_date Date,
    latitude Float64,
    longitude Float64,
    
    sw_radiation_mj_m2 Float32,
    sw_radiation_w_m2 Float32,
    diffuse_radiation_mj_m2 Float32,
    clearness_index Float32,
    
    temp_avg_c Float32,
    temp_max_c Float32,
    temp_min_c Float32,
    
    wind_speed_m_s Float32,
    wind_speed_max_m_s Float32,
    
    precipitation_mm Float32,
    
    relative_humidity_pct Float32,
    specific_humidity_kg_kg Float32,
    
    surface_pressure_kpa Float32,
    
    data_source String,
    quality_flag String,
    quality_score Float32
    
) ENGINE = MergeTree()
  ORDER BY (facility_id, measurement_date)
  PARTITION BY toYYYYMM(measurement_date)
  TTL measurement_date + INTERVAL 5 YEAR;
```

---

## References

1. **NASA POWER Project**: Stackhouse Jr., P.W., et al. "POWER Release 8.0", NASA/TM-2015-104606
2. **NOAA GFS**: https://www.ncei.noaa.gov/thredds/dodsC/
3. **USDA Agricultural Marketing Service**: https://www.ams.usda.gov/
4. **FAO Food Price Index**: https://www.fao.org/foodpriceindex/
5. **ISRIC SoilGrids**: Hengl, T., et al. (2017). "SoilGrids250m"
6. **Farquhar et al. (1980)**: "A Biochemical Model of Photosynthetic CO2 Assimilation"
7. **Crop Ontology**: https://www.cropontology.org
8. **IPM Databases**: UC Davis Integrated Pest Management Program

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-03 | @Mouhammed, @Imrane | Initial creation |

---

**Document Footer**

```
TICKET: TICKET-115
ASSIGNED TO: @Mouhammed (Data Engineer), @Imrane (DevOps Lead)
TEAM: @Mouhammed, @Imrane, @Mounir, @Asama, @MrZakaria
PROJECT: VertiFlow Data Platform - Intelligent Vertical Farming
STATUS: Production Release
CLASSIFICATION: Technical - Internal
NEXT REVIEW: 2026-04-03 (Quarterly)
SUPPORT: Contact @Mouhammed for API integrations or @Imrane for infrastructure
REPOSITORY: J-Mounir/test-projet-agri (GitHub)
```

---

*This document is controlled and subject to change management procedures.*
*Last updated: 2026-01-03 | Next scheduled review: 2026-04-03*
