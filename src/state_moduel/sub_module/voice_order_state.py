#!/usr/bin/env python3

#コメント
###スタートフェーズ

#ロボットをスタートロケーションへ移動（？？？）マップ生成から？
#スタート

###オーダーフェイズ

#1:クライアントが手を振り、ロボットがそれに反応する
#2:ロボットは「呼ばれていること」を違う人（バーマン）に伝える。そしてバーマンにオーダーを取りに行っていいかを聞く。Yesなら３へ進み　Noなら１へ戻る
#3:ロボットがクライアントのもとへ移動する　ここで座標とって、代入する？
#4:クライアントからオーダーを取る。オーダーの数は最大３つ。ロボットはオーダー内容を発話で反復して確認する
#5:キッチンに移動しバーマンにオーダーを伝える。

###デリバリーフェーズ

#1:ロボットはキッチンに置かれている複数のオブジェクトからオーダーされたものを把持する。(カスタムコンテナの使用OK)
#2:クライアントのところへ戻る
#3:オブジェクトを配膳するがクライアントのテーブルに置かないといけない
#4:バーマンのところへ戻る。1回目の場合「オーダーフェーズ」へ　２回目なら「終了」


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


class Voice_order(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['succeeded'],output_keys=['cmdstring','tasknum','task_order'])
        rospy.wait_for_service("qr_reader_server")
        self.qr_reader_exec = rospy.ServiceProxy("qr_reader_server", QRCodeReader)
        rospy.wait_for_service("RecognizeCommandServer")
        self.reco_command_exec = rospy.ServiceProxy("RecognizeCommandServer", RecognizeCommands)

    def execute(self, userdata): ##　途中 if文の中でbreak文？タイマーでちょっと時間が経ったら進むこととする
        whole_body.move_to_neutral()
        commandstring = ""
        # key = int(input("type any key"))

        while True:
            tts.say('What your order')
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
        tts.say("Accepted order")
        rospy.sleep(2)
        return "succeeded"

