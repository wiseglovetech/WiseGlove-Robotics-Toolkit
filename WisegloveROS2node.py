#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
商业级 ROS2 节点集成方案
项目名称：Wiseglove / WiseForce5D 具身智能标准双向 ROS2 驱动中间件
功能描述：基于 WGDevice 面向对象类，实现“手指角度/姿态/力触觉”的高频发布，
         同时订阅机器人的反向力矩，实现端到端的力反馈闭环。
如果您有疑问, 欢迎联系我们获取更多资料@wechat: wiseglove
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, Int32MultiArray, ByteMultiArray
from geometry_msgs.msg import PoseArray, Pose

import sys
import os

# 假设你们的 WGDevice 类保存在当前目录下的 ubuntuglovefunc.py 中
# from ubuntuglovefunc import WGDevice

# 为了保证脚本完整性，在此处直接使用您封装好的类（运行前确保 libwiseglove.so 路径正确）
# [此处已隐式包含您的 WGDevice 类声明]

class WiseForce5DROS2Bridge(Node):
    def __init__(self):
        super().__init__('wiseforce5d_ros2_bridge')
        
        # 1. 声明并获取 ROS2 外部参数
        self.declare_parameter('port', '/dev/ttyUSB0')
        self.declare_parameter('lib_path', './libwiseglove.so')
        
        port_name = self.get_parameter('port').get_parameter_value().string_value
        lib_path = self.get_parameter('lib_path').get_parameter_value().string_value
        
        # 2. 实例化您编写的 WGDevice 类，自动完成 C++ 对象创建与函数签名注册
        try:
            self.device = WGDevice(lib_path=lib_path)
            self.get_logger().info("libwiseglove.so 动态库加载成功，C++对象已安全实例化。")
        except Exception as e:
            self.get_logger().error(f"驱动初始化失败: {e}")
            sys.exit(1)
            
        # 3. 开启硬件设备通信端口
        if not self.device.open(port_name):
            self.get_logger().error(f"串口 {port_name} 打开失败！请检查连接或免Root权限配置。")
            sys.exit(1)
            
        # 4. 打印并记录硬件资产信息（用于 B 端客户设备日志审计）
        self.num_finger = self.device.get_num_of_finger()
        self.num_arm = self.device.get_num_of_arm()
        self.num_pressure = self.device.get_num_of_pressure()
        
        self.get_logger().info("==============================================")
        self.get_logger().info(f"设备成功上线 | 厂家: {self.device.get_manu()} | 型号: {self.device.get_model()} | 序列号: {self.device.get_sn()}")
        self.get_logger().info(f"传感器拓扑 -> 角度轴: {self.num_finger} | 空间IMU: {self.num_arm} | 触觉阵列: {self.num_pressure}")
        self.get_logger().info("==============================================")

        # 5. 【数据输出端】创建 ROS2 行业标准发布话题（Topics）
        # 适用于：驱动宇树/智元等人形机器人的多自由度灵巧手
        self.angle_pub = self.create_publisher(Float32MultiArray, '~/finger_angles', 10)
        # 适用于：控制 6自由度/双臂 机械臂的空间主从随动
        self.pose_pub = self.create_publisher(PoseArray, '~/arm_poses', 10)
        # 适用于：大模型的多模态触觉感知训练（Tactile Policy）
        self.pressure_pub = self.create_publisher(Int32MultiArray, '~/tactile_pressures', 10)
        
        # 6. 【控制输入端】订阅机械臂末端传回的实时力矩，驱动 WiseForce5D 外骨骼进行力反馈
        # 客户的机器人控制算法只需往此 Topic 发送 [f1, f2, f3, f4, f5] 的力矩数据，手套即可实时出力
        self.feedback_sub = self.create_subscription(
            Int32MultiArray, 
            '~/set_force_feedback', 
            self.feedback_callback, 
            10
        )

        # 7. 创建高频定时器：严格匹配外骨骼 80Hz 的无线数据更新率 (1/80s = 0.0125s)
        self.timer = self.create_timer(0.0125, self.sync_and_publish_loop)
        
    def sync_and_publish_loop(self):
        """全模态数据同步流：无阻塞并行采集与广播"""
        # 1. 发布手指角度
        if self.num_finger > 0:
            ret, angles = self.device.get_angle()
            if ret > 0:
                msg = Float32MultiArray()
                msg.data = angles
                self.angle_pub.publish(msg)
                
        # 2. 发布手臂空间位置四元数 (转换成 ROS 标准 Pose 姿态数组)
        if self.num_arm > 0:
            ret, quats = self.device.get_quat()
            if ret > 0:
                pose_array_msg = PoseArray()
                pose_array_msg.header.stamp = self.get_clock().now().to_msg()
                pose_array_msg.header.frame_id = "world"
                
                for i in range(self.num_arm):
                    idx = i * 4
                    pose = Pose()
                    pose.orientation.w = quats[idx]
                    pose.orientation.x = quats[idx+1]
                    pose.orientation.y = quats[idx+2]
                    pose.orientation.z = quats[idx+3]
                    pose_array_msg.poses.append(pose)
                self.pose_pub.publish(pose_array_msg)
                
        # 3. 发布手掌力触觉原始数据
        if self.num_pressure > 0:
            ret, pressures = self.device.get_pressure_raw()
            if ret > 0:
                msg = Int32MultiArray()
                msg.data = pressures
                self.pressure_pub.publish(msg)

    def feedback_callback(self, msg):
        """力反馈回调函数：接收机器人算法指令，控制外骨骼电机出力"""
        try:
            # 将接收到的常规整型力矩列表，安全转换为 C++ 需要的 ubyte 数组数据
            force_data = [max(0, min(255, int(f))) for f in msg.data] # 限幅在 0-255 的 ubyte 范围内
            
            # 直接调用您编写的类方法，通过 2.4G 无线将力矩发给外骨骼手套
            self.device.set_feedback(force_data)
            
        except Exception as e:
            self.get_logger().warn(f"力反馈控制指令执行异常: {e}")

    def destroy_node(self):
        self.get_logger().info("正在安全断开连接...")
        self.device.close()
        # 依靠您在 WGDevice 中编写的 __del__ 析构函数，系统会自动安全释放 C++ 内存对象
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = WiseForce5DROS2Bridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
