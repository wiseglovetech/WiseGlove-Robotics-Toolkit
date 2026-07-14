# WiseGlove-Robotics-Toolkit
Python SDK &amp; ROS2 bridge for WiseGlove/WiseForce5D datagloves. Features 80Hz low-latency multi-modal data fusion (19-ch fiber optic tracking, 4-IMU pose estimation, 19-pt tactile sensing) &amp; closed-loop force-feedback exoskeleton control. Built for Embodied AI data collection, humanoid teleoperation, and VR simulation. 
# WiseGlove Robotics Toolkit: Multi-Modal Teleoperation & ROS2 Driver(多模态遥操作ROS系统开发包)
An industrial-grade Python SDK and bidirectional ROS2 middleware for **WiseGlove 19E+** and **WiseForce5D Force-Feedback Exoskeleton Gloves**. Designed for Embodied AI data collection, humanoid dexterous hand tracking, and virtual reality teleoperation.
---
## 🛠️ Prerequisites & Installation

### 1. System Requirements
* **OS:** Ubuntu 20.04 / 22.04 / 24.04 LTS
* **Middleware:** ROS2 (Fumble / Iron / Humble / Jazzy)
* **Python:** 3.8+ (with `ctypes` built-in)

### 2. Device Permissions (Fix Serial Port Access)
To run the driver without root (`sudo`) privileges, add your Linux user to the `dialout` group:
```bash
sudo usermod -aG dialout \$USER
```
*Note: Log out and log back in for the changes to take effect.*

### 3. Install Dependencies
```bash
sudo apt update
sudo apt install python3-pip ros-\$ROS_DISTRO-desktop
```
### 4. Clone & Setup Library Path
Clone this repository to your workspace and ensure the dynamic link library (`libwiseglove.so`) is in the same directory as the execution scripts:
```bash
git clone https://github.com
cd WiseGlove-Robotics-Toolkit
chmod +x libwiseglove.so
```
---
## 🚀 Quick Start Guide
### Step 1: Plug in the Hardware
Connect your WiseGlove or WiseForce5D receiver via USB. Find the serial port name by running:
```bash
ls /dev/ttyUSB* # or ls /dev/ttyCH*
```
*(Default target port is usually `/dev/ttyUSB0`)*
### Step 2: Source your ROS2 Workspace
```bash
source /opt/ros/\$ROS_DISTRO/setup.bash
```
### Step 3: Run the Dual-Control Driver Node
Execute the interactive Python script to launch the synchronous data collection pipeline:
```bash
python3 wiseforce5d_ros2_bridge.py --ros-args -p port:=/dev/ttyUSB0
```
---
## 📡 ROS2 API Reference
### 📤 Published Topics (Data Output)
The driver publishes aligned multi-modal data streams at a steady **80Hz**:
| Topic Name | Message Type | Description |
| :--- | :--- | :--- |
| `~/finger_angles` | `std_msgs/Float32MultiArray` | 19-channel raw joint angles (in degrees) for dexterous hand mapping. |
| `~/arm_poses` | `geometry_msgs/PoseArray` | Arm/Wrist/Palm spatial orientations extracted from the 4-IMU array. |
| `~/tactile_pressures` | `std_msgs/Int32MultiArray` | 19-point tactile force array values (calibrated in grams). |
### 📥 Subscribed Topics (Force-Feedback Input)
To trigger the exoskeleton physical feedback loops on the **WiseForce5D** model, publish torque values to this endpoint:
| Topic Name | Message Type | Description |
| :--- | :--- | :--- |
| `~/set_force_feedback` | `std_msgs/Int32MultiArray` | Accepts a list of 5 integer values `[f1, f2, f3, f4, f5]` bounded between `0` (No Force) and `255` (Max Resistance). |
#### 💡 Quick Torque Test Command:
Open a separate terminal and push physical resistance to the user's thumb and index fingers:
```bash
ros2 topic pub --once /wiseforce5d_ros2_bridge/set_force_feedback std_msgs/msg/Int32MultiArray "{data: [200, 200, 0, 0, 0]}"
```
---
## 📐 Data Handshaking & Calibration
1. **Finger Range Calibration:** Press `r` on your terminal to reset the bounds, then fully flex and extend your hand to map min/max values.
2. **Arm Orientation Zeroing:** Assume an **A-Pose** (arms resting naturally at your sides, facing the screen) and press `r` to lock the 0-degree baseline orientation.
3. **Tactile Zeroing:** Ensure the glove is not touching any surface and press `z` to tare the pressure sensors.
## 📄 License & Attribution
Developed and maintained by our Robotics Studio. For commercial hardware sourcing, custom SDK wrappers, or technical support, please open an issue or contact our business channel.
