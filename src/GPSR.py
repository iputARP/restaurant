#! /usr/bin/env python3

import rospy
import smach
import smach_ros
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
from gpsr.srv import ObjectCount

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
        # インストラクションポインとに移動、本番はactionlib server
        # omni_base.go_abs(self.xyw[0],self.xyw[1],self.xyw[2])
        # omni_base.go_abs(3.3,0.5,math.pi/2)
        return "MoveToInstructions"

class UNDERSTANDING_COMMAND(smach.State):
    def __init__(self):
        smach.State.__init__(self,outcomes=['UnderstandingCommand'],output_keys=["cmdstring","tasknum","task_order"])
        # service関連
        rospy.wait_for_service("qr_reader_server")
        self.qr_reader_exec = rospy.ServiceProxy("qr_reader_server", QRCodeReader)
        rospy.wait_for_service("RecognizeCommandServer")
        self.reco_command_exec = rospy.ServiceProxy("RecognizeCommandServer", RecognizeCommands)

    def execute(self, ud):
        whole_body.move_to_neutral()
        commandstring = ""
        # key = int(input("type any key"))
        # 東くん作成QRコードを読むサービスノードを実行する
        while True:
            tts.say("今からQRを見る")
            a = self.qr_reader_exec()
            rospy.loginfo(a)

            # userdata.cmdstring
            ud.cmdstring = a.command
            commandstring = a.command
            if a.success == True:
                break
            elif a.success == False:
                tts.say("読めません")

        # 命令理解サービスノード実行
        a = self.reco_command_exec(commandstring)
        rospy.loginfo(a)
        ud.tasknum = a.task
        ud.task_order = a.order_task
        return "UnderstandingCommand"



class REPEAT_COMMAND(smach.State):
    def __init__(self):
        smach.State.__init__(self,outcomes=['ExecGraspMoveArea','ExecVision'],input_keys=["command","tasknum"])

    def execute(self, ud):

        rospy.loginfo(ud.command)
        # 復唱する
        tts.say(ud.command)
        if ud.tasknum == tasklist.TaskList.Grasp:
            rospy.loginfo("task Grasp execute")
            return "ExecGraspMoveArea"
        elif ud.tasknum == tasklist.TaskList.Vision:
            rospy.loginfo("task Vision execute")
            return "ExecVision"


class EXEC_GRASP_MOVE_AREA(smach.State):
    def __init__(self):
        smach.State.__init__(self,outcomes=["ExecGraspSearchObj"])


    def execute(self, ud):
        # 移動
        rospy.set_param("hsrb_visions/target_category", rospy.get_param("bring/graspobject"))
        gripper.command(1.2)
        xyw = area.Area.task_space[rospy.get_param("bring/gotolocation")]
        omni_base.go_abs(xyw[0],xyw[1],xyw[2],30)

        return "ExecGraspSearchObj"


class EXEC_GRASP_SEARCH_OBJ(smach.State):
    def __init__(self):
        smach.State.__init__(self,outcomes=["ExecGraspApproach"])
        self.x_width = 0
        # service関連
        rospy.wait_for_service("tidyup_target_server")
        self.target_server_exec = rospy.ServiceProxy("tidyup_target_server", target_tf_service)


    def execute(self, ud):
        # 見る時アーム邪魔なのでどかす
        whole_body.move_to_joint_positions({'arm_roll_joint': 0.5})
        #頭下げ
        whole_body.move_to_joint_positions({'head_tilt_joint': -0.8})
        rospy.sleep(5)
        while True:
            try:
                a = self.target_server_exec()
                rospy.loginfo("{}".format(a))
                if a.flag == True:
                    break
                else:
                    tts.say("視点をずらします")
                    # 視点をずらす操作を入れる
                    # tidy up go_abs 1.69,1.13,math.pi/2 幅はxに1.5 変える幅は0.3ずつ
                    whole_body.gaze_point(point=geometry.Vector3(x=1.69+self.x_width, y=1.8, z=0), ref_frame_id='map')
                    self.x_width=self.x_width+0.3
                    rospy.sleep(10)
                    pass
            except rospy.ServiceException as exc:
                rospy.loginfo(str(exc))

        return "ExecGraspApproach"

