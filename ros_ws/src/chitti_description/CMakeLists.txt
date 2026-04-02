cmake_minimum_required(VERSION 3.8)
project(chitti_description)

find_package(ament_cmake REQUIRED)

# Install URDF and launch files so ROS can find them
install(DIRECTORY urdf launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
