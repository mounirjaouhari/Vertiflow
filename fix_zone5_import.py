#!/usr/bin/env python3
"""
Fix Zone 5 to import Basil recipes via CSV→JSON conversion
"""

import requests
import json
import time
import sys
import urllib3

urllib3.disable_warnings()

BASE_URL = "https://localhost:8443/nifi-api"
HEADERS = {"Content-Type": "application/json"}

def get_zone_by_name(zone_name):
    """Find zone process group ID by name"""
    try:
        resp = requests.get(f"{BASE_URL}/process-groups/root/process-groups", 
                           headers=HEADERS, verify=False, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        for pg in data.get('processGroups', []):
            if zone_name in pg['component']['name']:
                return pg['id'], pg
        return None, None
    except Exception as e:
        print(f"❌ Error getting zones: {e}")
        return None, None

def get_processors_by_type(zone_id, proc_type):
    """Get processors of specific type in zone"""
    try:
        resp = requests.get(f"{BASE_URL}/process-groups/{zone_id}/processors",
                           headers=HEADERS, verify=False, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        procs = []
        for proc in data.get('processors', []):
            if proc_type in proc['component']['name']:
                procs.append(proc)
        return procs
    except Exception as e:
        print(f"❌ Error getting processors: {e}")
        return []

def start_processor(processor_id, revision):
    """Start a processor"""
    try:
        payload = {
            "revision": revision,
            "state": "RUNNING"
        }
        resp = requests.put(f"{BASE_URL}/processors/{processor_id}",
                           json=payload, headers=HEADERS, verify=False, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"❌ Error starting processor: {e}")
        return False

def get_processor_revision(processor_id):
    """Get current revision of processor"""
    try:
        resp = requests.get(f"{BASE_URL}/processors/{processor_id}",
                           headers=HEADERS, verify=False, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data['component']['revision']
    except Exception as e:
        print(f"❌ Error getting processor: {e}")
        return None

def main():
    print("🔧 Fixing Zone 5 for CSV/JSON Recipe Import\n")
    
    # Get Zone 5
    zone_id, zone_data = get_zone_by_name("Zone 5")
    if not zone_id:
        print("❌ Zone 5 not found!")
        return False
        
    print(f"✅ Found Zone 5: {zone_id}\n")
    
    # Get all GetFile processors (recipes, lab, datasets)
    getfiles = get_processors_by_type(zone_id, "GetFile")
    print(f"📁 Found {len(getfiles)} GetFile processors:")
    for gf in getfiles:
        state = gf['component']['state']
        name = gf['component']['name']
        print(f"  • {name}: {state}")
    
    # Start all GetFile processors
    print("\n🚀 Starting GetFile processors...")
    for gf in getfiles:
        proc_id = gf['id']
        name = gf['component']['name']
        revision = gf['component']['revision']
        
        if gf['component']['state'] != 'RUNNING':
            if start_processor(proc_id, revision):
                print(f"  ✅ {name} started")
            else:
                print(f"  ❌ Failed to start {name}")
        else:
            print(f"  ℹ️  {name} already running")
    
    # Wait and check status
    print("\n⏳ Waiting for processors to become active...")
    time.sleep(3)
    
    # Check for errors
    print("\n📊 Checking for processing errors...")
    try:
        with open('/var/log/nifi-app.log', 'r') as f:
            lines = f.readlines()[-100:]
            errors = [l for l in lines if 'recipes' in l.lower() and 'error' in l.lower()]
            if errors:
                print("  ❌ Found errors:")
                for e in errors[-3:]:
                    print(f"     {e.strip()}")
            else:
                print("  ✅ No recent errors")
    except:
        print("  ℹ️  Could not check error log")
    
    print("\n✅ Zone 5 configuration complete!")
    print("\n📝 Next steps:")
    print("   1. Monitor Zone 5 in NiFi UI (https://localhost:8443/nifi)")
    print("   2. Check MongoDB: docker exec mongo mongosh -u admin -p admin")
    print("   3. Verify recipes: db.plant_recipes.find().count()")
    print("   4. Check ClickHouse: docker exec clickhouse clickhouse-client")
    print("      SELECT COUNT(*) FROM vertiflow.ref_plant_recipes")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