class EXEC_GRASP_APPROACH(smach.State):
    def __init__(self):
        smach.State.__init__(self,outcomes=["ExecGrasp","NotFoundStatic"])

    def execute(self, ud):
        try:
            # 物体の把持 ピック上空点
            whole_body.move_end_effector_pose(geometry.pose(z=-0.2), "static_target")
        except Exception as e:
            rospy.loginfo(e)
            return "NoeFoundStatic"
        return "ExecGrasp"


class EXEC_GRASP(smach.State):
    def __init__(self):
        smach.State.__init__(self,outcomes=["Exec_Place_Obj","FailedGrasp"])

    def execute(self, ud):
        try:
            # 物体の把
            whole_body.move_end_effector_pose(geometry.pose(z=-0.02), "static_target")

            # 把持
            gripper.apply_force(0.2)

            # 持ち上げる
            whole_body.move_end_effector_pose(geometry.pose(z=-0.5), "static_target")

        except Exception as e:
            rospy.loginfo(e)
            return "FailedGrasp"
        return "Exec_Place_Obj"


class EXEC_GRASP_PLACE_OBJ(smach.State):
    def __init__(self):
        smach.State.__init__(self,outcomes=["MoveToInstructions"])

    def execute(self, ud):
        # key = int(input("type any key then MoveToInstructions"))
        xyw = area.Area.task_space[rospy.get_param("bring/destination")]
        omni_base.go_abs(xyw[0],xyw[1],xyw[2],30)

        whole_body.move_end_effector_pose(geometry.pose(z=-0.2), "place_target")
        whole_body.move_end_effector_pose(geometry.pose(z=-0.02), "place_target")

        gripper.command(1.2)
        return "MoveToInstructions"


class EXEC_FAILED_GRASP(smach.State):
    def __init__(self):
        smach.State.__init__(self,outcomes=["ExecGraspSearchObj"])

    def execute(self, ud):
        # static tfの座標値見る。
        # みた座標値から少し下がるx or y
        # 腕をどかす
        # 見た座標値を見るように設定する (gaze)
        return "ExecGraspSearchObj"

class EXEC_VISION(smach.State):
    def __init__(self):
        smach.State.__init__(self,outcomes=['FinishCommand',"FailedMove"],input_keys=["task_order"])

    def execute(self, ud):
        rospy.set_param("hsrb_visions/target_category","all")
        # visonタスクの中の find obj / find people のどちらを実行するかkeyで判断
        # key = int(input("type 0 or 1 key then finish repeat exec count command 0:object,1:people"))
        rospy.set_param("/hsrb_vision/target_category", "all")
        key = ud.task_order

        # 物体認識0、人認識1
        if key == 0:

            # カウントする物体カテゴリー名と場所名を取得
            obj_category = rospy.get_param("vision/countcategory")
            place = rospy.get_param("vision/placepose")

            # 場所へ行く
            xyw = area.Area.task_space[place]
            rospy.loginfo(xyw)
            try:
                omni_base.go_abs(xyw[0], xyw[1], xyw[2], 30)
            except Exception as e:
                rospy.loginfo(e)
                return "FailedMove"

            # 頭下げ
            whole_body.move_to_go()
            whole_body.move_to_joint_positions({'head_tilt_joint': -0.8})

            # 検出した物体をカテゴリ指定してカウントする
            rospy.sleep(5)
            rospy.wait_for_service("object_counter_server")
            exec = rospy.ServiceProxy("object_counter_server", ObjectCount)

            obj_num = -1
            try:
                obj_num = exec(obj_category)
            except rospy.ServiceException as exc:
                rospy.loginfo(str(exc))

            rospy.loginfo(f"obj_num:{obj_num}")
            tts.say(f"{place}にある{obj_category}は{obj_num.count}個です")
            rospy.sleep(2)
            return "FinishCommand"


        else:
            rospy.loginfo(f"count people")
            room = rospy.get_param("vision/countcategory")
            pose = rospy.get_param("vision/placepose")
            xyw = area.Area.task_space[room]
            rospy.loginfo(xyw)
            omni_base.go_abs(xyw[0], xyw[1], xyw[2], 30)


        return "FinishCommand"

