（一）Ubuntu（Linux）终端与目录操作

下周将重点学习 Ubuntu 系统中的基本命令行操作，包括文件与目录管理命令，如 ls、cd、pwd、mkdir、rm 等。通过在终端中的实际操作练习，熟练掌握文件路径的概念（绝对路径与相对路径），并理解 Linux 文件系统的基本结构与层级关系。同时，提高在 Ubuntu 环境下的命令行操作熟练度，为后续开发、调试与工程实践打下基础。

（二）Ubuntu（Linux）学习资料与应用理解

通过查阅相关学习资料，进一步了解 Linux 系统在软件开发领域中的重要作用，尤其是在机器人开发、服务器部署以及嵌入式系统中的广泛应用。重点理解 Linux 的开源特性、多用户机制以及强大的命令行工具生态。同时，认识 Linux 在 Robot Operating System（ROS）中的核心支撑作用，为后续 ROS 学习与机器人系统开发奠定基础。

（三）Panda 机器人运动学展示

在仿真环境中观察并分析 Panda 机械臂的运动学特性。通过运行相关示例程序，理解机械臂各关节的运动方式以及末端执行器在空间中的位置变化过程，从而建立对机器人运动控制的直观认识。这一过程有助于加深对机器人运动学模型的理解，并为后续运动学建模与控制算法学习提供实践基础。

（四）机器人基本概念学习

系统学习机器人运动学的基础概念，包括关节空间与坐标空间的区别，以及正运动学与逆运动学的基本原理：

关节空间：使用关节角度描述机器人状态
坐标空间：使用末端执行器的位置与姿态描述机器人状态
正运动学：已知关节角度，求解末端执行器位置
逆运动学：已知目标位置，求解关节角度

通过理论学习与简单实例分析，逐步建立机器人运动控制的基本数学与逻辑框架。

（五）总体目标

