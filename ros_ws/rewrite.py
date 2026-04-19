import yaml

destinations = {
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
}

with open('src/chitti_navigation/chitti_navigation/destination_manager_node.py', 'r') as f:
    content = f.read()

start = content.find("self.locations = {")
end = content.find("}", start) + 1

new_locations = "self.locations = {\n"
for k, v in destinations.items():
    new_locations += f"            '{k}': {{'name': '{v['name']}', 'lat': {v['lat']}, 'lon': {v['lon']}}},\n"
new_locations += "        }"

content = content[:start] + new_locations + content[end:]
with open('src/chitti_navigation/chitti_navigation/destination_manager_node.py', 'w') as f:
    f.write(content)


yaml_locations = {}
for k, v in destinations.items():
    yaml_locations[k] = {
        'name': v['name'],
        'coordinates': [v['lat'], v['lon'], 0.0],
        'description': v['name'],
        'accessibility': {
            'wheelchair_accessible': True,
            'elevator_available': True,
            'audio_guidance': True
        },
        'estimated_time_from_center': 5
    }

yaml_data = {
    'locations': yaml_locations,
    'quick_tours': {
        'campus_highlights': {
            'name': 'Campus Highlights',
            'duration': 45,
            'locations': ['library', 'jasubhai', 'sports_complex'],
            'description': 'See the best of IIT Gandhinagar'
        }
    }
}

with open('src/chitti_navigation/config/campus_locations.yaml', 'w') as f:
    yaml.dump(yaml_data, f, sort_keys=False)

