cmake_minimum_required(VERSION 3.8)
project(chitti_msgs)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(builtin_interfaces REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/LocationRequest.msg"
  "msg/ScreenState.msg"
  "msg/QRCode.msg"
  "msg/AudioMode.msg"
  "msg/NetworkStatus.msg"
  "msg/RobotLocation.msg"
  "msg/RobotState.msg"
  "msg/TourStatus.msg"
  "srv/StartNavigation.srv"
  "srv/SetAudioMode.srv"
  "srv/CreateSession.srv"
  "srv/CloseSession.srv"
  "srv/UpdateUI.srv"
  "srv/CustomizeTour.srv"
  "action/NavigateToLocation.action"
  "action/SpeakResponse.action"
  "action/ProcessVoice.action"
  "action/ConductTour.action"
  DEPENDENCIES std_msgs geometry_msgs builtin_interfaces
)

ament_package()
