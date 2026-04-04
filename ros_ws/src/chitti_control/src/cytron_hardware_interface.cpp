// Copyright 2026 Chitti Project
// Licensed under MIT

#include <cmath>
#include <string>
#include <vector>

#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/handle.hpp"
#include "hardware_interface/hardware_info.hpp"
#include "hardware_interface/types/hardware_interface_return_values.hpp"
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_lifecycle/state.hpp"
#include "pluginlib/class_list_macros.hpp"

// pigpio header – provides hardware-timed PWM on any GPIO pin
#ifdef USE_PIGPIO
#include <pigpio.h>
#endif

namespace chitti_control
{

class CytronHardwareInterface : public hardware_interface::SystemInterface
{
public:
  // ──────────────────────────────────────────────────────────────
  //  Lifecycle: on_init
  //  Read GPIO pin numbers and wheel parameters from URDF params.
  // ──────────────────────────────────────────────────────────────
  hardware_interface::CallbackReturn on_init(
    const hardware_interface::HardwareInfo & info) override
  {
    if (hardware_interface::SystemInterface::on_init(info) !=
      hardware_interface::CallbackReturn::SUCCESS)
    {
      return hardware_interface::CallbackReturn::ERROR;
    }

    // ── Read GPIO pin parameters from  URDF <ros2_control> block ──
    // Motor Driver 1 – Channel A  (Front Left)
    fl_pwm_pin_ = std::stoi(info_.hardware_parameters["fl_pwm_pin"]);
    fl_dir_pin_ = std::stoi(info_.hardware_parameters["fl_dir_pin"]);
    // Motor Driver 1 – Channel B  (Rear Left)
    rl_pwm_pin_ = std::stoi(info_.hardware_parameters["rl_pwm_pin"]);
    rl_dir_pin_ = std::stoi(info_.hardware_parameters["rl_dir_pin"]);

    // Motor Driver 2 – Channel A  (Front Right)
    fr_pwm_pin_ = std::stoi(info_.hardware_parameters["fr_pwm_pin"]);
    fr_dir_pin_ = std::stoi(info_.hardware_parameters["fr_dir_pin"]);
    // Motor Driver 2 – Channel B  (Rear Right)
    rr_pwm_pin_ = std::stoi(info_.hardware_parameters["rr_pwm_pin"]);
    rr_dir_pin_ = std::stoi(info_.hardware_parameters["rr_dir_pin"]);

    // ── Wheel physical parameters ──
    wheel_radius_ = std::stod(
      info_.hardware_parameters.count("wheel_radius")
      ? info_.hardware_parameters["wheel_radius"] : "0.05");

    max_motor_rpm_ = std::stod(
      info_.hardware_parameters.count("max_motor_rpm")
      ? info_.hardware_parameters["max_motor_rpm"] : "200.0");

    // rad/s at maximum PWM (255)
    max_rad_per_sec_ = max_motor_rpm_ * 2.0 * M_PI / 60.0;

    // Resize state & command vectors for 4 wheels
    hw_positions_.resize(4, 0.0);
    hw_velocities_.resize(4, 0.0);
    hw_commands_.resize(4, 0.0);

    RCLCPP_INFO(rclcpp::get_logger("CytronHardwareInterface"),
      "Loaded GPIO config – FL(%d/%d) RL(%d/%d) FR(%d/%d) RR(%d/%d)",
      fl_pwm_pin_, fl_dir_pin_, rl_pwm_pin_, rl_dir_pin_,
      fr_pwm_pin_, fr_dir_pin_, rr_pwm_pin_, rr_dir_pin_);

    return hardware_interface::CallbackReturn::SUCCESS;
  }

  // ──────────────────────────────────────────────────────────────
  //  Lifecycle: on_configure  →  Initialise pigpio
  // ──────────────────────────────────────────────────────────────
  hardware_interface::CallbackReturn on_configure(
    const rclcpp_lifecycle::State & /*previous_state*/) override
  {
#ifdef USE_PIGPIO
    if (gpioInitialise() < 0) {
      RCLCPP_ERROR(rclcpp::get_logger("CytronHardwareInterface"),
        "pigpio initialisation FAILED – are you running as root?");
      return hardware_interface::CallbackReturn::ERROR;
    }

    // Set all direction pins as outputs
    gpioSetMode(fl_dir_pin_, PI_OUTPUT);
    gpioSetMode(rl_dir_pin_, PI_OUTPUT);
    gpioSetMode(fr_dir_pin_, PI_OUTPUT);
    gpioSetMode(rr_dir_pin_, PI_OUTPUT);

    // Set PWM frequency to 20 kHz (silent for motors)
    gpioSetPWMfrequency(fl_pwm_pin_, 20000);
    gpioSetPWMfrequency(rl_pwm_pin_, 20000);
    gpioSetPWMfrequency(fr_pwm_pin_, 20000);
    gpioSetPWMfrequency(rr_pwm_pin_, 20000);

    // Set PWM range 0-255
    gpioSetPWMrange(fl_pwm_pin_, 255);
    gpioSetPWMrange(rl_pwm_pin_, 255);
    gpioSetPWMrange(fr_pwm_pin_, 255);
    gpioSetPWMrange(rr_pwm_pin_, 255);

    RCLCPP_INFO(rclcpp::get_logger("CytronHardwareInterface"),
      "pigpio initialised – GPIO ready");
#else
    RCLCPP_WARN(rclcpp::get_logger("CytronHardwareInterface"),
      "Built WITHOUT pigpio (USE_PIGPIO not defined). "
      "Running in DRY-RUN / simulation mode – no physical GPIO output.");
#endif
    return hardware_interface::CallbackReturn::SUCCESS;
  }

