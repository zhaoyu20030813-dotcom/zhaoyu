import pybullet as p
import pybullet_data
import time
import numpy as np
import math


class QuadrupedController:
    """简单的四足控制器"""

    def __init__(self, robot_id):
        self.robot_id = robot_id

        self.leg_joints = {
            'FR': [0,  1,  2],
            'FL': [4,  5,  6],
            'RR': [8,  9,  10],
            'RL': [12, 13, 14],
        }

        self.stance_height = 0.45
        self.step_height = 0.05
        self.step_length = 0.1

        self.flip_timer = 0.0
        self.flip_phase = "IDLE"

    # =========================
    # gait（简单站立步态）
    # =========================
    def trot_gait(self, t, leg_name, frequency=1.0):
        if leg_name in ['FL', 'RL']:
            hip = 0.4
        else:
            hip = -0.4

        thigh = 0.9
        calf = -1.8

        return [hip, thigh, calf]

    # =========================
    # 统一控制腿
    # =========================
    def set_all(self, hip_l, hip_r, thigh, calf, force=500):
        for leg_name, joint_ids in self.leg_joints.items():
            hip = hip_l if leg_name in ['FL', 'RL'] else hip_r

            for joint_id, angle in zip(joint_ids, [hip, thigh, calf]):
                p.setJointMotorControl2(
                    self.robot_id,
                    joint_id,
                    p.POSITION_CONTROL,
                    targetPosition=angle,
                    force=force
                )

    # =========================
    # flip 状态机
    # =========================
    def flip_update(self, dt):

        self.flip_timer += dt

        if self.flip_phase == "CROUCH":
            self.set_all(0.4, -0.4, 1.3, -2.2, force=600)

            if self.flip_timer > 0.3:
                self.flip_timer = 0
                self.flip_phase = "LAUNCH"

        elif self.flip_phase == "LAUNCH":
            self.set_all(0.4, -0.4, 0.3, -0.6, force=600)

            if self.flip_timer < 2 / 240:
                p.resetBaseVelocity(
                    self.robot_id,
                    linearVelocity=[0, 0, 6.0],
                    angularVelocity=[0, 12, 0]
                )

            if self.flip_timer > 0.15:
                self.flip_timer = 0
                self.flip_phase = "ROTATE"

        elif self.flip_phase == "ROTATE":
            self.set_all(0.4, -0.4, 1.5, -2.6, force=200)

            if self.flip_timer > 0.5:
                self.flip_timer = 0
                self.flip_phase = "LAND"

        elif self.flip_phase == "LAND":
            self.set_all(0.4, -0.4, 0.9, -1.8, force=600)

            if self.flip_timer > 0.4:
                self.flip_timer = 0
                self.flip_phase = "SETTLE"

        elif self.flip_phase == "SETTLE":
            self.set_all(0.4, -0.4, 0.9, -1.8, force=500)

            if self.flip_timer > 2.0:
                self.flip_timer = 0
                self.flip_phase = "IDLE"
                print("落地完成，继续站立")

    # =========================
    # 主控制 step
    # =========================
    def step(self, t):

        if self.flip_phase != "IDLE":
            self.flip_update(1 / 240)
            return

        for leg_name, joint_ids in self.leg_joints.items():
            target_angles = self.trot_gait(t, leg_name)

            for joint_id, angle in zip(joint_ids, target_angles):
                p.setJointMotorControl2(
                    self.robot_id,
                    joint_id,
                    p.POSITION_CONTROL,
                    targetPosition=angle,
                    force=500
                )

    # =========================
    # 开始翻滚
    # =========================
    def start_flip(self):
        if self.flip_phase == "IDLE":
            self.flip_timer = 0
            self.flip_phase = "CROUCH"
            print("开始前空翻！")


# ======================================================
# MAIN
# ======================================================
def main():

    p.connect(p.GUI)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -9.8)
    p.loadURDF("plane.urdf")

    start_orientation = p.getQuaternionFromEuler([math.pi / 2, 0, math.pi / 2])
    robotId = p.loadURDF(
        "laikago/laikago_toes.urdf",
        [0, 0, 1.0],
        start_orientation
    )

    controller = QuadrupedController(robotId)

    t = 0
    dt = 1. / 240.

    # =========================
    # ⭐ 新增：启动等待 + 自动翻滚
    # =========================
    wait_time = 5.0
    start_time = 0.0
    flip_interval = 10.0
    last_flip_time = 0.0

    print("开始仿真：先等待5秒，再每10秒自动空翻")

    try:
        while True:

            # =========================
            # ⭐ 开始等待5秒
            # =========================
            if start_time < wait_time:
                controller.step(t)
                start_time += dt

                p.stepSimulation()
                time.sleep(dt)
                t += dt
                continue

            # =========================
            # ⭐ 自动空翻触发（10秒间隔）
            # =========================
            if controller.flip_phase == "IDLE":
                if t - last_flip_time > flip_interval:
                    controller.start_flip()
                    last_flip_time = t

            controller.step(t)

            p.stepSimulation()
            time.sleep(dt)
            t += dt

    except KeyboardInterrupt:
        print("仿真结束")

    p.disconnect()


if __name__ == '__main__':
    main()