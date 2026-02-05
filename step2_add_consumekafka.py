#!/usr/bin/env python3
"""
STEP 2 PROGRAMMATIC EXECUTION
Ajouter 3× ConsumeKafka processors en Zone 1 via manipulation XML
"""

import subprocess
import xml.etree.ElementTree as ET
import gzip
import uuid
import time
from datetime import datetime

print("="*80)
print("🔧 STEP 2: AJOUTER 3× ConsumeKafka ZONE 1")
print("="*80)

# Configuration
EXTERNAL_TOPICS = [
    {"name": "A4 - NASA POWER", "topic": "vertiflow.external.nasa", "group": "nifi-external-group-nasa"},
    {"name": "A5 - Weather", "topic": "vertiflow.external.weather", "group": "nifi-external-group-weather"},
    {"name": "A6 - AirQuality", "topic": "vertiflow.external.airquality", "group": "nifi-external-group-airquality"},
]

# 1. Extract flow.xml from container
print("\n1️⃣  EXTRACTION...")
try:
    subprocess.run(["docker", "cp", "nifi:/opt/nifi/nifi-current/conf/flow.xml.gz", "/tmp/flow_step2.xml.gz"],
                   capture_output=True, check=True, timeout=30)
    print("   ✅ Flow extrait du conteneur")
except Exception as e:
    print(f"   ❌ Erreur: {e}")
    exit(1)

# 2. Decompress
print("\n2️⃣  DÉCOMPRESSION...")
try:
    with gzip.open("/tmp/flow_step2.xml.gz", 'rb') as f:
        xml_data = f.read()
    with open("/tmp/flow_step2.xml", 'wb') as f:
        f.write(xml_data)
    print("   ✅ XML décompressé")
except Exception as e:
    print(f"   ❌ Erreur: {e}")
    exit(1)

# 3. Parse XML
print("\n3️⃣  PARSING XML...")
try:
    # Register namespace for proper handling
    ET.register_namespace('', 'http://www.springframework.org/schema/beans')
    tree = ET.parse("/tmp/flow_step2.xml")
    root = tree.getroot()
    print("   ✅ XML parsé")
except Exception as e:
    print(f"   ❌ Erreur parsing: {e}")
    exit(1)

# 4. Find Zone 1
print("\n4️⃣  LOCATING ZONE 1...")
zone_1 = None
zone_1_id = None
merge_processor_id = None

for pg in root.findall('.//processGroup'):
    name_elem = pg.find('name')
    if name_elem is not None and "Zone 1" in name_elem.text:
        zone_1 = pg
        zone_1_id = pg.find('id').text
        print(f"   ✅ Zone 1 trouvée (ID: {zone_1_id[:12]}...)")
        
        # Find MergeContent processor in Zone 1
        for proc in pg.findall('processor'):
            proc_name = proc.find('name')
            if proc_name is not None and "MergeContent" in proc_name.text:
                merge_processor_id = proc.find('id').text
                print(f"   ✅ MergeContent trouvé (ID: {merge_processor_id[:12]}...)")
                break
        break

if zone_1 is None:
    print("   ❌ Zone 1 non trouvée!")
    exit(1)

if merge_processor_id is None:
    print("   ⚠️  MergeContent non trouvé (créera sans connexion)")

# 5. Create 3 ConsumeKafka processors
print("\n5️⃣  CRÉATION 3× ConsumeKafka...")

created_proc_ids = []

for topic_config in EXTERNAL_TOPICS:
    proc_id = str(uuid.uuid4())
    created_proc_ids.append(proc_id)
    
    # Create processor element
    processor = ET.Element('processor')
    
    # ID
    proc_id_elem = ET.SubElement(processor, 'id')
    proc_id_elem.text = proc_id
    
    # Name
    name_elem = ET.SubElement(processor, 'name')
    name_elem.text = topic_config['name']
    
    # Comment (optional)
    comment = ET.SubElement(processor, 'comment')
    comment.text = f"Consume {topic_config['topic']}"
    
    # Position
    pos = ET.SubElement(processor, 'position')
    x = ET.SubElement(pos, 'x')
    x.text = str(100 + len(created_proc_ids) * 250)
    y = ET.SubElement(pos, 'y')
    y.text = "100"
    
    # Class
    class_elem = ET.SubElement(processor, 'class')
    class_elem.text = "org.apache.nifi.processors.kafka.pubsub.ConsumeKafka_2_6"
    
    # Bundle
    bundle = ET.SubElement(processor, 'bundle')
    bundle_artifact = ET.SubElement(bundle, 'artifact')
    bundle_artifact.text = "nifi-kafka-2-6-nar"
    bundle_version = ET.SubElement(bundle, 'version')
    bundle_version.text = "1.23.2"
    
    # Config
    config = ET.SubElement(processor, 'config')
    
    # Scheduling
    sched = ET.SubElement(config, 'schedulingPeriod')
    sched.text = "0 sec"
    
    sched_strat = ET.SubElement(config, 'schedulingStrategy')
    sched_strat.text = "TIMER_DRIVEN"
    
    concur = ET.SubElement(config, 'concurrentlySchedulableTaskCount')
    concur.text = "1"
    
    # State
    state = ET.SubElement(processor, 'scheduledState')
    state.text = "RUNNING"
    
    # Properties
    properties = ET.SubElement(config, 'properties')
    
    prop_list = [
        ('bootstrap.servers', 'kafka:9092'),
        ('topic', topic_config['topic']),
        ('group.id', topic_config['group']),
        ('Session timeout', '30 sec'),
        ('Offset reset strategy', 'latest'),
        ('Key attribute encoding', 'utf-8'),
        ('Message Demarcator', None),
        ('Max poll records', '500'),
        ('Connections Per Broker', '1'),
        ('Max uncommitted messages', '10000'),
    ]
    
    for prop_name, prop_value in prop_list:
        if prop_value is not None:
            prop = ET.SubElement(properties, 'entry')
            key = ET.SubElement(prop, 'key')
            key.text = prop_name
            val = ET.SubElement(prop, 'value')
            val.text = prop_value
    
    # Relationships
    rels = ET.SubElement(config, 'autoTerminatedRelationships')
    
    # Add processor to Zone 1
    zone_1.append(processor)
    print(f"   ✅ {topic_config['name']} créé")

