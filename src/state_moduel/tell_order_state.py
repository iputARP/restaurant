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

# bottleのマーカの手前0.02[m],z軸回に-1.57回転させた姿勢
bottle_to_hand = geometry.pose(z=-0.02, ek=-1.57)

# handを0.1[m]上に移動させる姿勢
hand_up = geometry.pose(x=0.05)

# handを0.5[m]手前に移動させる姿勢
hand_back = geometry.pose(z=-0.5)

# 棚の場所（変更しないといけないかも）
shelf_pos = (3.3, 3.6, 1.57)
# 人に持ってゆく場所（変更しないといけないかも）
desk_pos = (1.9, 0.5, 1.57)

# マイクの取得　…　PCで代用中。HSR本体のマイクに切り替えが必要
r = sr.Recognizer()
mic = sr.Microphone()

# キッチンの座標（仮）
kitchen_x=0
kitchen_y=0
kitchen_z=0

# キッチンの座標判定
judge_kitchen_x = round(kitchen_x, 1)
judge_kitchen_y = round(kitchen_y, 1)
judge_kitchen_z = round(kitchen_z, 1)

# 客の座標（仮）
client_x=0.1
client_y=0.1
client_z=0

# 客の座標判定
judge_client_x=round(client_x, 1)
judge_client_y=round(client_y, 1)
judge_client_z=round(client_z, 1)

# ロボットの現在の座標変数
now_pose_x=0
now_pose_y=0
now_pose_z=0

now_pose_xx=0
now_pose_yy=0
now_pose_zz=0

count1 = 0
count2 = 0
count3 = 0
count4 = 0

order_count = 0

order0 = 0
order1 = 0
order2 = 0

loop1 = 0





class Tell_order(smach.State):################################
    def __init__(self):
        smach.State.__init__(self, outcomes=['succeeded','failed'])

    def execute(self, userdata):

        try:
            tts.say('I will tell order')
            rospy.sleep(2)
            if order_count == 0:
                tts.say(order0)
                rospy.sleep(3)
                tts.say(order1)
                rospy.sleep(3)
                tts.say(order2)
                rospy.sleep(3)
            elif order_count == 1:
                tts.say(order0)
                rospy.sleep(3)
            elif order_count == 2:
                tts.say(order0)
                rospy.sleep(3)
                tts.say(order1)
                rospy.sleep(3)
            return 'succeeded'
            #if rospy.get_param("menu/number") == "1":
             #   tts.say("Coke")
              #  rospy.sleep(3)
            #elif rospy.get_param("menu/number") == "2":
             #   tts.say("Green Tea")
              #  rospy.sleep(3)
            #elif rospy.get_param("menu/number") == "3":
             #   tts.say("Potato Sticks")
              #  rospy.sleep(3)
            #elif rospy.get_param("menu/number") == "4":
             #   tts.say("Chocolate")
              #  rospy.sleep(3)
            #elif rospy.get_param("menu/number") == "5":
             #   tts.say("Green Pepper")
              #  rospy.sleep(3)
            #elif rospy.get_param("menu/number") == "6":
             #   tts.say("Lemon")
              #  rospy.sleep(3)
            #elif rospy.get_param("menu/number") == "7":
             #   tts.say("Bowl")
              #  rospy.sleep(3)
            #elif rospy.get_param("menu/number") == "8":
             #   tts.say("Mug")
              #  rospy.sleep(3)
        except:
            rospy.loginfo('オーダーの発話失敗しました')
            rospy.sleep(3)
            return 'failed'

     #       if loop == 0:
      #          rosparam.set_param("hsrb_visions/target_category",order0)
       #         tts.say("{}認識準備しました。".format(order0))
        #    rospy.sleep(1)
         #   return 'succeeded'
        #except:
         #   tts.say("物体認識失敗")
          #  rospy.sleep(1)
           # return 'failed'
#class Grasp(smach.State):
 #   def __init__(self):
  #      smach.State.__init__(self, outcomes=['succeeded', 'failed'])

   # def execute(self, userdata):

    #    try:
     #       tts.say("物体把持成功")
      #      rospy.sleep(1)
       #     return 'succeeded'
        #except:
         #   tts.say("物体認識失敗")
          #  rospy.sleep(1)
           # return 'failed'