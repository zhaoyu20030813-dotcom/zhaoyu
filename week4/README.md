一、编程基础概念学习
下周将系统学习编程的基础概念，包括变量、数据类型、运算符、条件语句、循环结构以及函数等内容。通过在 Python 环境中进行简单练习，加深对程序执行流程的理解，逐步建立基本的编程思维。同时，掌握基础的调试方法，能够识别并解决常见的语法错误和运行错误。

二、机器人基础概念说明
在机器人相关理论方面，将学习机器人的基本组成与工作原理，包括传感器、执行器、控制系统等核心模块。了解机器人系统中的信息流与控制流程，并初步接触机器人操作系统的基本概念，为后续深入学习 Robot Operating System 打下理论基础。

三、程序运行与实践作业
结合所学编程知识，在 Ubuntu 环境中完成程序的编写与运行练习。通过在 Visual Studio Code 或终端中运行 Python 程序，熟悉从编写、调试到执行的完整流程。同时，根据课程要求完成指定作业任务，确保能够独立运行程序并理解其输出结果。

总体而言，下周的重点在于打牢编程基础，并将理论知识与实际操作相结合，为后续机器人编程与系统开发做好准备。
![alt text](2.png)
![alt text](3.png)
```#!/usr/bin/env python3
"""
让小乌龟走正方形的控制脚本
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import time


class SquareMover(Node):
    """走正方形的控制节点"""

    def __init__(self):
        super().__init__('square_mover')

        # 创建发布者
        self.cmd_vel_pub = self.create_publisher(
            Twist, 
            '/turtle1/cmd_vel', 
            10
        )

        # ============ 参数设置 ============
        self.SPEED = 1.0              # 线速度 m/s
        self.TURN_SPEED = 1.0          # 角速度 rad/s
        self.SIDE_LENGTH = 2.0         # 边长 m

        # 计算运动时间
        self.MOVE_TIME = self.SIDE_LENGTH / self.SPEED
        self.TURN_TIME = 1.5708 / self.TURN_SPEED  # 90° = π/2

        self.get_logger().info('🎯 正方形控制节点启动！')
        self.get_logger().info(f'📐 边长: {self.SIDE_LENGTH}m, 速度: {self.SPEED}m/s')

    def move_straight(self, duration):
        """直行指定时间"""
        self.get_logger().info('→ 直行...')

        msg = Twist()
        msg.linear.x = float(self.SPEED)
        msg.angular.z = 0.0

        # 记录开始时间
        start_time = self.get_clock().now()

        # 持续发布命令
        while (self.get_clock().now() - start_time).nanoseconds < duration * 1e9:
            self.cmd_vel_pub.publish(msg)
            time.sleep(0.01)

        # 停止
        self.stop()
        self.get_logger().info('✓ 直行完成')

    def turn(self, duration):
        """旋转指定时间"""
        self.get_logger().info('↻ 旋转...')

        msg = Twist()
        msg.linear.x = 0.0
        msg.angular.z = float(self.TURN_SPEED)

        start_time = self.get_clock().now()

        while (self.get_clock().now() - start_time).nanoseconds < duration * 1e9:
            self.cmd_vel_pub.publish(msg)
            time.sleep(0.01)

        self.stop()
        self.get_logger().info('✓ 旋转完成')

    def stop(self):
        """停止运动"""
        msg = Twist()
        msg.linear.x = 0.0
        msg.angular.z = 0.0
        self.cmd_vel_pub.publish(msg)
        time.sleep(0.1)

    def move_square(self):
        """执行走正方形"""
        self.get_logger().info('🏁 开始走正方形！')

        for i in range(4):
            self.get_logger().info(f'━━━ 第 {i+1}/4 条边 ━━━')
            self.move_straight(self.MOVE_TIME)

            self.get_logger().info(f'━━━ 第 {i+1}/4 次转弯 ━━━')
            self.turn(self.TURN_TIME)

        self.get_logger().info('🎉 正方形走完！回到起点！')


def main(args=None):
    rclpy.init(args=args)
    node = SquareMover()

    # 给系统一点准备时间
    time.sleep(1)

    # 执行走正方形
    node.move_square()

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()