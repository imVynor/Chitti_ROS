// Copyright 2026 Chitti Project
// Licensed under MIT

#include <cmath>
#include <string>
#include <vector>
#include <fcntl.h>
#include <termios.h>
#include <unistd.h>
#include <iostream>

#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/handle.hpp"
#include "hardware_interface/hardware_info.hpp"
#include "hardware_interface/types/hardware_interface_return_values.hpp"
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_lifecycle/state.hpp"
#include "pluginlib/class_list_macros.hpp"

namespace chitti_control
{

class CytronHardwareInterface : public hardware_interface::SystemInterface
{
public:
  hardware_interface::CallbackReturn on_init(
    const hardware_interface::HardwareInfo & info) override
  {
    if (hardware_interface::SystemInterface::on_init(info) !=
      hardware_interface::CallbackReturn::SUCCESS)
    {
      return hardware_interface::CallbackReturn::ERROR;
    }

    serial_port_ = info_.hardware_parameters.count("serial_port")
                   ? info_.hardware_parameters["serial_port"]
                   : "/dev/ttyUSB1";

    wheel_radius_ = std::stod(
      info_.hardware_parameters.count("wheel_radius")
      ? info_.hardware_parameters["wheel_radius"] : "0.05");

    max_motor_rpm_ = std::stod(
      info_.hardware_parameters.count("max_motor_rpm")
      ? info_.hardware_parameters["max_motor_rpm"] : "200.0");

    max_rad_per_sec_ = max_motor_rpm_ * 2.0 * M_PI / 60.0;

    hw_positions_.resize(4, 0.0);
    hw_velocities_.resize(4, 0.0);
    hw_commands_.resize(4, 0.0);

    RCLCPP_INFO(rclcpp::get_logger("CytronHardwareInterface"),
      "Configured for ESP32 Serial at port: %s", serial_port_.c_str());

    return hardware_interface::CallbackReturn::SUCCESS;
  }

  hardware_interface::CallbackReturn on_configure(
    const rclcpp_lifecycle::State & /*previous_state*/) override
  {
    serial_fd_ = open(serial_port_.c_str(), O_RDWR | O_NOCTTY | O_NDELAY);
    if (serial_fd_ == -1) {
      RCLCPP_ERROR(rclcpp::get_logger("CytronHardwareInterface"),
        "Failed to open Serial Port %s. Check permissions or connection.", serial_port_.c_str());
      return hardware_interface::CallbackReturn::ERROR;
    }

    struct termios options;
    tcgetattr(serial_fd_, &options);
    cfsetispeed(&options, B115200);
    cfsetospeed(&options, B115200);
    options.c_cflag |= (CLOCAL | CREAD);
    options.c_cflag &= ~PARENB;
    options.c_cflag &= ~CSTOPB;
    options.c_cflag &= ~CSIZE;
    options.c_cflag |= CS8;
    options.c_lflag &= ~(ICANON | ECHO | ECHOE | ISIG);
    options.c_oflag &= ~OPOST;
    tcsetattr(serial_fd_, TCSANOW, &options);

    RCLCPP_INFO(rclcpp::get_logger("CytronHardwareInterface"),
      "Serial connected to ESP32 successfully.");
      
    return hardware_interface::CallbackReturn::SUCCESS;
  }

  hardware_interface::CallbackReturn on_cleanup(
    const rclcpp_lifecycle::State & /*previous_state*/) override
  {
    if (serial_fd_ != -1) {
      std::string stop_cmd = "S";
      ::write(serial_fd_, stop_cmd.c_str(), stop_cmd.length());
      close(serial_fd_);
    }
    return hardware_interface::CallbackReturn::SUCCESS;
  }

  std::vector<hardware_interface::StateInterface>
  export_state_interfaces() override
  {
    std::vector<hardware_interface::StateInterface> state_interfaces;
    for (size_t i = 0; i < info_.joints.size(); ++i) {
      state_interfaces.emplace_back(
        info_.joints[i].name, hardware_interface::HW_IF_POSITION,
        &hw_positions_[i]);
      state_interfaces.emplace_back(
        info_.joints[i].name, hardware_interface::HW_IF_VELOCITY,
        &hw_velocities_[i]);
    }
    return state_interfaces;
  }

  std::vector<hardware_interface::CommandInterface>
  export_command_interfaces() override
  {
    std::vector<hardware_interface::CommandInterface> command_interfaces;
    for (size_t i = 0; i < info_.joints.size(); ++i) {
      command_interfaces.emplace_back(
        info_.joints[i].name, hardware_interface::HW_IF_VELOCITY,
        &hw_commands_[i]);
    }
    return command_interfaces;
  }

  hardware_interface::return_type read(
    const rclcpp::Time & /*time*/,
    const rclcpp::Duration & period) override
  {
    double dt = period.seconds();
    for (size_t i = 0; i < 4; ++i) {
      if (std::isnan(hw_commands_[i])) {
        hw_commands_[i] = 0.0;
      }
      hw_velocities_[i] = hw_commands_[i];
      hw_positions_[i] += hw_velocities_[i] * dt;
    }
    return hardware_interface::return_type::OK;
  }

  hardware_interface::return_type write(
    const rclcpp::Time & /*time*/,
    const rclcpp::Duration & /*period*/) override
  {
    // hw_commands_[0] and [2] are left side. hw_commands_[1] and [3] are right side.
    double left_vel = hw_commands_[0];
    double right_vel = hw_commands_[1];
    
    char cmd = 'S';
    double threshold = 0.5; // Trigger point in rad/s

    if (left_vel > threshold && right_vel > threshold) {
      cmd = 'F';
    } else if (left_vel < -threshold && right_vel < -threshold) {
      cmd = 'B';
    } else if (left_vel < -threshold && right_vel > threshold) {
      cmd = 'L';
    } else if (left_vel > threshold && right_vel < -threshold) {
      cmd = 'R';
    }

    if (serial_fd_ != -1) {
      std::string cmd_str(1, cmd);
      ::write(serial_fd_, cmd_str.c_str(), cmd_str.length());
    }

    return hardware_interface::return_type::OK;
  }

private:
  int rads_to_pwm(double velocity_rad_s)
  {
    if (std::isnan(velocity_rad_s)) velocity_rad_s = 0.0;
    
    double sign = velocity_rad_s >= 0.0 ? 1.0 : -1.0;
    double abs_vel = std::fabs(velocity_rad_s);

    if (abs_vel > max_rad_per_sec_) {
      abs_vel = max_rad_per_sec_;
    }

    int duty = static_cast<int>((abs_vel / max_rad_per_sec_) * 255.0);
    return duty * sign;
  }

  std::string serial_port_ = "/dev/ttyUSB1";
  int serial_fd_ = -1;

  double wheel_radius_ = 0.05;
  double max_motor_rpm_ = 200.0;
  double max_rad_per_sec_ = 0.0;

  std::vector<double> hw_positions_;
  std::vector<double> hw_velocities_;
  std::vector<double> hw_commands_;
};

}  // namespace chitti_control

PLUGINLIB_EXPORT_CLASS(
  chitti_control::CytronHardwareInterface,
  hardware_interface::SystemInterface)
