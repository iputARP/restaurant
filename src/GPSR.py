#! /usr/bin/env python3

import smach
import smach_ros
import rospy
import hsrb_interface
import math
import area # 場所の情報が辞書型で検索できる
import instruction
import tasklist #Graspとかのやつ enum的に使うつもり
from gpsr.srv import QRCodeReader,QRCodeReaderResponse # QRCode読み取り用srv
from gpsr.srv import RecognizeCommands # 命名理解用
robot = hsrb_interface.Robot()
omni_base = robot.get("omni_base")
whole_body = robot.get('whole_body')
gripper = robot.get('gripper')
tts = robot.get('default_tts')

class WAIT_DOOR_OPEN(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['DoorOpen'])

    def execute(self, ud):
        # int(input("type some key then door opened"))
        return "DoorOpen"


class MOVE_TO_INSTRUCTIONS(smach.State):
    def __init__(self):
        smach.State.__init__(self,outcomes=['MoveToInstructions','GPSREnd'])
        self.counter=0
        self.xyw = instruction.Instruction.InstructionPoints["point0"]

    def execute(self, ud):
        self.counter+=1
        if self.counter==4:
            return "GPSREnd"

        # int(input("type some key then move to instructions"))
        #インストラクションポインとに移動、本番はactionlib server
        # omni_base.go_abs(self.xyw[0],self.xyw[1],self.xyw[2])
        # omni_base.go_abs(3.3,0.5,math.pi/2)
        return "MoveToInstructions"

class UNDERSTANDING_COMMAND(smach.State):
    def __init__(self):
        smach.State.__init__(self,outcomes=['UnderstandingCommand'],output_keys=["cmdstring","tasknum"])

    def execute(self, ud):
        commandstring = ""
        # int(input("type some key then understanding command"))
        # 東くん作成QRコードを読むサービスノード実行する
        # rospy.wait_for_service("qr_reader_server")
        # exec = rospy.ServiceProxy("qr_reader_server", QRCodeReader)
        # while True:
        #     tts.say("今からQRを見る")
        #     rospy.sleep(1)
        #     a = exec()
        #     rospy.loginfo("--------------------------")
        #     rospy.loginfo(a)
        #     # userdata.cmdstring
        #     ud.cmdstring = a.command
        #     commandstring = a.command
        #     rospy.loginfo(a.command)
        #     rospy.loginfo(type(a.command))
        #     rospy.loginfo("--------------------------")
        #     if a.success == True:
        #         break
        #     elif a.success == False:
        #         tts.say("読めない")
        # # 命令を理解するサービスノードを実行する
        # try:
        #     tts.say("理解します")
        #     rospy.wait_for_service("RecognizeCommandServer")
        #
        #     exec = rospy.ServiceProxy("RecognizeCommandServer", RecognizeCommands)
        #     a = exec(commandstring)
        #     rospy.loginfo(a)
        #     ud.tasknum = a.task
        # except rospy.ServiceException as e:
        #     rospy.loginfo(e)
        key = int(input("type 0 or 1 0:Grasp 1:Vision"))
        if key == 0:
            ud.tasknum = tasklist.TaskList.Grasp
        elif key == 1:
            ud.tasknum = tasklist.TaskList.Vision
        return "UnderstandingCommand"


class REPEAT_COMMAND(smach.State):
    def __init__(self):
        smach.State.__init__(self,outcomes=['ExecGrasp','ExecVision'],input_keys=["command","tasknum"])

    def execute(self, ud):
        # 復唱する
        # tts.say(ud.command)
        if ud.tasknum == tasklist.TaskList.Grasp:
            rospy.loginfo("task Grasp execute")
            return "ExecGrasp"
        elif ud.tasknum == tasklist.TaskList.Vision:
            rospy.loginfo("task Vision execute")
            return "ExecVision"


class EXEC_GRASP(smach.State):
    def __init__(self):
        smach.State.__init__(self,outcomes=['FinishCommand'])

    def execute(self, ud):
        key = int(input("type some key then finish grasp"))
        # 物体探索のサービスノード実行

        # 物体の把持のサービスノード実行

        # 把持対象を見る

        # 把持対象のtfをstatic tfにする

        # 指定先への配達するサービスノード実行(場所or個人)

        return "FinishCommand"

class EXEC_VISION(smach.State):
    def __init__(self):
        smach.State.__init__(self,outcomes=['FinishCommand'])

    def execute(self, ud):
        key = int(input("type some key then finish visions"))

        return "FinishCommand"



if __name__ == "__main__":
    print("main")

    sm=smach.StateMachine(outcomes=["END"])
    # tasklistで条件分岐
    sm.userdata.sm_tasknum = None
    # 命令理解,復唱用に使う
    sm.userdata.commandstring = ""
    #

    with(sm):
        smach.StateMachine.add('WAIT_DOOR_OPEN',WAIT_DOOR_OPEN(),transitions={"DoorOpen":"MOVE_TO_INSTRUCTIONS"})
        smach.StateMachine.add('MOVE_TO_INSTRUCTIONS',MOVE_TO_INSTRUCTIONS(),transitions={"MoveToInstructions":"UNDERSTANDING_COMMAND","GPSREnd":"END"})
        smach.StateMachine.add('UNDERSTANDING_COMMAND',UNDERSTANDING_COMMAND(),transitions={"UnderstandingCommand":"REPEAT_COMMAND"},remapping={'cmdstring':'commandstring',"tasknum":"sm_tasknum"})
        smach.StateMachine.add('REPEAT_COMMAND',REPEAT_COMMAND(),transitions={"ExecGrasp":"EXEC_GRASP","ExecVision":"EXEC_VISION"},remapping={"command":"commandstring","tasknum":"sm_tasknum"})
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
