# STEP 2 EXECUTION - Add ConsumeKafka Processors Zone 1

**Objective**: Add 3× ConsumeKafka processors to consume external API data (NASA, Weather, AirQuality)

## Problem Context

**Current State**:
- Zone 0: 9 processors publish to Kafka topics
  - vertiflow.external.nasa (NASA POWER solar radiation, temperature)
  - vertiflow.external.weather (Open-Meteo: temperature, humidity, wind)
  - vertiflow.external.airquality (OpenAQ: PM2.5, O3, NO2, CO)
- Zone 1: Only consumes `vertiflow.ingestion.raw` ❌
- **Result**: 11 external columns missing, 599k+ messages accumulated

**Solution**: Add 3 ConsumeKafka processors to bridge Zone 0 → Zone 1

## Execution Steps

### Option A: Manual UI (5-15 minutes)

#### 1. Open NiFi UI
```
https://localhost:8443/nifi
Username/Password: (from docker-compose or env)
```

#### 2. Navigate to Zone 1
- Left panel: Expand process groups
- Click "Zone 1 - Ingestion & Validation"

#### 3. Create 3 New ConsumeKafka Processors

**Processor 1: ConsumeKafka - NASA POWER**

a) Right-click canvas → Add Processor
b) Search: "ConsumeKafka_2_6"  
c) Configure:
   - **Name**: `A4 - NASA POWER Consumer`
   - **Properties**:
     - `Bootstrap Servers`: `kafka:9092`
     - `Topic Names(s)`: `vertiflow.external.nasa`
     - `Group ID`: `nifi-external-group-nasa`
     - `Session Timeout`: `30 sec`
   - **Apply** → **Close**

d) Connect:
   - Drag "success" output to existing "MergeContent" processor
   - Relationship: **success** → auto-routed

e) Start processor (right-click → Start)

**Processor 2: ConsumeKafka - Weather**

Repeat above with:
- **Name**: `A5 - Open-Meteo Weather Consumer`
- **Topic**: `vertiflow.external.weather`
- **Group ID**: `nifi-external-group-weather`

**Processor 3: ConsumeKafka - Air Quality**

Repeat above with:
- **Name**: `A6 - OpenAQ Air Quality Consumer`
- **Topic**: `vertiflow.external.airquality`
- **Group ID**: `nifi-external-group-airquality`

#### 4. Verify All 3 are RUNNING
- All 3 should show **red circle** = RUNNING
- Check for errors in logs (Logs icon)

#### 5. Monitor Data Flow
- Watch counters increase (top-right of each processor)
- Expected: input counters should show messages

### Option B: NiFi REST API (Automated - Requires Auth Token)

```bash
#!/bin/bash

NIFI_URL="https://localhost:8443"
ZONE_1_GROUP_ID="<zone-1-id>"  # Get from UI or API
TOKEN="<auth-token>"  # Requires login first

# Create 3 ConsumeKafka processors
for topic in nasa weather airquality; do
  curl -X POST "$NIFI_URL/nifi-api/process-groups/$ZONE_1_GROUP_ID/processors" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d @- << PAYLOAD
{
  "revision": {"version": 0, "clientId": "nifi-script"},
  "component": {
    "type": "org.apache.nifi.processors.kafka.pubsub.ConsumeKafka_2_6",
    "name": "A4 - $topic Consumer",
    "config": {
      "properties": {
        "bootstrap.servers": "kafka:9092",
        "topic": "vertiflow.external.$topic",
        "group.id": "nifi-external-group-$topic"
      }
    }
  }
}
PAYLOAD
done
```

### Option C: Automated Programmatic (Modify flow.xml.gz directly)

⚠️ **Warning**: This requires careful XML manipulation. Already attempted in STEP 3-4.

```python
# Would need to:
# 1. Extract flow.xml.gz
# 2. Parse XML (ElementTree)
# 3. Find Zone 1 processGroup ID
# 4. Add 3 new <processor> elements with ConsumeKafka config
# 5. Add 3 new <connection> elements linking to MergeContent
# 6. Recompress and deploy
# 7. Restart NiFi

# See /tmp/modify_nifi_flow.py for reference
```

## Expected Outcomes

### After STEP 2 Complete:

**Kafka Consumer Groups**:
```
GROUP                           TOPIC                    LAG
nifi-external-group-nasa        vertiflow.external.nasa  0
nifi-external-group-weather     vertiflow.external.weather 0
nifi-external-group-airquality  vertiflow.external.airquality 0
```

**ClickHouse Columns Added**:
- From NASA: `ext_temp_nasa`, `ext_humidity_nasa`, `ext_solar_radiation`
- From Weather: `ext_temperature_api`, `ext_humidity_api`, `ext_wind_speed_api`
- From AirQuality: `ext_pm25`, `ext_o3`, `ext_no2`, `ext_co`

**Grafana Dashboard 12** (Meteo Externe):
- Should display NASA and Open-Meteo data
- Temperature comparison: internal vs external
- Solar radiation for growth modeling

## Troubleshooting

| Issue | Diagnosis | Solution |
|-------|-----------|----------|
| Processors won't start | Check Kafka connectivity | Verify Kafka running: `docker ps \| grep kafka` |
| No data flowing | Check topic existence | `docker exec kafka /opt/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092` |
| LAG not decreasing | Processor paused | Right-click → Start (if stopped) |
| Queue backing up | MergeContent timeout | Adjust merge criteria or batch size |
| NiFi web UI crashes | Out of memory | Increase XMX: `docker update --memory 8g nifi` |

## Verification Commands

```bash
# 1. Check Kafka topics exist
docker exec kafka /opt/kafka/bin/kafka-topics.sh --describe \
  --topic vertiflow.external.nasa --bootstrap-server localhost:9092

# 2. Monitor consumer group LAG
watch -n 5 "docker exec kafka /opt/kafka/bin/kafka-consumer-groups.sh \
  --describe --bootstrap-server localhost:9092 \
  | grep nifi-external"

# 3. Check ClickHouse for new columns
docker exec clickhouse clickhouse-client --query \
  "SHOW COLUMNS FROM vertiflow.basil_ultimate_realtime LIKE 'ext_%'"

# 4. Tail NiFi logs for errors
docker logs -f nifi | grep -E "ERROR|WARN|ConsumeKafka"
```

## Time Estimate

- **Manual UI**: 5-15 minutes (depends on NiFi UI responsiveness)
- **REST API**: 2 minutes (once auth token obtained)
- **Programmatic**: Already attempted (complex XML manipulation)

## Recommended Approach

**Recommend**: Manual UI (Option A)
- Most reliable
- Easy to verify in real-time
- Easiest to troubleshoot
- Standard NiFi administration workflow

---

**After completing STEP 2, proceed to STEP 5: Validation Tests**

