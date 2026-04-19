import os
import glob

# New list of destinations
new_destinations = """        self.destinations = {
            'library': {'name': 'Central Library', 'lat': 23.213556, 'lon': 72.686485},
            'jibaben': {'name': 'Jibaben', 'lat': 23.214793, 'lon': 72.685498},
            'jasubhai': {'name': 'Jasubhai', 'lat': 23.214685, 'lon': 72.685762},
            'duven': {'name': 'Duven Hostel', 'lat': 23.210695, 'lon': 72.685313},
            'sports_complex': {'name': 'Sports Complex', 'lat': 23.211714, 'lon': 72.687882},
            'guest_house': {'name': 'Guest House', 'lat': 23.211416, 'lon': 72.689919},
            'jaiswal_mess': {'name': 'Jaiswal Mess', 'lat': 23.210932, 'lon': 72.683778},
            'new_pc': {'name': 'New PC', 'lat': 23.209977, 'lon': 72.684410},
            'rangmanch': {'name': 'Rangmanch', 'lat': 23.216262, 'lon': 72.687482},
            'gate_1': {'name': 'Gate 1', 'lat': 23.215753, 'lon': 72.693079},
        }"""

# Replacements for datum
REPLACEMENTS = [
    ('23.213911122480645', '23.213556'),
    ('23.2139111', '23.213556'),
    ('23.213911', '23.213556'),
    ('72.68500570339303', '72.686485'),
    ('72.6850057', '72.686485'),
    ('72.685005', '72.686485'),
]

files_to_update = [
    'src/chitti_hmi/web_interface/app.py',
    'src/chitti_navigation/chitti_navigation/osrm_path_node.py',
    'src/chitti_navigation/chitti_navigation/fake_sensors.py',
    'src/chitti_bringup/config/navsat_transform.yaml',
    'src/chitti_navigation/config/campus_locations.yaml'
]

for filepath in files_to_update:
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            content = f.read()
        for old, new in REPLACEMENTS:
            content = content.replace(old, new)
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Updated {filepath}")

# Special update for destination_manager_node.py
dest_manager = 'src/chitti_navigation/chitti_navigation/destination_manager_node.py'
if os.path.exists(dest_manager):
    with open(dest_manager, 'r') as f:
        content = f.read()
    
    start_idx = content.find("self.destinations = {")
    end_idx = content.find("}", start_idx) + 1
    
    if start_idx != -1 and end_idx != -1:
        content = content[:start_idx] + new_destinations + content[end_idx:]
        with open(dest_manager, 'w') as f:
            f.write(content)
        print(f"Updated destinations in {dest_manager}")

