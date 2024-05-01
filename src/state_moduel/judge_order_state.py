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


#VOSKのモデルパス ここはしょうへいから聞く
#MODEL_PATH =

# 移動のタイムアウト[s]
_MOVE_TIMEOUT=60.0
# 把持力[N]
_GRASP_FORCE=0.2
# ボトルのtf名
_TARGET_TF='static_target'
# グリッパのtf名
_HAND_TF='hand_palm_link'

# ロボット機能を使うための準備
robot = hsrb_interface.Robot()
omni_base = robot.get('omni_base')
whole_body = robot.get('whole_body')
gripper = robot.get('gripper')
tts = robot.get('default_tts')



class Judge_order(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['succeeded','back', 'failed'])

    def execute(self, userdata):#オーダー回数によって保存先を変える。そして、オーダーを終えると、[Yes][No]を聞く[Do you want more]で、noなら終わりyesならreturn backで返す？
        global order_count
        global order0
        global order1
        global order2

        try:
            if order_count == 0:
                order0 = rospy.get_param('menu/object1')
                order_count = 1
            elif order_count == 1:
                order1 = rospy.get_param('menu/object1')
                order_count = 2
            elif order_count == 2:
                order2 = rospy.get_param('menu/object1')
                order_count = 0
            tts.say("Do you want any more?")
            rospy.sleep(3)
            if  rospy.get_param("menu/judge") == "Yes":
                tts.say("I continue to take order")
                rospy.sleep(3)
                return "back"
            elif rospy.get_param("menu/judge") == "No":
                tts.say("I finish to take order")
                rospy.sleep(3)
                return "succeeded"
        except :
            if order_count == 0:
                rospy.loginfo("オーダー処理失敗1")
            elif order_count == 1:
                rospy.loginfo("オーダー処理失敗2")
            elif order_count == 2:
                rospy.loginfo("オーダー処理失敗3")
            return "failed"