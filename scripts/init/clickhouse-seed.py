from clickhouse_driver import Client
from dotenv import load_dotenv
import os
import random
import uuid
from datetime import datetime, timedelta

# ============================
# LOAD ENV
# ============================
load_dotenv()


client = Client(
    host=os.getenv("CLICKHOUSE_HOST"),
    port=int(os.getenv("CLICKHOUSE_PORT")),
    user=os.getenv("CLICKHOUSE_USER"),
    password=os.getenv("CLICKHOUSE_PASSWORD"),
    database=os.getenv("CLICKHOUSE_DB"),
)


# ============================
# CONFIG
# ============================
N_ROWS = 500      # 👈 change this
BATCH_SIZE = 100

# ============================
# HELPERS
# ============================
def r(a, b, d=2):
    return round(random.uniform(a, b), d)

def ri(a, b):
    return random.randint(a, b)

# ============================
# DATA GENERATION
# ============================
rows = []

base_time = datetime.now()

for i in range(N_ROWS):
    rows.append((
        # I. IDENTIFICATION & GEO
        base_time + timedelta(seconds=i),
        "VERT-MAROC-01",
        f"830-AB-{ri(100,999)}",
        r(32.5, 32.7, 4),
        r(-7.7, -7.5, 4),
        random.choice(["ZONE_A", "ZONE_B", "ZONE_C"]),
        "R01",
        1,
        "MOD-001",
        "BATCH-C",
        "Ocimum basilicum Genovese",
        f"X{ri(1,20)}-Y{ri(1,20)}",
        r(100, 150),

        # II. NUTRITION
        ri(150,200), ri(30,60), ri(180,240), ri(140,180), ri(40,60),
        ri(50,80), r(2.0,3.0), r(0.6,1.0), r(0.4,0.8),
        r(0.05,0.15), r(0.2,0.5), r(0.02,0.08),
        ri(25,45), r(0.01,0.05), r(1.6,2.2),

        # III. LIGHT & PHOTOSYNTHESIS
        ri(280,350), ri(40,60), ri(800,1000), r(0.5,0.8),
        ri(16,20), r(12,16), ri(14,18), r(0.7,0.85), r(20,25),
        ri(800,900), r(2.5,3.5), r(0.8,1.5), r(0.4,0.7),
        ri(70,90), "LED_RECIPE_A",

        # IV. GROWTH
        r(130,160), r(16,22), r(2.5,4.0), r(0.35,0.5),
        r(0.07,0.1), r(4.5,6.5), r(25,32), r(0.5,0.7),
        ri(20,30), ri(500,600), "Végétatif",
        r(2.0,3.5), base_time.date() + timedelta(days=ri(10,20)),
        r(5.8,6.5), ri(150,220),

        # V. HEALTH
        r(0.85,1.0), ri(30,60), r(0.3,0.5), r(0.08,0.15),
        r(0.05,0.1), r(1.0,1.6), r(3.5,5.0), r(2.0,3.5),
        ri(10,20), r(-1.0,0.0), r(0.01,0.05),
        ri(10,30), r(2.0,3.5), r(0.7,0.9), r(0.7,0.9),

        # VI. ENVIRONMENT
        r(20,26), ri(60,75), r(0.7,1.0), r(0.2,0.5),
        ri(1000,1025), ri(55,75),
        r(18,22), ri(65,80), ri(380,450),
        r(18,24), r(14,18), ri(50,65),
        1, r(2.0,4.5), ri(30,50), r(0.05,0.2),

        # VII. WATER & ROOT
        r(18,24), r(5.6,6.5), r(7.0,9.0), r(1.0,1.5),
        r(3.0,5.0), r(0.5,0.8), r(0.9,1.2), ri(90000,130000),
        r(0.6,0.8), r(0.05,0.12), r(0.2,0.4), r(0.1,0.2),
        ri(200,280), r(1.3,1.8), r(0.1,0.25),

        # VIII. ECONOMICS
        r(0.1,0.2), r(3.0,4.5), ri(90,130),
        r(1.0,1.5), r(1.2,1.6), 1,
        r(0.8,1.0), r(0.3,0.5), r(2.0,3.0), r(0.7,0.9),

        # IX. HARDWARE
        r(0.01,0.05), r(1.0,2.0), ri(30,45),
        r(0.1,0.3), r(0.8,1.0),
        0, 0, ri(10,15), r(0.005,0.02), r(0.9,1.0),

        # X. AI & DECISION
        "AUTO", r(0.02,0.1), r(16,22), r(0.05,0.2),
        "IRRIG_STD", r(0.85,0.98),
        uuid.uuid4().hex,
        "SIG-2025-A",
        "Premium",
        0,

        # XI. REFERENCE TARGETS
        180, 45, 210, 160, 48,
        24, 3.5, 2.8, 4.5, 110000,
        16, 620, 12, 50, 70,

        # XII. TRACEABILITY
        "IoT",
        "SENS-BASIL-01",
        "v1.3",
        r(0.9,1.0),
        0,
        base_time.date() - timedelta(days=ri(10,30)),
        r(0.05,0.2),
        uuid.uuid4()
    ))

# ============================
# INSERT
# ============================
query = "INSERT INTO vertiflow.basil_ultimate_realtime VALUES"

client.execute(query, rows)
print(f"✅ Inserted {N_ROWS} rows")

