#! /usr/bin/env python3

import smach
import smach_ros
import rospy
import hsrb_interface
import math


robot = hsrb_interface.Robot()
omni_base = robot.get("omni_base")
whole_body = robot.get('whole_body')
gripper = robot.get('gripper')
tts = robot.get('default_tts')

class WAIT_DOOR_OPEN(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['DoorOpen'])

    def execute(self, ud):
        int(input("type some key then door opened"))
        return "DoorOpen"


class MOVE_TO_INSTRUCTIONS(smach.State):
    def __init__(self):
        smach.State.__init__(self,outcomes=['MoveToInstructions','GPSREnd'])
        self.counter=0

    def execute(self, ud):
        self.counter+=1
        if self.counter==4:
            return "GPSREnd"

        int(input("type some key then move to instructions"))
        #インストラクションポインタに移動、本番はactionlib server
        # omni_base.go_abs(3.3,0.5,math.pi/2)
        return "MoveToInstructions"

class UNDERSTANDING_COMMAND(smach.State):
    def __init__(self):
        smach.State.__init__(self,outcomes=['UnderstandingCommand'])

    def execute(self, ud):
        int(input("type some key then understanding command"))
        # 東くん作成QRコードを読むサービスノード実行する
        # 命令を理解するサービスノードを実行する
        return "UnderstandingCommand"


class REPEAT_COMMAND(smach.State):
    def __init__(self):
        smach.State.__init__(self,outcomes=['ExecGrasp','ExecVision'])

    def execute(self, ud):
        key = int(input("type 0 or 1 key then finish repeat exec understood command 0:grasp,1:vision"))
        # 復唱する
        # tts.say()
        if key==0:
            return "ExecGrasp"
        elif key==1:
            return "ExecVision"


class EXEC_GRASP(smach.State):
    def __init__(self):
        smach.State.__init__(self,outcomes=['FinishCommand'])

    def execute(self, ud):
        key = int(input("type some key then finish grasp"))
        # 物体探索のサービスノード実行
        # 物体の把持のサービスノード実行
        # 指定先への配達するサービスノード実行(場所or個人)
        return "FinishCommand"

class EXEC_VISION(smach.State):
    def __init__(self):
        smach.State.__init__(self,outcomes=['FinishCommand'])

    def execute(self, ud):
        key = int(input("type some key then finish visions"))
        
        return "FinishCommand"



if __name__ == "__main__":
    rospy.init_node("GPSR")
    print("main")

    sm=smach.StateMachine(outcomes=["END"])

    with(sm):
        smach.StateMachine.add('WAIT_DOOR_OPEN',WAIT_DOOR_OPEN(),transitions={"DoorOpen":"MOVE_TO_INSTRUCTIONS"})
        smach.StateMachine.add('MOVE_TO_INSTRUCTIONS',MOVE_TO_INSTRUCTIONS(),transitions={"MoveToInstructions":"UNDERSTANDING_COMMAND","GPSREnd":"END"})
        smach.StateMachine.add('UNDERSTANDING_COMMAND',UNDERSTANDING_COMMAND(),transitions={"UnderstandingCommand":"REPEAT_COMMAND"})
        smach.StateMachine.add('REPEAT_COMMAND',REPEAT_COMMAND(),transitions={"ExecGrasp":"EXEC_GRASP","ExecVision":"EXEC_VISION"})
        smach.StateMachine.add('EXEC_GRASP',EXEC_GRASP(),transitions={"FinishCommand":"MOVE_TO_INSTRUCTIONS"})
        smach.StateMachine.add('EXEC_VISION',EXEC_VISION(),transitions={"FinishCommand":"MOVE_TO_INSTRUCTIONS"})

    sis=smach_ros.IntrospectionServer("server_name",sm,"/START")




    sis.start()
    # rospy.sleep(1)

    result=sm.execute()
    rospy.loginfo("result {}".format(result))
    # rospy.spin()
    sis.stop()
    print("処理終了")
