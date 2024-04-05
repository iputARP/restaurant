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
from hsrb_tf_service.srv import target_tf_service
from hsrb_interface import geometry

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
        smach.State.__init__(self,outcomes=['UnderstandingCommand'],output_keys=["cmdstring","tasknum","task_order"])

    def execute(self, ud):
        commandstring = ""
        # int(input("type some key then understanding command"))
        # 東くん作成QRコードを読むサービスノード実行する
        rospy.wait_for_service("qr_reader_server")
        exec = rospy.ServiceProxy("qr_reader_server", QRCodeReader)
        while True:
            tts.say("今からQRを見る")
            rospy.sleep(1)
            a = exec()
            rospy.loginfo("--------------------------")
            rospy.loginfo(a)
            # userdata.cmdstring
            ud.cmdstring = a.command
            commandstring = a.command
            rospy.loginfo(a.command)
            rospy.loginfo(type(a.command))
            rospy.loginfo("--------------------------")
            if a.success == True:
                break
            elif a.success == False:
                tts.say("読めない")
        # 命令を理解するサービスノードを実行する
        try:
            tts.say("理解します")
            rospy.wait_for_service("RecognizeCommandServer")

            exec = rospy.ServiceProxy("RecognizeCommandServer", RecognizeCommands)
            a = exec(commandstring)
            rospy.loginfo(a)
            ud.tasknum = a.task
            ud.task_order = a.order_task
        except rospy.ServiceException as e:
            rospy.loginfo(e)
        # key = int(input("type 0 or 1 0:Grasp 1:Vision"))
        # if key == 0:
        #     ud.tasknum = tasklist.TaskList.Grasp
        # elif key == 1:
        #     ud.tasknum = tasklist.TaskList.Vision
        return "UnderstandingCommand"



class REPEAT_COMMAND(smach.State):
    def __init__(self):
        smach.State.__init__(self,outcomes=['ExecGrasp','ExecVision'],input_keys=["command","tasknum"])

    def execute(self, ud):
        # 復唱する
        tts.say(ud.command)
        if ud.tasknum == tasklist.TaskList.Grasp:
            rospy.loginfo("task Grasp execute")
            return "ExecGrasp"
        elif ud.tasknum == tasklist.TaskList.Vision:
            rospy.loginfo("task Vision execute")
            return "ExecVision"


class EXEC_GRASP(smach.State):
    def __init__(self):
        smach.State.__init__(self,outcomes=['FinishCommand'],input_keys=["task_order"])

    def execute(self, ud):
        # key = int(input("type some key then finish grasp"))
        # 物体探索のサービスノード実行 rosparamset→把持対象がある場所移動→target見つけたら、static tf化
        # 移動
        rospy.set_param("hsrb_vision/target_category", rospy.get_param("bring/graspobject"))
        gripper.command(1.2)
        xyw = area.Area.task_space[rospy.get_param("bring/gotolocation")]
        rospy.loginfo(xyw)
        omni_base.go_abs(xyw[0],xyw[1],xyw[2],30)
        #頭下げ
        whole_body.move_to_joint_positions({'head_tilt_joint': -0.8})
        rospy.sleep(5)
        #static tf client 実行
        rospy.wait_for_service("tidyup_target_server")

        exec = rospy.ServiceProxy("tidyup_target_server", target_tf_service)
        try:
            a = exec()
            rospy.loginfo("{}".format(a))
        except rospy.ServiceException as exc:
            rospy.loginfo(str(exc))

        # 物体の把持のサービスノード実行
        whole_body.move_end_effector_pose(geometry.pose(z=-0.2), "static_target")
        whole_body.move_end_effector_pose(geometry.pose(z=-0.02), "static_target")

        # 把持する
        gripper.apply_force(0.2)

        #持ち上げる
        whole_body.move_end_effector_pose(geometry.pose(z=-0.5), "static_target")

        # 指定先への配達するサービスノード実行(場所or個人)
        xyw = area.Area.task_space[rospy.get_param("bring/destination")]
        omni_base.go_abs(xyw[0],xyw[1],xyw[2],30)

        whole_body.move_end_effector_pose(geometry.pose(z=-0.2), "place_target")
        whole_body.move_end_effector_pose(geometry.pose(z=-0.02), "place_target")

        gripper.command(1.2)

        return "FinishCommand"

class EXEC_VISION(smach.State):
    def __init__(self):
        smach.State.__init__(self,outcomes=['FinishCommand'],input_keys=["task_order"])

    def execute(self, ud):
        key = int(input("type some key then finish visions"))

        return "FinishCommand"



if __name__ == "__main__":
    print("main")

    sm=smach.StateMachine(outcomes=["END"])
    # tasklistで条件分岐
    sm.userdata.sm_tasknum = None
    # 命令理解,復唱用に使う
    aaaa=None
    sm.userdata.sm_commandstring = ""
    sm.userdata.sm_task_order = None



    with(sm):
        smach.StateMachine.add('WAIT_DOOR_OPEN',WAIT_DOOR_OPEN(),transitions={"DoorOpen":"MOVE_TO_INSTRUCTIONS"})
        smach.StateMachine.add('MOVE_TO_INSTRUCTIONS',MOVE_TO_INSTRUCTIONS(),transitions={"MoveToInstructions":"UNDERSTANDING_COMMAND","GPSREnd":"END"})
        smach.StateMachine.add('UNDERSTANDING_COMMAND',UNDERSTANDING_COMMAND(),transitions={"UnderstandingCommand":"REPEAT_COMMAND"},remapping={'outputcmd':'sm_commandstring',"tasknum":"sm_tasknum","task_order":"sm_task_order"})
        smach.StateMachine.add('REPEAT_COMMAND',REPEAT_COMMAND(),transitions={"ExecGrasp":"EXEC_GRASP","ExecVision":"EXEC_VISION"},remapping={"command":"sm_commandstring","tasknum":"sm_tasknum"})
        smach.StateMachine.add('EXEC_GRASP',EXEC_GRASP(),transitions={"FinishCommand":"MOVE_TO_INSTRUCTIONS"},remapping={"task_order":"sm_task_order"})
        smach.StateMachine.add('EXEC_VISION',EXEC_VISION(),transitions={"FinishCommand":"MOVE_TO_INSTRUCTIONS"},remapping={"task_order":"sm_task_order"})

    sis=smach_ros.IntrospectionServer("server_name",sm,"/START")




    sis.start()
    # rospy.sleep(1)

    result=sm.execute()
    rospy.loginfo("result {}".format(result))
    # rospy.spin()
    sis.stop()
    print("処理終了")
