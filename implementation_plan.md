# Real-World Integration Execution Plan

Based on `analysis_results.md`, your system architecture is almost complete, but there are isolated gaps holding everything off from working out-of-the-box on a real Raspberry Pi. I will implement the 5 priority gaps outlined to combine your physical stack with your Navigator pipeline.

## Proposed Changes

### 1. `chitti_bringup/launch/sensors.launch.py`
**Issue:** `sensors.launch.py` has no driver nodes. 
**Fix:** I will inject the `nmea_navsat_driver` and `mpu9250driver` nodes so your computer actively grabs I2C and Serial feeds to publish the `/fix` and `/imu/data` topics respectively. *(Note: Since you are on a VirtualBox, these nodes will idle unless you plug the hardware in via USB passthrough, but their presence is mandatory for the main robot).*

#### [MODIFY] [sensors.launch.py](file:///home/anubhav-gupta/Chitti/ros_ws/src/chitti_bringup/launch/sensors.launch.py)

### 2. `chitti_bringup/config/ekf.yaml`
**Issue:** The EKF only relies on GPS (`odom0`) and IMU (`imu0`), throwing away the reliable wheel spins we fixed earlier!
**Fix:** Add `odom1: /odom` (your hardware wheel odometry) to the filter config, fusing the `Twist` (linear and angular velocities) so the robot maintains smooth track awareness if the GPS signal bounces underneath trees.

#### [MODIFY] [ekf.yaml](file:///home/anubhav-gupta/Chitti/ros_ws/src/chitti_bringup/config/ekf.yaml)

### 3. `chitti_bringup/launch/navigation.launch.py`
**Issue:**
- A static transform hardcodes `map` -> `odom`, shutting out the NavSat transform localization predictions.
- `navigation.launch.py` operates as a simulator config.
**Fix:**
- Encapsulate the static transform into an `IfCondition` matching an `is_simulation` flag, so it dynamically drops off when you run real-world sensors. 

#### [MODIFY] [navigation.launch.py](file:///home/anubhav-gupta/Chitti/ros_ws/src/chitti_bringup/launch/navigation.launch.py)

### 4. `chitti_bringup/launch/robot.launch.py`
**Issue:** You're required to spin `hardware.launch.py` separately from `navigation.launch.py`, resulting in duplicated processes.
**Fix:** Create a new unified `robot.launch.py` encompassing your ENTIRE robot framework:
- Starts **Real Sensors** (`sensors.launch.py`)
- Starts **Hardware Controllers** (`hardware.launch.py`)
- Starts **Navigation + Routing** (`navigation.launch.py` with `use_fake_sensors=false` and `is_simulation=false`)
*(I will tweak the nested launches so `robot_state_publisher` doesn't inadvertently launch twice and crash!).*

#### [NEW] [robot.launch.py](file:///home/anubhav-gupta/Chitti/ros_ws/src/chitti_bringup/launch/robot.launch.py)

## Open Questions

> [!WARNING]  
> Are your IMU and GPS nodes literally using `nmea_navsat_driver` and standard `mpu9250driver`, or were you planning on writing custom python scripts for the Raspberry Pi I2C buses? If standard packages, I will build out the `package.xml` files with their specific standard executions.

## Verification Plan
1. We will compile and launch the new `robot.launch.py`.
2. Ensure no duplicate TFs exist, no `map`->`odom` static locks exist, and the new `/fix` and `/imu/data` topics are registered inside the environment properly waiting for hardware plugin.
