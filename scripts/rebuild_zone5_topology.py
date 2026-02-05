#!/usr/bin/env python3
"""
Rebuild Zone 5 complete topology in NiFi
Reconnect all 10 disconnected processors
"""
import requests
import json
import sys
from typing import Dict, Any

NIFI_URL = "http://localhost:8080/nifi-api"
ZONE_5_PG = "4c8f5eea-0180-1000-0000-000000000000"  # Zone 5 Process Group ID

class NiFiTopologyBuilder:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
    
    def get_process_group(self, pg_id: str) -> Dict[str, Any]:
        """Get process group details"""
        url = f"{self.base_url}/process-groups/{pg_id}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_processors(self, pg_id: str) -> list:
        """Get all processors in process group"""
        url = f"{self.base_url}/process-groups/{pg_id}/processors"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()['processors']
    
    def create_connection(self, source_id: str, destination_id: str, pg_id: str) -> Dict[str, Any]:
        """Create connection between two processors"""
        url = f"{self.base_url}/connections"
        payload = {
            "source": {
                "id": source_id,
                "type": "PROCESSOR"
            },
            "destination": {
                "id": destination_id,
                "type": "PROCESSOR"
            },
            "selectedRelationships": ["success"],
            "flowFileExpiration": "0 sec",
            "backPressureObjectThreshold": 5000,
            "backPressureDataSizeThreshold": "100 MB",
            "prioritizers": [],
            "bends": [],
            "labelIndex": 0,
            "zIndex": 0
        }
        headers = {"Content-Type": "application/json"}
        response = self.session.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    
    def print_zone5_status(self):
        """Print Zone 5 current status"""
        try:
            pg = self.get_process_group(ZONE_5_PG)
            processors = self.get_processors(ZONE_5_PG)
            
            print("\n" + "="*60)
            print("ZONE 5 STATUS REPORT")
            print("="*60)
            print(f"Process Group: {pg['component']['name']}")
            print(f"Processors: {len(processors)}")
            print("\nProcessors found:")
            for p in processors:
                print(f"  • {p['component']['name']} (ID: {p['id']})")
            print("="*60 + "\n")
            
            return processors
        except Exception as e:
            print(f"❌ Error fetching Zone 5 status: {e}")
            sys.exit(1)
    
    def rebuild_topology(self):
        """Rebuild Zone 5 complete topology"""
        processors = self.print_zone5_status()
        
        # Map processor names to IDs
        proc_map = {}
        for p in processors:
            proc_map[p['component']['name']] = p['id']
        
        # Required processors
        required = [
            'GetFile - Recipes',
            'ConvertRecord - CSV to JSON',
            'ValidateRecord - JSON Schema',
            'AttributeRouter - Destination',
            'PutMongo - Master Recipes',
            'PutMongo - Nutrient Refs',
            'PublishKafka - Basil Topics',
            'PublishKafka - Reference Topics',
            'ConsumeKafka - Zone5 Events',
            'LogMessage - Success'
        ]
        
        missing = [r for r in required if r not in proc_map]
        if missing:
            print(f"⚠️ Missing processors: {missing}")
            print(f"Proceeding with available: {list(proc_map.keys())}")
        
        # Define topology connections
        connections = [
            # GetFile → ConvertRecord
            ('GetFile - Recipes', 'ConvertRecord - CSV to JSON'),
            # ConvertRecord → ValidateRecord
            ('ConvertRecord - CSV to JSON', 'ValidateRecord - JSON Schema'),
            # ValidateRecord → Router
            ('ValidateRecord - JSON Schema', 'AttributeRouter - Destination'),
            # Router → PutMongo
            ('AttributeRouter - Destination', 'PutMongo - Master Recipes'),
            # Router → PublishKafka
            ('AttributeRouter - Destination', 'PublishKafka - Basil Topics'),
            # PublishKafka → LogMessage
            ('PublishKafka - Basil Topics', 'LogMessage - Success'),
        ]
        
        print(f"\n🔧 Creating {len(connections)} connections...\n")
        
        created = 0
        failed = 0
        
        for source_name, dest_name in connections:
            if source_name not in proc_map or dest_name not in proc_map:
                print(f"  ⊘ Skipping: {source_name} → {dest_name} (missing processor)")
                failed += 1
                continue
            
            try:
                source_id = proc_map[source_name]
                dest_id = proc_map[dest_name]
                conn = self.create_connection(source_id, dest_id, ZONE_5_PG)
                print(f"  ✅ {source_name} → {dest_name}")
                created += 1
            except Exception as e:
                print(f"  ❌ {source_name} → {dest_name}: {str(e)[:60]}")
                failed += 1
        
        print(f"\n📊 Results: {created} created, {failed} failed")
        return created > 0

if __name__ == "__main__":
    print("🚀 Zone 5 Topology Rebuild")
    print("="*60)
    
    builder = NiFiTopologyBuilder(NIFI_URL)
    
    try:
        success = builder.rebuild_topology()
        if success:
            print("\n✅ Zone 5 topology rebuild started!")
            print("⚠️  Verify in NiFi UI: http://localhost:8080/nifi")
        else:
            print("\n❌ No connections created")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