class EXEC_VISION_FAILED_MOVE(smach.State):
    def __init__(self):
        smach.State.__init__(self,outcomes=["ExecVision"])

    def execute(self, ud):
        # ちょっと動く
        place = rospy.get_param("vision/placepose")
        xyw = area.Area.task_space[place]
        omni_base.go_abs(xyw[0]-0.1,xyw[1]-0.1,xyw[2],30)
        return "ExecVision"



if __name__=="__main__":

    sm = smach.StateMachine(outcomes="END")

    sm = smach.StateMachine(outcomes=["END"])
    # tasklistで条件分岐
    sm.userdata.sm_tasknum = None
    # 命令理解,復唱用に使う
    aaaa = None
    sm.userdata.sm_commandstring = ""
    sm.userdata.sm_task_order = None

    with(sm):
        smach.StateMachine.add('WAIT_DOOR_OPEN', WAIT_DOOR_OPEN(), transitions={"DoorOpen": "MOVE_TO_INSTRUCTIONS"})
        smach.StateMachine.add('MOVE_TO_INSTRUCTIONS', MOVE_TO_INSTRUCTIONS(),
                               transitions={"MoveToInstructions": "UNDERSTANDING_COMMAND", "GPSREnd": "END"})
        smach.StateMachine.add('UNDERSTANDING_COMMAND', UNDERSTANDING_COMMAND(),
                               transitions={"UnderstandingCommand": "REPEAT_COMMAND"},
                               remapping={'cmdstring': 'sm_commandstring', "tasknum": "sm_tasknum",
                                          "task_order": "sm_task_order"})
        smach.StateMachine.add('REPEAT_COMMAND', REPEAT_COMMAND(),
                               transitions={"ExecGraspMoveArea":"EXEC_GRASP_MOVE_AREA", "ExecVision": "EXEC_VISION"},
                               remapping={"command": "sm_commandstring", "tasknum": "sm_tasknum"})
        smach.StateMachine.add('EXEC_GRASP_MOVE_AREA',EXEC_GRASP_MOVE_AREA(),transitions={"ExecGraspSearchObj":"EXEC_GRASP_SEARCH_OBJ"})

        smach.StateMachine.add("EXEC_GRASP_SEARCH_OBJ",EXEC_GRASP_SEARCH_OBJ(),transitions={"ExecGraspApproach":"EXEC_GRASP_APPROACH"})
        smach.StateMachine.add("EXEC_GRASP_APPROACH", EXEC_GRASP_APPROACH(),transitions={"ExecGrasp": "EXEC_GRASP", "NotFoundStatic": "EXEC_GRASP_SEARCH_OBJ"})
        smach.StateMachine.add("EXEC_GRASP",EXEC_GRASP(),transitions={"Exec_Place_Obj":"EXEC_GRASP_PLACE_OBJ","FailedGrasp":"EXEC_FAILED_GRASP"})
        smach.StateMachine.add("EXEC_GRASP_PLACE_OBJ",EXEC_GRASP_PLACE_OBJ(),transitions={"MoveToInstructions":"MOVE_TO_INSTRUCTIONS"})
        smach.StateMachine.add("EXEC_FAILED_GRASP",EXEC_FAILED_GRASP(),transitions={"ExecGraspSearchObj":"EXEC_GRASP_SEARCH_OBJ"})
        smach.StateMachine.add('EXEC_VISION', EXEC_VISION(), transitions={"FinishCommand": "MOVE_TO_INSTRUCTIONS","FailedMove":"EXEC_VISION_FAILED_MOVE"},remapping={"task_order": "sm_task_order"})
        smach.StateMachine.add("EXEC_VISION_FAILED_MOVE",EXEC_VISION_FAILED_MOVE(),transitions={"ExecVision":"EXEC_VISION"})

    sis = smach_ros.IntrospectionServer("server_name", sm, "/START")

    sis.start()
    # rospy.sleep(1)

    result=sm.execute()
    rospy.loginfo("result {}".format(result))
    # rospy.spin()
    sis.stop()
    print("処理終了")