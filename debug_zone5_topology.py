#!/usr/bin/env python3
"""
Debug et fix Zone 5 connections - pourquoi les recettes ne vont pas à MongoDB?
"""

import subprocess
import gzip
import xml.etree.ElementTree as ET
import json

# Extraire le flow.xml.gz
result = subprocess.run(
    ["docker", "exec", "nifi", "gzip", "-dc", "/opt/nifi/nifi-current/conf/flow.xml.gz"],
    capture_output=True,
    text=True
)

data = result.stdout
root = ET.fromstring(data)

# Trouver Zone 5
zone5 = None
for pg in root.findall('.//processGroup'):
    name_elem = pg.find('name')
    if name_elem is not None and 'Zone 5' in name_elem.text:
        zone5 = pg
        break

if not zone5:
    print("❌ Zone 5 not found!")
    exit(1)

print("=" * 80)
print("🔍 ZONE 5 TOPOLOGY ANALYSIS")
print("=" * 80)

# Afficher les processors
print("\n📦 PROCESSORS:")
processors = {}
for proc in zone5.findall('.//processor'):
    proc_id = proc.find('id')
    proc_name = proc.find('name')
    proc_class = proc.find('class')
    state = proc.find('scheduleState')
    
    if proc_id is not None and proc_name is not None:
        proc_key = proc_id.text
        processors[proc_key] = {
            'name': proc_name.text,
            'class': proc_class.text if proc_class is not None else 'UNKNOWN',
            'state': state.text if state is not None else 'UNKNOWN'
        }
        print(f"  [{proc_key[:8]}...] {proc_name.text}")
        print(f"      └─ Class: {proc_class.text if proc_class is not None else 'UNKNOWN'}")
        print(f"      └─ State: {state.text if state is not None else 'UNKNOWN'}")

# Afficher les connections
print("\n🔗 CONNECTIONS:")
connections = []
for conn in zone5.findall('.//connection'):
    src = conn.find('source/id')
    dest = conn.find('destination/id')
    rel = conn.find('relationshipNames/name')
    
    if src is not None and dest is not None:
        src_id = src.text
        dest_id = dest.text
        rel_name = rel.text if rel is not None else "DEFAULT"
        
        src_name = processors.get(src_id, {}).get('name', f'[UNKNOWN {src_id[:8]}]')
        dest_name = processors.get(dest_id, {}).get('name', f'[UNKNOWN {dest_id[:8]}]')
        
        connections.append((src_name, dest_name, rel_name))
        print(f"  {src_name}")
        print(f"    ──[{rel_name}]──>")
        print(f"  {dest_name}\n")

# Analyser le flux
print("\n" + "=" * 80)
print("🎯 ANALYSIS")
print("=" * 80)

# Trouver les chemins à partir de GetFile - Recipes
print("\n📤 PATH: GetFile - Recipes")
print("  1. GetFile - Recipes")
next_conns = [c for c in connections if c[0] == 'GetFile - Recipes']
if next_conns:
    for src, dest, rel in next_conns:
        print(f"     ──[{rel}]──> {dest}")
        # Continuer le chemin
        next2 = [c for c in connections if c[0] == dest]
        for s2, d2, r2 in next2:
            print(f"              ──[{r2}]──> {d2}")
else:
    print("  ❌ GetFile - Recipes n'a aucune connection sortante!")

# Vérifier si PutMongo a des entrants
print("\n🔴 PutMongo ANALYSIS:")
for proc_name in ['PutMongo - Plant Recipes', 'PutMongo - Market Prices']:
    incoming = [c for c in connections if c[1] == proc_name]
    if incoming:
        print(f"  ✅ {proc_name}:")
        for src, dest, rel in incoming:
            print(f"     {src} ──[{rel}]──> {proc_name}")
    else:
        print(f"  ❌ {proc_name}: NO INCOMING CONNECTIONS!")

print("\n" + "=" * 80)
print("💡 CONCLUSION")
print("=" * 80)

if not any(dest == 'PutMongo - Plant Recipes' for src, dest, rel in connections):
    print("\n❌ PROBLEM FOUND:")
    print("   PutMongo - Plant Recipes has NO incoming connections!")
    print("   The data is being routed elsewhere (probably to PutFile - output)")
    print("\n   SOLUTION: Reconnect ValidateRecord → PutMongo - Plant Recipes")
else:
    print("\n✅ Zone 5 connections look OK!")
    print("   Check if ValidateRecord is routing to 'success' relationship")

print("\n" + "=" * 80)
