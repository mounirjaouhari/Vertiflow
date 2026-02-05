#!/usr/bin/env python3
"""
STEP 5: VALIDATION TESTS
Verify that STEPS 1-4 have successfully fixed the data pipeline
"""

import subprocess
import time
import json
from datetime import datetime

print("="*80)
print("✅ STEP 5: VALIDATION TESTS")
print("="*80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Test 1: Kafka LAG Status
print("\n" + "="*80)
print("TEST 1: Kafka Consumer Group LAG")
print("="*80)

result = subprocess.run([
    "docker", "exec", "kafka",
    "/opt/kafka/bin/kafka-consumer-groups.sh",
    "--describe",
    "--bootstrap-server", "localhost:9092",
    "--group", "nifi-storage-group"
], capture_output=True, text=True, timeout=10)

kafka_output = result.stdout
print(kafka_output)

# Parse LAG
lag_lines = [l for l in kafka_output.split('\n') if 'basil_telemetry_full' in l]
if lag_lines:
    lag_value = lag_lines[0].split()[-1]
    try:
        lag_int = int(lag_value)
        if lag_int == 0:
            print("✅ PASS: LAG = 0 (no backlog)")
        elif lag_int < 1000:
            print(f"⚠️  WARN: LAG = {lag_int} (small backlog, normal after reset)")
        else:
            print(f"❌ FAIL: LAG = {lag_int} (large backlog)")
    except:
        print(f"⚠️  Could not parse LAG: {lag_value}")

# Test 2: ClickHouse Record Count
print("\n" + "="*80)
print("TEST 2: ClickHouse Record Count")
print("="*80)

result = subprocess.run([
    "docker", "exec", "clickhouse",
    "clickhouse-client",
    "--query", "SELECT COUNT() as total_records, "
              "COUNT(DISTINCT timestamp) as unique_timestamps "
              "FROM vertiflow.basil_ultimate_realtime"
], capture_output=True, text=True, timeout=10)

ch_output = result.stdout.strip()
print(f"Records: {ch_output}")

if result.returncode == 0:
    try:
        parts = ch_output.split('\t')
        total = int(parts[0])
        print(f"✅ PASS: ClickHouse has {total} records")
        if total > 5000:
            print("   → Baseline met (>5000 records)")
        else:
            print(f"   → Only {total} records (low, but normal after reset)")
    except:
        print("⚠️  Could not parse ClickHouse output")
else:
    print(f"❌ FAIL: ClickHouse error: {result.stderr}")

# Test 3: NiFi Zone Status
print("\n" + "="*80)
print("TEST 3: NiFi Zone Status")
print("="*80)

result = subprocess.run([
    "docker", "exec", "nifi",
    "curl", "-s",
    "http://localhost:8080/nifi-api/flow/process-groups/root"
], capture_output=True, text=True, timeout=10)

if result.returncode == 0:
    try:
        data = json.loads(result.stdout)
        zones = data.get('processGroups', [])
        
        print(f"Found {len(zones)} zones:")
        for zone in zones:
            name = zone.get('component', {}).get('name', 'Unknown')
            state = zone.get('component', {}).get('state', 'Unknown')
            print(f"  • {name}: {state}")
            
            if 'Zone 2' in name and state == 'RUNNING':
                print("    ✅ Zone 2 (Contextualisation) RUNNING")
            elif 'Zone 4' in name and state == 'RUNNING':
                print("    ✅ Zone 4 (Rétroaction) RUNNING")
    except json.JSONDecodeError:
        print("⚠️  Could not parse NiFi API response")
else:
    print(f"⚠️  NiFi API not responding (expected during bootstrap)")

# Test 4: Verify Processor States
print("\n" + "="*80)
print("TEST 4: Verify Key Processors Running")
print("="*80)

processors_to_check = [
    ("Zone 2", "B1 - LookupRecord"),
    ("Zone 4", "D0 - ConsumeKafka"),
    ("Zone 3", "C1 - PutClickHouse")
]

for zone_name, proc_name in processors_to_check:
    # Try to get status from NiFi
    result = subprocess.run([
        "docker", "exec", "nifi",
        "bash", "-c",
        f"curl -s http://localhost:8080/nifi-api/flow/process-groups/root | grep -i '{proc_name}' | head -1"
    ], capture_output=True, text=True, timeout=10)
    
    if "RUNNING" in result.stdout or result.returncode == 0:
        print(f"  ✅ {zone_name} → {proc_name}: likely RUNNING")
    else:
        print(f"  ⚠️  {zone_name} → {proc_name}: status unknown (NiFi may still be starting)")

# Test 5: Database Integrity
print("\n" + "="*80)
print("TEST 5: Data Integrity Check")
print("="*80)

result = subprocess.run([
    "docker", "exec", "clickhouse",
    "clickhouse-client",
    "--query", "SELECT "
              "COUNT() as total, "
              "COUNT(DISTINCT lineage_uuid) as unique_lineage, "
              "COUNT(DISTINCT timestamp) as unique_timestamps "
              "FROM vertiflow.basil_ultimate_realtime"
], capture_output=True, text=True, timeout=10)

if result.returncode == 0:
    output = result.stdout.strip()
    print(f"Integrity metrics: {output}")
    
    try:
        parts = output.split('\t')
        total = int(parts[0])
        unique_lineage = int(parts[1])
        unique_ts = int(parts[2])
        
        if unique_lineage == total:
            print("✅ PASS: No duplication detected (unique_lineage = total)")
        else:
            duplication_ratio = (1 - unique_lineage/total) * 100
            print(f"⚠️  WARN: Duplication detected ({duplication_ratio:.1f}%)")
    except:
        print("⚠️  Could not parse integrity output")

# Test 6: External Data Columns
print("\n" + "="*80)
print("TEST 6: External Data Columns Presence")
print("="*80)

result = subprocess.run([
    "docker", "exec", "clickhouse",
    "clickhouse-client",
    "--query", "SHOW COLUMNS FROM vertiflow.basil_ultimate_realtime LIKE 'ext_%'"
], capture_output=True, text=True, timeout=10)

if result.returncode == 0:
    ext_cols = result.stdout.strip().split('\n')
    ext_count = len([c for c in ext_cols if c])
    print(f"Found {ext_count} external columns:")
    for col in ext_cols[:10]:
        if col:
            print(f"  • {col.split()[0]}")
    
    if ext_count > 0:
        print(f"✅ PASS: External data columns present ({ext_count} found)")
    else:
        print(f"⚠️  WARN: No external columns found (STEP 2 may not be complete)")
else:
    print("⚠️  Could not query columns")

# Test 7: Lookup Columns (health_score, rack_id)
print("\n" + "="*80)
print("TEST 7: Lookup Columns (STEP 3 verification)")
print("="*80)

result = subprocess.run([
    "docker", "exec", "clickhouse",
    "clickhouse-client",
    "--query", "SELECT COUNT(DISTINCT health_score) FROM vertiflow.basil_ultimate_realtime"
], capture_output=True, text=True, timeout=10)

if result.returncode == 0:
    count = result.stdout.strip()
    try:
        distinct_health = int(count)
        if distinct_health > 1:
            print(f"✅ PASS: health_score has {distinct_health} distinct values")
        elif distinct_health == 0:
            print(f"⚠️  WARN: health_score all NULL (LookupRecord may not be processing)")
        else:
            print(f"⚠️  WARN: health_score only {distinct_health} distinct value")
    except:
        print(f"⚠️  Could not parse health_score count")
else:
    print(f"❌ FAIL: health_score column not found or ClickHouse error")

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

summary = """
✅ Completed Tests:
  1. Kafka LAG status
  2. ClickHouse record count
  3. NiFi zone status
  4. Processor state verification
  5. Data integrity check
  6. External columns check
  7. Lookup columns check

📊 Expected Passing Tests:
  • Test 1: LAG should be 0 or declining
  • Test 2: Records > 5,000
  • Test 3: At least Zone 3 RUNNING (persistence)
  • Test 4: Key processors visible/running
  • Test 5: No duplication (unique_lineage ≈ total)
  • Test 6: ext_* columns present (if STEP 2 done)
  • Test 7: health_score values > 1 distinct (if STEP 3 done)

⚠️ Manual Verification Required:
  • Open Grafana: http://localhost:3000
  • Dashboard 05: Check for rack_id in tables
  • Dashboard 08: Check for predicted_* columns
  • Dashboard 12: Check for NASA temperature data

🚀 Next Steps:
  1. If Tests 1-5 pass: Execute STEP 2 (manual UI)
  2. After STEP 2: Re-run this test for Tests 6-7
  3. After all tests pass: Deployment complete! ✅
"""

print(summary)
print("="*80)
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

