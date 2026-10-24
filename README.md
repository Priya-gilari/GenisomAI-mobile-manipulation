
# ZSL-1W Wheel-Legged Robot — ROS 2 Gazebo Simulation

![ZSL-1W driving in Gazebo](docs/drive.gif)

Simulation of the **GENISOM ZSL-1W** wheel-legged quadruped in **ROS 2 Humble** and **Gazebo Classic**,
as the mobile base for an autonomous mobile-manipulation project (ZSL-1W + AgileX Piper arm).

## Features
- ROS 2 description package built from the manufacturer's URDF (meshes, inertias, 16 joints)
- **Legs (12 joints):** torque-controlled PD via `joint_trajectory_controller` (effort interface),
  smooth stand-up into a computed standing pose
- **Wheels (4 joints):** skid-steer driving via `diff_drive_controller`, publishes odometry and TF
- Keyboard teleoperation with `teleop_twist_keyboard`
- Self-contained Gazebo world (no online model database needed)

## System
| Component | Version |
|---|---|
| OS | Ubuntu 22.04 |
| ROS 2 | Humble |
| Simulator | Gazebo Classic 11 |
| Control | ros2_control, gazebo_ros2_control |

## Installation
```bash
sudo apt install -y ros-humble-gazebo-ros-pkgs ros-humble-gazebo-ros2-control \
  ros-humble-ros2-control ros-humble-ros2-controllers ros-humble-joint-trajectory-controller \
  ros-humble-teleop-twist-keyboard ros-humble-xacro

mkdir -p ~/dog_ws/src && cd ~/dog_ws/src
git clone https://github.com/Priya-gilari/GenisomAI-mobile-manipulation.git zsl1w_description
cd ~/dog_ws
colcon build --packages-select zsl1w_description
source install/setup.bash
```

## Usage
**Start the simulation**
```bash
ros2 launch zsl1w_description gazebo.launch.py
```
**Drive with the keyboard** (second terminal)
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r cmd_vel:=/diff_drive_controller/cmd_vel_unstamped
```
`i` forward · `,` backward · `j`/`l` turn · `k` stop · `q`/`z` speed up/down

**Check the controllers**
```bash
ros2 control list_controllers
```

## Robot parameters
| Parameter | Value |
|---|---|
| Total mass | 20.6 kg |
| Wheel radius | 0.0704 m |
| Wheel separation (left–right) | 0.319 m |
| Wheelbase (front–rear) | 0.349 m |
| Thigh / calf length | 0.200 m / 0.214 m |
| Standing pose (ABAD, HIP, KNEE) | 0.0, 0.8, −1.6 rad |
| Motor limits | 28 Nm, 28 rad/s |

## Package structure
zsl1w_description/
```
├── urdf/
│ ├── ZSL-1W.urdf # robot model (cleaned up from manufacturer URDF)
│ └── zsl1w_gazebo.urdf.xacro # + ros2_control interfaces, Gazebo plugin, wheel friction
├── meshes/ # STL meshes
├── config/controllers.yaml # leg PD gains, diff-drive parameters
├── launch/gazebo.launch.py # Gazebo, spawn, controllers, stand-up sequence
└── worlds/flat.world # ground plane + lighting
```

## How it works
**Startup sequence** (in `gazebo.launch.py`):
1. Spawn the robot at its standing height (0.37 m) with legs in the standing pose
2. Activate `leg_controller` → leg motors hold the joints
3. Send a 2-second trajectory to the standing pose
4. Activate `diff_drive_controller` → wheels respond to `cmd_vel`

The wheels are activated only after standing up, so they can roll freely while the legs extend.

## Engineering notes — problems solved
| Problem | Cause | Fix |
|---|---|---|
| Meshes not found in RViz/Gazebo | URDF used relative paths `../meshes/` | Converted to `package://` paths, added `package.xml` / `CMakeLists.txt` |
| Robot model missing in RViz | German locale (decimal comma) broke number parsing | `LC_NUMERIC=en_US.UTF-8` |
| `mass [0.90130429 ] is not a float` | Trailing spaces in URDF attributes | Stripped with `sed` |
| Gazebo froze on startup | Online model database unreachable | `GAZEBO_MODEL_DATABASE_URI=""` |
| Robot fell through the floor | Default world's `ground_plane` was never loaded | Own world file with a built-in ground plane |
| Robot launched into the air | Position interface in Gazebo *teleports* joints into contact | Effort interface + PD control (`joint_trajectory_controller`) |
| Robot flipped during stand-up | Legs limp before controller start; locked wheels levered the body | Spawn at standing height, legs first, wheels after stand-up |
| Wheel collisions dropped by Gazebo | Mesh collisions lost in URDF→SDF conversion | Replaced with cylinder primitives |

## Roadmap
- [x] Robot description and Gazebo simulation
- [x] Standing and teleoperation
- [ ] 2D LiDAR + SLAM Toolbox mapping
- [ ] Nav2 autonomous navigation with obstacle avoidance
- [ ] Mount AgileX Piper arm (MoveIt 2): retract / extend / scan poses
- [ ] Mission node: navigate → stop → arm scan → retract → repeat
- [ ] Isaac Lab: RL locomotion for the wheel-legged robot

## Credits
Robot model (URDF and meshes) by **GENISOM AI / zsibot**: [zsibot/genisom_model](https://github.com/zsibot/genisom_model).
Simulation setup, control configuration and launch files by Priyadharshini Gilari.

