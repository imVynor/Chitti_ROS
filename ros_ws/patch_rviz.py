import re

with open('/home/anubhav-gupta/Chitti/ros_ws/src/chitti_bringup/rviz/nav_debug.rviz', 'r') as f:
    content = f.read()

marker_yaml = """    - Class: rviz_default_plugins/Marker
      Enabled: true
      Marker Topic:
        Depth: 5
        Durability Policy: Transient Local
        History Policy: Keep Last
        Reliability Policy: Reliable
        Value: /campus_map_marker
      Name: Campus Map
      Namespaces:
        osmnx_map: true
      Value: true
"""
if 'Marker Topic:' not in content:
    content = content.replace('    - Class: rviz_default_plugins/Path', marker_yaml + '    - Class: rviz_default_plugins/Path')
    with open('/home/anubhav-gupta/Chitti/ros_ws/src/chitti_bringup/rviz/nav_debug.rviz', 'w') as f:
        f.write(content)