# 6. Create connections (if MergeContent found)
print("\n6️⃣  CRÉATION CONNECTIONS...")

if merge_processor_id:
    for proc_id in created_proc_ids:
        conn = ET.Element('connection')
        
        # ID
        conn_id = ET.SubElement(conn, 'id')
        conn_id.text = str(uuid.uuid4())
        
        # Source
        source = ET.SubElement(conn, 'source')
        id_src = ET.SubElement(source, 'id')
        id_src.text = proc_id
        rel = ET.SubElement(source, 'port')
        rel.text = "success"
        
        # Destination
        dest = ET.SubElement(conn, 'destination')
        id_dest = ET.SubElement(dest, 'id')
        id_dest.text = merge_processor_id
        port_dest = ET.SubElement(dest, 'port')
        port_dest.text = "input"
        
        # Name
        conn_name = ET.SubElement(conn, 'name')
        conn_name.text = ""
        
        # Flowfile expiration
        exp = ET.SubElement(conn, 'flowFileExpiration')
        exp.text = "0 sec"
        
        # Back pressure
        bp = ET.SubElement(conn, 'backPressureObjectThreshold')
        bp.text = "20000"
        
        bp_size = ET.SubElement(conn, 'backPressureDataSizeThreshold')
        bp_size.text = "100 MB"
        
        # Add connection to Zone 1
        zone_1.append(conn)
    
    print(f"   ✅ {len(created_proc_ids)} connections créées")
else:
    print(f"   ⚠️  Connections non créées (MergeContent pas trouvé)")

# 7. Save modified XML
print("\n7️⃣  SAUVEGARDE...")
try:
    tree.write("/tmp/flow_step2_modified.xml", encoding='UTF-8', xml_declaration=True)
    print("   ✅ XML modifié sauvegardé")
except Exception as e:
    print(f"   ❌ Erreur sauvegarde: {e}")
    exit(1)

# 8. Compress
print("\n8️⃣  COMPRESSION...")
try:
    with open("/tmp/flow_step2_modified.xml", 'rb') as f_in:
        data = f_in.read()
    with gzip.open("/tmp/flow_step2_modified.xml.gz", 'wb') as f_out:
        f_out.write(data)
    print("   ✅ Compressé")
except Exception as e:
    print(f"   ❌ Erreur compression: {e}")
    exit(1)

# 9. Deploy
print("\n9️⃣  DÉPLOIEMENT...")
try:
    # Backup
    subprocess.run(["docker", "exec", "nifi", "bash", "-c",
                   "cp /opt/nifi/nifi-current/conf/flow.xml.gz /opt/nifi/nifi-current/conf/flow.xml.gz.backup.step2"],
                   capture_output=True, check=True, timeout=30)
    
    # Deploy
    subprocess.run(["docker", "cp", "/tmp/flow_step2_modified.xml.gz", "nifi:/opt/nifi/nifi-current/conf/flow.xml.gz"],
                   capture_output=True, check=True, timeout=30)
    print("   ✅ Déployé au conteneur")
except Exception as e:
    print(f"   ❌ Erreur déploiement: {e}")
    exit(1)

# 10. Restart NiFi
print("\n🔟 REDÉMARRAGE NIFI...")
try:
    subprocess.run(["docker", "stop", "nifi"], capture_output=True, timeout=30)
    time.sleep(3)
    subprocess.run(["docker", "start", "nifi"], capture_output=True, timeout=30)
    print("   ✅ NiFi arrêté et redémarré")
    
    print("   ⏳ Attente démarrage (30s)...")
    time.sleep(30)
    
    # Vérifier
    ps_result = subprocess.run(["docker", "ps", "--format", "{{.Status}}", "-f", "name=nifi"],
                              capture_output=True, text=True)
    if "Up" in ps_result.stdout:
        print("   ✅ NiFi en cours de démarrage")
    else:
        print("   ⚠️  NiFi status inconnu")
        
except Exception as e:
    print(f"   ⚠️  Erreur redémarrage: {e}")

print("\n" + "="*80)
print("✅ STEP 2 COMPLÉTED")
print("="*80)
print(f"""
3 ConsumeKafka processors créés:
  ✅ A4 - NASA POWER (vertiflow.external.nasa)
  ✅ A5 - Weather (vertiflow.external.weather)
  ✅ A6 - AirQuality (vertiflow.external.airquality)

Status: NiFi en cours de redémarrage

Prochaine étape:
  1. Attendre NiFi healthy (2-3 min)
  2. Exécuter STEP 5 validation tests
  3. Vérifier Grafana Dashboard 12 pour NASA data

Commandes de vérification:
  docker ps | grep nifi
  docker exec nifi curl -s http://localhost:8080/nifi-api/system-diagnostics
  python3 step5_validation_tests.py
""")

print(f"Terminé: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

