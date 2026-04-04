cmake_minimum_required(VERSION 3.8)
project(chitti_control)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# ── Dependencies ──
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(hardware_interface REQUIRED)
find_package(pluginlib REQUIRED)
find_package(rclcpp_lifecycle REQUIRED)

# ── Optional: pigpio for real Raspberry Pi GPIO ──
# To build with real GPIO support, pass  -DUSE_PIGPIO=ON  to colcon / cmake.
option(USE_PIGPIO "Build with pigpio for real GPIO output" OFF)

# ── Shared library: hardware interface plugin ──
add_library(cytron_hardware_interface SHARED
  src/cytron_hardware_interface.cpp
)
target_include_directories(cytron_hardware_interface PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
ament_target_dependencies(cytron_hardware_interface
  rclcpp
  hardware_interface
  pluginlib
  rclcpp_lifecycle
)

if(USE_PIGPIO)
  target_compile_definitions(cytron_hardware_interface PRIVATE USE_PIGPIO)
  target_link_libraries(cytron_hardware_interface pigpio)
endif()

# ── Register the pluginlib plugin ──
pluginlib_export_plugin_description_file(hardware_interface chitti_control_plugin.xml)

# ── Install targets ──
install(TARGETS cytron_hardware_interface
  EXPORT export_chitti_control
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

install(DIRECTORY config/
  DESTINATION share/${PROJECT_NAME}/config
)

# ── Testing ──
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
