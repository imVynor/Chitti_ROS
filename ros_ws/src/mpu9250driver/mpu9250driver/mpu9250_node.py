import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
import math

class MPU9250Node(Node):
    def __init__(self):
        super().__init__('mpu9250_node')
        
        self.declare_parameter('i2c_bus', 1)
        self.declare_parameter('i2c_address', 0x68)
        self.declare_parameter('calibrate', True)
        
        try:
            from mpu9250_jmdev.registers import AK8963_ADDRESS, MPU9050_ADDRESS_68, GFS_1000, AFS_8G, AK8963_BIT_16, AK8963_MODE_C100HZ
            from mpu9250_jmdev.mpu_9250 import MPU9250
            
            i2c_bus = self.get_parameter('i2c_bus').get_parameter_value().integer_value
            address = self.get_parameter('i2c_address').get_parameter_value().integer_value
            calibrate = self.get_parameter('calibrate').get_parameter_value().bool_value
            
            self.mpu = MPU9250(
                address_ak=AK8963_ADDRESS, 
                address_mpu_master=address, 
                address_mpu_slave=None, 
                bus=i2c_bus,
                gfs=GFS_1000, 
                afs=AFS_8G, 
                mfs=AK8963_BIT_16, 
                mode=AK8963_MODE_C100HZ
            )
            
            self.mpu.configure()
            
            if calibrate:
                self.get_logger().info('Calibrating IMU... Please keep it flat and still for 5 seconds.')
                self.mpu.calibrate()
                self.get_logger().info('Calibration complete.')
                
            self.is_connected = True
        except ImportError:
            self.get_logger().error("Failed to import mpu9250_jmdev. Install via 'pip3 install mpu9250-jmdev'")
            self.is_connected = False
        except Exception as e:
            self.get_logger().error(f"Failed to initialize MPU9250: {e}")
            self.is_connected = False
            
        self.publisher_ = self.create_publisher(Imu, '/imu/data', 10)
        self.timer = self.create_timer(0.02, self.timer_callback) # 50Hz
        
    def timer_callback(self):
        if not self.is_connected:
            return
            
        try:
            accel = self.mpu.readAccelerometerMaster() # g
            gyro = self.mpu.readGyroscopeMaster()      # deg/s
            mag = self.mpu.readMagnetometerMaster()    # uT
            
            msg = Imu()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = 'imu_link'
            
            msg.linear_acceleration.x = accel[0] * 9.80665
            msg.linear_acceleration.y = accel[1] * 9.80665
            msg.linear_acceleration.z = accel[2] * 9.80665
            
            msg.angular_velocity.x = math.radians(gyro[0])
            msg.angular_velocity.y = math.radians(gyro[1])
            msg.angular_velocity.z = math.radians(gyro[2])
            
            # Simple Tilt-Compensated Heading
            roll = math.atan2(accel[1], accel[2])
            pitch = math.atan2(-accel[0], math.sqrt(accel[1]*accel[1] + accel[2]*accel[2]))
            
            Xh = mag[0] * math.cos(pitch) + mag[2] * math.sin(pitch)
            Yh = mag[0] * math.sin(roll) * math.sin(pitch) + mag[1] * math.cos(roll) - mag[2] * math.sin(roll) * math.cos(pitch)
            yaw = math.atan2(Yh, Xh)
            
            cy = math.cos(yaw * 0.5)
            sy = math.sin(yaw * 0.5)
            cp = math.cos(pitch * 0.5)
            sp = math.sin(pitch * 0.5)
            cr = math.cos(roll * 0.5)
            sr = math.sin(roll * 0.5)

            msg.orientation.w = cr * cp * cy + sr * sp * sy
            msg.orientation.x = sr * cp * cy - cr * sp * sy
            msg.orientation.y = cr * sp * cy + sr * cp * sy
            msg.orientation.z = cr * cp * sy - sr * sp * cy
            
            msg.orientation_covariance[0] = 0.05
            msg.orientation_covariance[4] = 0.05
            msg.orientation_covariance[8] = 0.05
            
            msg.linear_acceleration_covariance[0] = 0.04
            msg.linear_acceleration_covariance[4] = 0.04
            msg.linear_acceleration_covariance[8] = 0.04
            
            msg.angular_velocity_covariance[0] = 0.002
            msg.angular_velocity_covariance[4] = 0.002
            msg.angular_velocity_covariance[8] = 0.002

            self.publisher_.publish(msg)
            
        except Exception as e:
            pass # Suppress temporary read errors over I2C

def main(args=None):
    rclpy.init(args=args)
    node = MPU9250Node()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
