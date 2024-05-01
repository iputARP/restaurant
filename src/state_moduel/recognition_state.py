import geometry_msgs
import hsrb_interface
import rospy
import rosparam
import smach
import smach_ros
import random
import sys
import time

from github.Reaction import Reaction
from hsrb_interface import geometry
import speech_recognition as sr #音声認識ライブラリ
from gpsr.srv import QRCodeReader,QRCodeReaderResponse # QRCode読み取り用srv
from gpsr.srv import RecognizeCommands # 命名理解用
#from hsrb_tf_service.srv import target_tf_service,gpsr_place,gpsr_placeRequest
from hsrb_interface import geometry
from visualization_msgs.msg import MarkerArray
#import vosk #オフライン用音声認識ライブラリ
import tf2_ros
from geometry_msgs.msg import TransformStamped
from numpy import source

# ロボット機能を使うための準備
robot = hsrb_interface.Robot()
omni_base = robot.get('omni_base')
whole_body = robot.get('whole_body')
gripper = robot.get('gripper')
tts = robot.get('default_tts')

class Recognition(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['succeeded','failed'],output_keys=['cmdstring','tasknum','task_order'])
        rospy.wait_for_service("qr_reader_server")
        self.qr_reader_exec = rospy.ServiceProxy("qr_reader_server", QRCodeReader)
        rospy.wait_for_service("RecognizeCommandServer")
        self.reco_command_exec = rospy.ServiceProxy("RecognizeCommandServer", RecognizeCommands)

    def execute(self, userdata):
        tts.say('Can I take order?')
        rospy.loginfo('オーダーとってもいいですか？')
        rospy.sleep(2)

        while True:
            rospy.loginfo("今からQRを見る")
            a = self.qr_reader_exec()
            rospy.loginfo(a)

            # userdata.cmdstring
            userdata.cmdstring = a.command
            commandstring = a.command
            if a.success == True:
                break
            elif a.success == False:
                tts.say("I can not recognize")
                rospy.loginfo("読めませんでした")

            # 命令理解サービスノード実行

        a = self.reco_command_exec(commandstring)
        rospy.loginfo(a)
        userdata.tasknum = a.task
        userdata.task_order = a.order_task
        tts.say("Accepted your judge")
        rospy.sleep(2)
        if rospy.get_param("menu/judge") == "Yes":
            tts.say('I leave here')
            rospy.loginfo('I leave here')
            rospy.sleep(2)
            return 'succeeded'
            #return "succeeded"
        elif rospy.get_param("menu/judge") == "No":
            tts.say('I wait here')
            rospy.loginfo('I wait here')
            rospy.sleep(2)
            return "failed"