本周学习将从 Linux 基础操作与系统认知出发，逐步过渡到机器人运动学的理解与应用。通过理论学习与仿真实验相结合的方式，加深对机器人系统结构与运动控制原理的理解，为后续机器人编程、控制算法设计以及 ROS 开发打下坚实基础。
```import pybullet as p
import pybullet_data as pd
import time
import math

# --- 1. 환경 초기화 | 环境初始化 | Environment Initialization ---
p.connect(p.GUI)
p.setAdditionalSearchPath(pd.getDataPath())
p.setGravity(0, 0, -9.8) # 표준 Z-Up 중력 | 标准Z轴重力 | Standard Z-Up gravity
p.configureDebugVisualizer(p.COV_ENABLE_GUI, 1)
# 카메라 위치 설정 | 设置摄像头视角 | Set camera view
p.resetDebugVisualizerCamera(1.5, 45, -30, [0.5, 0, 0.65])

# 지면 및 테이블 로드 | 加载地面与桌子 | Load plane and table
p.loadURDF("plane.urdf")
table_pos = [0.5, 0, 0] 
p.loadURDF("table/table.urdf", table_pos, useFixedBase=True)
table_height = 0.625          # 桌面高度
cube_half_height = 0.025       # cube_small.urdf 边长 0.05 m，半高 0.025
cube_start_pos = [0.5, 0.0, table_height + cube_half_height]
cube_start_orientation = p.getQuaternionFromEuler([0, 0, 0])
cube_id = p.loadURDF(
    "cube_small.urdf",
    cube_start_pos,
    cube_start_orientation,
    globalScaling=1.5
)

# 로봇 암 로드 (테이블 위에 고정) | 加载并固定机器人 | Load & fix robot on table
panda_pos = [0.0, 0, 0.625] # Z=0.625는 테이블 높이 | 桌面高度 | Table height
pandaId = p.loadURDF("franka_panda/panda.urdf", panda_pos, useFixedBase=True)
def control_gripper(robot_id, open=True):
    if open:
        target = 0.04   # 张开
    else:
        target = 0.0    # 闭合
    for j in [9, 10]:  # Panda 夹爪两个关节
        p.setJointMotorControl2(
            robot_id,
            j,
            p.POSITION_CONTROL,
            targetPosition=target,
            force=50
        )

# --- 2. 컨트롤 패널 생성 | 创建控制面板 | Create Control Panel ---
# 모드 전환 스위치 (체크 시 IK 모드) | 模式切换开关 | Mode toggle (Checked = IK)
mode_toggle = p.addUserDebugParameter("RUN IK (Checked) / RUN JOINT (Unchecked)", 1, 0, 0)

# A. 데카르트 좌표계 슬라이더 | 笛卡尔坐标滑块 | Cartesian Sliders (X, Y, Z)
p.addUserDebugText("--- CARTESIAN SETTINGS ---", [1.2, 0.5, 1.2], [0,0,1], 1)
ctrl_x = p.addUserDebugParameter("Target_X", 0.3, 0.8, 0.6)
ctrl_y = p.addUserDebugParameter("Target_Y", -0.4, 0.4, 0.0)
ctrl_z = p.addUserDebugParameter("Target_Z", 0.65, 1.2, 0.8)

# B. 관절 공간 슬라이더 | 关节空间滑块 | Joint Space Sliders (J0-J6)
p.addUserDebugText("--- JOINT SETTINGS ---", [1.2, -0.5, 1.2], [0,0.5,0], 1)
joint_params = []
joint_names = ["J0_Base", "J1_Shoulder", "J2_Arm", "J3_Elbow", "J4_Forearm", "J5_Wrist", "J6_Flange"]
# Panda 관절 한계 설정 | 关节限位设置 | Joint limits for Panda
joint_limits = [(-2.89, 2.89), (-1.76, 1.76), (-2.89, 2.89), (-3.07, -0.06), (-2.89, 2.89), (-0.01, 3.75), (-2.89, 2.89)]
for i in range(7):
    joint_params.append(p.addUserDebugParameter(joint_names[i], joint_limits[i][0], joint_limits[i][1], 0.0))

info_id = -1 # 디버그 텍스트 ID | 调试文本ID | Debug text ID

# --- 3. 메인 로직 루프 | 核心逻辑循环 | Main Logic Loop ---
try:
    initial_joints = [0, -0.5, 0, -2.0, 0, 1.5, 0.7]
    for i in range(7):
        p.resetJointState(pandaId, i, initial_joints[i])

    # 让仿真稳定几步
    for _ in range(100):
        p.stepSimulation()

    cid = None
    t = 0.0
    while True:
        # 스위치 상태 확인 | 读取开关状态 | Read mode toggle state
        run_ik = p.readUserDebugParameter(mode_toggle)
        
        if run_ik > 0.5:
    # ---- 自动抓取方块 ----
    # Panda 夹爪目标位置
            print(f"run_ik = {run_ik}, t = {t}")
            above_cube    = [cube_start_pos[0], cube_start_pos[1], cube_start_pos[2] + 0.15]
            approach_cube = [cube_start_pos[0], cube_start_pos[1], cube_start_pos[2] + 0.05]
            lift_cube     = [cube_start_pos[0], cube_start_pos[1], cube_start_pos[2] + 0.25]

            # 动作按时间段
            if t < 2:
                target_pos = above_cube
                control_gripper(pandaId, open=True)
            elif t < 4:
                target_pos = approach_cube
                control_gripper(pandaId, open=True)
            elif t < 6:
                target_pos = approach_cube
                control_gripper(pandaId, open=False)

                ee_pos = p.getLinkState(pandaId, 11)[0]
                dist = sum((a-b)**2 for a,b in zip(ee_pos, approach_cube))**0.5
                print(f"dist={dist:.4f}  EE={[round(x,3) for x in ee_pos]}  target={approach_cube}")
                if dist < 0.05 and cid is None:
                    cid = p.createConstraint(
                        parentBodyUniqueId=pandaId,
                        parentLinkIndex=11,
                        childBodyUniqueId=cube_id,
                        childLinkIndex=-1,
                        jointType=p.JOINT_FIXED,
                        jointAxis=[0,0,0],
                        parentFramePosition=[0,0,0.05],
                        childFramePosition=[0,0,0]
                    )
            elif t < 8:
                target_pos = lift_cube
            else:
                t = 0.0
                if cid is not None:
                    p.removeConstraint(cid)
                    cid = None
                continue

            # IK 计算
            joint_poses = p.calculateInverseKinematics(
                pandaId,
                11,
                target_pos,
                p.getQuaternionFromEuler([math.pi, 0, 0]),
                maxNumIterations=100,
                residualThreshold=0.001
            )
            print(f"joint_poses = {[round(x,3) for x in joint_poses[:7]]}")  # ← 加这行
            for i in range(7):
                p.setJointMotorControl2(
                    pandaId,
                    i,
                    p.POSITION_CONTROL,
                    targetPosition=joint_poses[i],
                    force=5000,
                    maxVelocity=1.0
                )

            t += 1./120.
            mode_str = "AUTO MODE: PICK & PLACE"
        
        else:
    
            for i in range(7):
                target_val = p.readUserDebugParameter(joint_params[i])
                p.setJointMotorControl2(pandaId, i, p.POSITION_CONTROL, target_val, force=500)
            
            mode_str = "CURRENT MODE: JOINT SPACE (Direct)"

        ee_state = p.getLinkState(pandaId, 11)
        curr_p = ee_state[0]

        curr_j = [p.getJointState(pandaId, i)[0] for i in range(7)]

        if info_id != -1:
            p.removeUserDebugItem(info_id)
        
        display_text = f"{mode_str}\n"
        display_text += f"End-Effector [X,Y,Z]: [{curr_p[0]:.2f}, {curr_p[1]:.2f}, {curr_p[2]:.2f}]\n"
        display_text += "-"*30 + "\n"
        display_text += "Real-time Joints (rad):\n" + "\n".join([f"J{i}: {curr_j[i]:.2f}" for i in range(7)])

        info_id = p.addUserDebugText(display_text, [0.4, -0.8, 0.8], [0,0,0], 1.2)

        p.stepSimulation()
        time.sleep(1./120.)

except Exception as e:
    print(f"Error occurred: {e}")
finally:
    p.disconnect()