  // ──────────────────────────────────────────────────────────────
  //  Lifecycle: on_cleanup  →  Shutdown pigpio
  // ──────────────────────────────────────────────────────────────
  hardware_interface::CallbackReturn on_cleanup(
    const rclcpp_lifecycle::State & /*previous_state*/) override
  {
#ifdef USE_PIGPIO
    // Stop all motors
    gpioPWM(fl_pwm_pin_, 0);
    gpioPWM(rl_pwm_pin_, 0);
    gpioPWM(fr_pwm_pin_, 0);
    gpioPWM(rr_pwm_pin_, 0);
    gpioTerminate();
#endif
    return hardware_interface::CallbackReturn::SUCCESS;
  }

  // ──────────────────────────────────────────────────────────────
  //  Export state interfaces (position + velocity for each wheel)
  // ──────────────────────────────────────────────────────────────
  std::vector<hardware_interface::StateInterface>
  export_state_interfaces() override
  {
    std::vector<hardware_interface::StateInterface> state_interfaces;

    // Order: FL, FR, RL, RR  (matches info_.joints order from URDF)
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

  // ──────────────────────────────────────────────────────────────
  //  Export command interfaces (velocity for each wheel)
  // ──────────────────────────────────────────────────────────────
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

  // ──────────────────────────────────────────────────────────────
  //  read()  –  Open-loop: fake encoder feedback from commands
  // ──────────────────────────────────────────────────────────────
  hardware_interface::return_type read(
    const rclcpp::Time & /*time*/,
    const rclcpp::Duration & period) override
  {
    double dt = period.seconds();
    for (size_t i = 0; i < 4; ++i) {
      if (std::isnan(hw_commands_[i])) {
        // Guard against NaN commands sent during startup or recovery
        hw_commands_[i] = 0.0;
      }
      // Open-loop: assume velocity matches the command perfectly
      hw_velocities_[i] = hw_commands_[i];
      // Integrate position (radians)
      hw_positions_[i] += hw_velocities_[i] * dt;
    }
    return hardware_interface::return_type::OK;
  }

  // ──────────────────────────────────────────────────────────────
  //  write()  –  Convert rad/s commands  →  PWM + DIR on GPIO
  // ──────────────────────────────────────────────────────────────
  hardware_interface::return_type write(
    const rclcpp::Time & /*time*/,
    const rclcpp::Duration & /*period*/) override
  {
    // Map rad/s  →  PWM duty (0-255)
    // hw_commands_[0] = front_left,  [1] = front_right,
    // [2] = rear_left,   [3] = rear_right
    set_motor(fl_pwm_pin_, fl_dir_pin_, hw_commands_[0]);
    set_motor(fr_pwm_pin_, fr_dir_pin_, hw_commands_[1]);
    set_motor(rl_pwm_pin_, rl_dir_pin_, hw_commands_[2]);
    set_motor(rr_pwm_pin_, rr_dir_pin_, hw_commands_[3]);

    return hardware_interface::return_type::OK;
  }

private:
  // Convert a wheel velocity (rad/s) to GPIO PWM + direction
  void set_motor(int pwm_pin, int dir_pin, double velocity_rad_s)
  {
    bool forward = velocity_rad_s >= 0.0;
    double abs_vel = std::fabs(velocity_rad_s);

    if (std::isnan(abs_vel)) {
      abs_vel = 0.0;
    }

    // Clamp to max
    if (abs_vel > max_rad_per_sec_) {
      abs_vel = max_rad_per_sec_;
    }

    // Map to 0-255 PWM range
    int duty = static_cast<int>((abs_vel / max_rad_per_sec_) * 255.0);

#ifdef USE_PIGPIO
    gpioWrite(dir_pin, forward ? 1 : 0);
    gpioPWM(pwm_pin, duty);
#else
    // Dry-run logging (only when duty changes significantly)
    (void)pwm_pin;
    (void)dir_pin;
    (void)duty;
    (void)forward;
#endif
  }

  // ── GPIO pin numbers (set from URDF parameters) ──
  int fl_pwm_pin_ = -1, fl_dir_pin_ = -1;  // Front Left
  int fr_pwm_pin_ = -1, fr_dir_pin_ = -1;  // Front Right
  int rl_pwm_pin_ = -1, rl_dir_pin_ = -1;  // Rear Left
  int rr_pwm_pin_ = -1, rr_dir_pin_ = -1;  // Rear Right

  // ── Wheel / motor parameters ──
  double wheel_radius_ = 0.05;
  double max_motor_rpm_ = 200.0;
  double max_rad_per_sec_ = 0.0;

  // ── Joint state storage ──
  std::vector<double> hw_positions_;
  std::vector<double> hw_velocities_;
  std::vector<double> hw_commands_;
};

}  // namespace chitti_control

PLUGINLIB_EXPORT_CLASS(
  chitti_control::CytronHardwareInterface,
  hardware_interface::SystemInterface)
