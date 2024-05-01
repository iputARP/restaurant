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


#ステートモジュールの呼び出し。呼びさし先で、実際の処理を記述
from state_moduel.init_state import Init                      #初期化クラス
from state_moduel.vision_client_state import Vision_client    #人認識クラス
from state_moduel.recognition_state import Recognition        #QR読み取りクラス
from state_moduel.go_to_client_state import Go_to_client      #クライアントへの移動クラス
from state_moduel.voice_order_state import Voice_order        #
from state_moduel.judge_order_state import Judge_order
from state_moduel.go_to_kitchen_state import Go_to_kitchen
from state_moduel.tell_order_state import Tell_order
from state_moduel.go_to_client_state import Go_to_client
from state_moduel.back_to_kitchen_state import Back_to_kitchen

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

#visionの失敗カウント
vision_failed_count = 0

rospy.set_param("pose_condition","restaurant")

object_class = 47 #yoloでのクラス分類...初期ではりんごを指定
class Init(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['succeeded','failed']) # 初期化における結果を事前に定義

    def execute(self, userdata):
        # 初期化中である状態をログに残す
        rospy.loginfo('初期化します')
        tts.say('Initializing')
        rospy.sleep(1)
        try:
            gripper.command(0.0)
            whole_body.move_to_neutral()
            rospy.loginfo('初期化に成功')
            tts.say('Initialization succeeded')
            rospy.sleep(1)
            # tts.say('初期化に成功')
            #tts.say('Initialization succeeded')            
            return 'succeeded' # 'succeeded'という結果を返す．    
        except:
            tts.say('Initialization failed')
            rospy.logger('fail to init')
            sys.exit()
            return 'failed' # 'failed'という結果を返す

class Vision_client(smach.State):  ###手を振っている判断をもうちょっと考える
    def __init__(self):
        smach.State.__init__(self, outcomes=['succeeded','failed'])

    def _get_position(self):
        #
        markers = self.msg.markers
        if len(markers) > 0:
            for marker in markers:
                
                #ポーズの種類が手を挙げているであれば座標を取得
                if marker.text == "Raising one hand":

                    # print("Raising one hand")
                    #手を挙げている人の座標に静的座標を設定する
                    self.position = marker.pose.position
                    print(self.position)
                    #座標を登録する
                    self._register_tf()
                    return 'succeeded'

    def _register_tf(self):
       global client_x
       global client_y
       global client_z
       global judge_client_x
       global judge_client_y
       global judge_client_z

       #座標値の代入
       client_x = self.position.x - 0.1
       client_y = self.position.y - 0.1
       client_z = self.position.z

       judge_client_x=round(client_x, 1)
       judge_client_y=round(client_y, 1)
       judge_client_z=round(client_z, 1)
   
    def execute(self, userdata):
        global vision_failed_count
    
        tts.say('Recognize clients')
        rospy.sleep(2)
        tts.say('Please raise your hand')
        rospy.sleep(2)


        try:
            #カメラの高さを調整
            whole_body.move_to_joint_positions({'head_tilt_joint':0.05})  

            #人の座標とポーズの種類を取得。msgに格納
            self.msg = rospy.wait_for_message("human_detection/target_text_human_pose", MarkerArray, timeout=10)
            tts.say('Recognition succeeded')

            #取得してきた人座標リストから手を挙げている人を取得
            self._get_position()
            rospy.sleep(2)

            #顔を元の位置に戻す
            whole_body.move_to_joint_positions({'head_pan_joint':0}) 
            return 'succeeded'
        except:
            #５回失敗したら次の処理へ
            if vision_failed_count >= 5:

                #決め打ちの座標まで移動を行う
                omni_base.go_abs(client_x,client_y,client_z)

                #出てきてもらうように、呼びかける
                tts.say('Please come here to order')
                whole_body.move_to_joint_positions({'head_pan_joint':0}) 
                return 'succeded'
           
            #認証が失敗した場合、見る範囲を変える。
            pan_rad = -1 + vision_failed_count*0.2
            whole_body.move_to_joint_positions({'head_pan_joint':pan_rad}) 
            tts.say('Recognition failed')

            #失敗のカウント
            vision_failed_count += 1
            rospy.sleep(2)
            return 'failed'



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
    #while True:
     #       print('Say something.....')
      #      with mic as source:
       #         r.adjust_for_ambient_noise(source)  # 雑音対策
                # 音声データ取得
        #        audio_judge = r.listen(source)

         #   print('Now to recognize....')
          #  try: ## if文で認識できてるかできてないかでsucceedとcontinueを分けたい.もしかしたらcontinueがいらなくなるかもif文でバーマンにNoと言われたときのfailedも必要
                # 音声を認識し、文字起こし（オンライン）
           #     message_judge = r.recognize_google(audio_judge)
            #    print(message_judge)
             #   tts.say(message_judge)

              #  if r.recognize_google(audio_judge) == "yes":
               #     tts.say('I leave here')
                #    rospy.sleep(1)
                 #   return 'succeeded'

                #elif r.recognize_google(audio_judge) == "no":
                 #   tts.say('I know')
                  #  rospy.sleep(1)
                   # tts.say('I wait here')
                    #rospy.sleep(1)
                    #return 'back'

       #     except sr.UnknownValueError:
        #        tts.say("could not understand audio")
         #       rospy.sleep(1)
          #      tts.say("please say again")
           #     rospy.sleep(1)

            #    print("could not understand audio")

             #   return 'failed'

            #except sr.RequestError as e:
#
 #               print("Could not request results from Google Speech Recognition service; {0}".format(e))
  #              return 'failed'

class Go_to_client(smach.State):
    def __init__(self):##手を振っているクライアントにTFをつけてそれをもとに動く？手フリの位置を変数代入
        smach.State.__init__(self, outcomes=['succeeded','continue','failed'])

    def execute(self, userdata):
        global count1
        if count1 == 0:
            tts.say('I go to client')
            rospy.loginfo('I go to client')
            rospy.sleep(1)
            count1 = 1
       # now_pose = omni_base.pose
        try:
            now_pose_x = float(omni_base.pose[0])
            now_pose_y = float(omni_base.pose[1])
            now_pose_z = float(omni_base.pose[2])
            print(now_pose_x)
            print(now_pose_y)
            print(now_pose_z)
            print(judge_client_x)
            print(judge_client_y)
            print(judge_client_z)
            if judge_client_x == round(now_pose_x, 1):
                if judge_client_y == round(now_pose_y, 1):
                    if judge_client_z == round(now_pose_z, 1):
                        tts.say("I arrived at the client")
                        rospy.loginfo('I arrived at the client')
                        rospy.sleep(1)
                        return 'succeeded'
                    else:
                        rospy.loginfo('移動を続けますね')
                        omni_base.go_abs(client_x, client_y, client_z)
                        return 'continue'
                else:
                    rospy.loginfo('移動を続けますよ')
                    omni_base.go_abs(client_x, client_y, client_z)
                    return 'continue'
            else:
                rospy.loginfo('移動を続けまーーす')
                omni_base.go_abs(client_x, client_y, client_z)
                return 'continue'

        except:
            rospy.loginfo("移動に失敗")
            rospy.sleep(1)
            return 'failed'
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

        #while True:
         #       tts.say("オーダーはなんですか？")
          #      print("Say something...")
           ##        r.adjust_for_ambient_noise(source)
             #       audio_order = r.listen(source)
              #  print("Now to recognizing...")

        #for文で最大３回の２回できるようにして、オーダーを聞いて[0]~[2]までに入れて保存する
        #そして１かいずつオーダーを終えるとまだオーダーがあるかどうかを聞いて、yesなら続行、Noならやめるか２人目に行く
        #for i in 2:
        #try:# ここの分岐考える
                    #if count == 0:
                     #   order0 = r.listen(audio_order)
                        #if order0 == "Apple":
                         #   tts.say(order0)
                          #  rospy.sleep(1)
                    #elif count == 1:
                     #   order1 = r.listen(audio_order)
                      #  if order1 == "orange":
                       #     tts.say(order1)
                        #    rospy.sleep(1)
                    #tts.say("他にオーダーはありますか？")
                    #with mic as source:
                     #   r.adjust_for_ambient_noise(source)  # 雑音対策
                      #  audio_judge = r.listen(source)
                       # if r.recognize_google(audio_judge) == "yes":
                        #    tts.say('わかりました')
                         #   rospy.sleep(1)
                          #  count = count + 1
                           # loop = 1
                            #return 'continue'

                        #elif r.recognize_google(audio_judge) == "no":
            #tts.say('オーダー終了します')
            #rospy.sleep(1)
            #return 'succeeded'

                    # 音声を認識し、文字起こし（オンライン）
             #       message_order1 = r.recognize_google(audio_order1)
                    # 認識したメッセージのオウム返し
              #      tts.say(message_order1)
              #rosparam/set_param("hsrb_visions/target_category", "apple")でとりあえずりんごにする

    #        elif loop == 1:
     #           audio_order2 = r.listen(source)
      #          try:
                    # 音声を認識し、文字起こし（オンライン）
       #             message_order2 = r.recognize_google(audio_order2)
                    # 認識したメッセージのオウム返し
        #            tts.say(message_order2)

    #        else:
     #           audio_order3 = r.listen(source)
      #          try:
                    # 音声を認識し、文字起こし（オンライン）
       #             message_order3 = r.recognize_google(audio_order3)
                    # 認識したメッセージのオウム返し
        #            tts.say(message_order3)

        #except:
         #   tts.say("失敗")
          #  rospy.sleep(1)
           # return 'failed'

class Go_to_kitchen(smach.State):#一旦タンスの左の一番置くの白テーブルをキッチンと見立てて、そこにプリングルスをおいてやってみる
    def __init__(self):
        smach.State.__init__(self, outcomes=['succeeded','continue','failed'])


    def execute(self, userdata):
        global count2
        if count2 == 0:
            tts.say("Go to the kitchen")
            rospy.sleep(1)
            count2 = 1
        try:
            now_pose_xx = float(omni_base.pose[0])
            now_pose_yy = float(omni_base.pose[1])
            now_pose_zz = float(omni_base.pose[2])
            print(now_pose_xx)
            print(now_pose_yy)
            print(now_pose_zz)
            print(judge_kitchen_x)
            print(judge_kitchen_y)
            print(judge_kitchen_z)
            if judge_kitchen_x == round(now_pose_xx, 1):
                if judge_kitchen_y == round(now_pose_yy, 1):
                    if judge_kitchen_z == round(now_pose_zz, 1):
                        tts.say("I arrived at the kitchen")
                        rospy.sleep(1)
                        return 'succeeded'
                    else:
                        rospy.loginfo('移動を続けますよ')
                        omni_base.go_abs(kitchen_x, kitchen_y, kitchen_z)
                        return 'continue'
                else:
                    rospy.loginfo('移動を続けますよ')
                    omni_base.go_abs(kitchen_x, kitchen_y, kitchen_z)
                    return 'continue'
            else:
                rospy.loginfo('移動を続けまーーす')
                omni_base.go_abs(kitchen_x, kitchen_y, kitchen_z)
                return 'continue'

        except:
            rospy.loginfo("移動に失敗")
            rospy.sleep(1)
            return 'failed'

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
class Go_to_client2(smach.State):
    def __init__(self):##手を振っているクライアントにTFをつけてそれをもとに動く？手フリの位置を変数代入
        smach.State.__init__(self, outcomes=['succeeded','continue','failed'])

    def execute(self, userdata):

       # now_pose = omni_base.pose
        try:
            global count3
            if count3 == 0:
                tts.say('I go to client')
                rospy.sleep(1)
                count3 = 1
            now_pose_x = float(omni_base.pose[0])
            now_pose_y = float(omni_base.pose[1])
            now_pose_z = float(omni_base.pose[2])
            print(now_pose_x)
            print(now_pose_y)
            print(now_pose_z)
            print(judge_client_x)
            print(judge_client_y)
            print(judge_client_z)
            if judge_client_x == round(now_pose_x, 1):
                if judge_client_y == round(now_pose_y, 1):
                    if judge_client_z == round(now_pose_z, 1):
                        tts.say("I arrived at the client")
                        rospy.sleep(1)
                        return 'succeeded'
                    else:
                        rospy.loginfo('移動を続けますね')
                        omni_base.go_abs(client_x, client_y, client_z)
                        return 'continue'
                else:
                    rospy.loginfo('移動を続けますよ')
                    omni_base.go_abs(client_x, client_y, client_z)
                    return 'continue'
            else:
                rospy.loginfo('移動を続けまーーす')
                omni_base.go_abs(client_x, client_y, client_z)
                return 'continue'

        except:
            rospy.loginfo("移動に失敗")
            rospy.sleep(1)
            return 'failed'
class Give_to_client(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['succeeded', 'failed'])

    def execute(self, userdata):

        try:
            #omni_base.go_abs()
            tts.say("Raise my arm")
            whole_body.move_to_joint_positions({'arm_lift_joint':0.2})
            rospy.sleep(10)
            whole_body.move_to_neutral()
            return 'succeeded'
        except:
            rospy.loginfo("特定位置移動失敗")
            rospy.sleep(1)
            return 'failed'
class Back_to_kitchen(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['succeeded','second','continue', 'failed'])

    def execute(self, userdata):
        global count4
        global loop1
        if count4 == 0:
            tts.say("Back to the kitchen")
            rospy.loginfo('Back to the kitchen')
            rospy.sleep(1)
            count4 = 1
        try:
            now_pose_xx = float(omni_base.pose[0])
            now_pose_yy = float(omni_base.pose[1])
            now_pose_zz = float(omni_base.pose[2])
            print(now_pose_xx)
            print(now_pose_yy)
            print(now_pose_zz)
            print(judge_kitchen_x)
            print(judge_kitchen_y)
            print(judge_kitchen_z)
            if judge_kitchen_x == round(now_pose_xx, 1):
                if judge_kitchen_y == round(now_pose_yy, 1):
                    if judge_kitchen_z == round(now_pose_zz, 1):
                        tts.say("I arrived at the kitchen")
                        rospy.loginfo('I arrived at the kitchen')
                        rospy.sleep(1)
                        if loop1 == 0:
                            loop1 =1
                            rospy.loginfo("二回目行くよ")#各カウントのリセットを行うのを入れる
                            return 'second'
                        elif loop1 == 1:
                            return 'succeeded'
                    else:
                        rospy.loginfo('移動を続けますよ')
                        omni_base.go_abs(kitchen_x, kitchen_y, kitchen_z)
                        return 'continue'
                else:
                    rospy.loginfo('移動を続けますよ')
                    omni_base.go_abs(kitchen_x, kitchen_y, kitchen_z)
                    return 'continue'
            else:
                rospy.loginfo('移動を続けまーーす')
                omni_base.go_abs(kitchen_x, kitchen_y, kitchen_z)
                return 'continue'

        except:
            rospy.loginfo("移動に失敗")
            rospy.sleep(1)
            return 'failed'
#class Release_obj(smach.State):
 #   def __init__(self):
  #      smach.State.__init__(self, outcomes=['succeeded', 'failed'])

   # def execute(self, userdata):

    #    try:
     #       tts.say("物体放下成功")
      #      rospy.sleep(1)
       #     return 'succeeded'
        #except:
         #   tts.say("物体放下成功")
          #  rospy.sleep(1)
           # return 'failed'

if __name__ == '__main__':
    # まずは一言
    rospy.sleep(2.0)
    tts.say('Hello')
    rospy.sleep(2.0)

    # ROSノードの立ち上げてステートマシンクラスのインスタンスを作る。outcomesに渡した文字列がこのステートマシンの終了状態
    #rospy.init_node('state_machine')
    
    sm = smach.StateMachine(outcomes=['SUCCEED']) # SUCCEEDが来たら終わり
    sm.userdata.sm_tasknum = None
    aaaa = None
    sm.userdata.sm_commandstring = ""
    sm.userdata.sm_task_order = None

    with sm:
        smach.StateMachine.add('INIT',Init(),transitions={'succeeded':'VISION_CLIENT','failed':'INIT'})
        smach.StateMachine.add('VISION_CLIENT',Vision_client(),transitions={'succeeded':'RECOGNITION','failed':'VISION_CLIENT'})
        #smach.StateMachine.add('VISION_CLIENT', Vision_client(),transitions={'succeeded': 'GO_TO_CLIENT', 'failed': 'VISION_CLIENT'})
        smach.StateMachine.add('RECOGNITION',Recognition(),transitions={'succeeded':'GO_TO_CLIENT','failed':'RECOGNITION'})
        #smach.StateMachine.add('RECOGNITION', Recognition(),transitions={'succeeded': 'VOICE_ORDER', 'failed': 'RECOGNITION'})
        smach.StateMachine.add('GO_TO_CLIENT',Go_to_client(),transitions={'succeeded':'VOICE_ORDER','continue':'GO_TO_CLIENT','failed':'GO_TO_CLIENT'})
        #smach.StateMachine.add('GO_TO_CLIENT', Go_to_client(),transitions={'succeeded': 'GO_TO_KITCHEN', 'continue': 'GO_TO_CLIENT','failed': 'GO_TO_CLIENT'})
        smach.StateMachine.add('VOICE_ORDER',Voice_order(),transitions={'succeeded':'JUDGE_ORDER'})
        #smach.StateMachine.add('VOICE_ORDER', Voice_order(), transitions={'succeeded': 'TELL_ORDER'})
        smach.StateMachine.add('JUDGE_ORDER',Judge_order(),transitions={'succeeded':'GO_TO_KITCHEN','back':'VOICE_ORDER','failed':'JUDGE_ORDER'})
        smach.StateMachine.add('GO_TO_KITCHEN', Go_to_kitchen(), transitions={'succeeded': 'TELL_ORDER', 'continue': 'GO_TO_KITCHEN', 'failed': 'GO_TO_KITCHEN'})
        #smach.StateMachine.add('GO_TO_KITCHEN', Go_to_kitchen(),transitions={'succeeded': 'GO_TO_CLIENT2', 'continue': 'GO_TO_KITCHEN','failed': 'GO_TO_KITCHEN'})
        #smach.StateMachine.add('TELL_ORDER', Tell_order(), transitions={'succeeded': 'GO_TO_CLIENT2', 'failed': 'TELL_ORDER'})
        smach.StateMachine.add('TELL_ORDER', Tell_order(),transitions={'succeeded': 'GO_TO_CLIENT2', 'failed': 'TELL_ORDER'})
        smach.StateMachine.add('GO_TO_CLIENT2', Go_to_client2(),transitions={'succeeded': 'GIVE_TO_CLIENT', 'continue': 'GO_TO_CLIENT2','failed': 'GO_TO_CLIENT2'})
        #smach.StateMachine.add('VISION_OBJ', Vision_obj(), transitions={'succeeded': 'GRASP', 'failed': 'VISION_OBJ'})
        #smach.StateMachine.add('GRASP', Grasp(), transitions={'succeeded': 'GO_TO_LOCATION', 'failed': 'GRASP'})
        smach.StateMachine.add('GIVE_TO_CLIENT', Give_to_client(), transitions={'succeeded':'BACK_TO_KITCHEN','failed':'GIVE_TO_CLIENT'})
        smach.StateMachine.add('BACK_TO_KITCHEN', Back_to_kitchen(), transitions={'succeeded':'SUCCEED','second':'VISION_CLIENT','continue':'BACK_TO_KITCHEN','failed':'BACK_TO_KITCHEN'})
        #smach.StateMachine.add('RELEASE_OBJ', Release_obj(), transitions={'succeeded':'SUCCEED','failed':'RELEASE_OBJ'})

    sis = smach_ros.IntrospectionServer('server_name', sm, '/START')
    sis.start()
    rospy.sleep(1)

    result = sm.execute()
    rospy.loginfo('result: %s' % result)
    rospy.spin()
    sis.stop()



###############
#if __name__ == '__main__':
    # まずは一言
#    rospy.sleep(5.0)
#    tts.say('Hello')
#    rospy.sleep(10.0)
    # ROSノードの立ち上げてステートマシンクラスのインスタンスを作る。outcomesに渡した文字列がこのステートマシンの終了状態
    #rospy.init_node('state_machine')
#    sm = smach.StateMachine(outcomes=['SUCCEED']) # SUCCEEDが来たら終わり
#
    # ステートマシンに、ステートの名前、ステートのインスタンス、遷移先を指定
    # 遷移先は、そのステートで指定したoutcomesとそのときの遷移先のステートを書く。
#    with (sm):
#	
#        smach.StateMachine.add('INIT',Init(),transitions={'succeeded':'ORDER','failed':'INIT'})
#        
#        sm_order = smach.StateMachine(outcomes=['done_order'])
#        with sm_order:
#            smach.StateMachine.add('VISION_CLIENT', Vision_client(), transitions={'succeeded':'RECOGNITION','failed':'VISION_CLIENT'})
#            smach.StateMachine.add('RECOGNITION', Recognition(), transitions={'succeeded':'GO_TO_CLIENT','back':'VISION_CLIENT','failed':'RECOGNITION'})
#            smach.StateMachine.add('GO_TO_CLIENT',Go_to_client(), transitions={'succeeded':'VOICE_ORDER','failed':'GO_TO_CLIENT'})
#            smach.StateMachine.add('VOICE_ORDER',Voice_order(), transitions={'succeeded':'done_order','failed':'VOICE_ORDER'})
#        smach.StateMachine.add('ORDER',sm_order, transitions={'done_order':'DELIVERY'})
#        sm_delivery = smach.StateMachine(outcomes=['done_delivery'])
#        with sm_delivery:
#            smach.StateMachine.add('GO_TO_KITCHEN', Go_to_kitchen(), transitions={'succeeded':'VISION_OBJ','failed':'GO_TO_KITCHEN'})
#            smach.StateMachine.add('VISION_OBJ', Vision_obj(), transitions={'succeeded':'GRASP','failed':'VISION_OBJ'})
#            smach.StateMachine.add('GRASP', Grasp(), transitions={'succeeded':'GO_TO_LOCATION','continue':'GRASP','failed':'GRASP'})
#            smach.StateMachine.add('GO_TO_LOCATION', Go_to_location(), transitions={'succeeded':'VISION_DESK','failed':'GO_TO_LOCATION'})
#            smach.StateMachine.add('VISION_DESK', Vision_desk(), transitions={'succeeded':'RELEASE_OBJ','failed':'VISION_DESK'})
#            smach.StateMachine.add('RELEASE_OBJ', Release_obj(), transitions={'succeeded':'done_delivery','continue':'ORDER','failed':'RELEASE_OBJ'})
#        smach.StateMachine.add('DELIVERY',sm_delivery, transitions={'done_delivery':'SUCCEED'})
#
#    sis = smach_ros.IntrospectionServer('server_name', sm, '/START')
#    sis.start()
#    rospy.sleep(1)
#
#    result = sm.execute()
#    rospy.loginfo('result: %s' % result)
#    rospy.spin()
#    sis.stop()

#3/29(金)　次週までにオーダーの音声認識の完成　Onlineマッピングの深堀、あわよくば完成、音声発話は完成してるらしいからそれも聞く。オンラインマッピングのナビゲーションの完成。全体のフローを完成する。それから担当振りする。ロボットとバーマンと注文する人のフロー分けして、それが噛み合うように。カスタムコンテナをどうするか。てさげかばんで本当にできるのか。
#音声認識が難しいからQRコードに変えたらしい。
#オーダーの部分の話（青い服の人にお願いしますとかいう糞意地悪なオーダーがある？）
#マップがある前提で且つ手フリ位置も決め打ち、QRコードでオーダを取るとする。
#現状、rosrun object detectionを走らせつつ、target_tfのノードも走らせつつ、プログラムを走らせている
#スマッチでcontinueで繰り返して目的地へ移動するようにする。（多分hecter_slamを別のターミナルで実行しながら各ステートで目的地に移動しなければならないときに目的地と自己位置を比べて移動させる（５０ｃｍぐらいしか移動しないから））
#ちなみに上の中村先生のやつはexceptに入ってもう一回動かしてやって目的地に行ったらsuccessになるらしい
#仮キッチン（3.0,-0.16,-1.58）tryの中にif文を書いてみたがやっぱり、いきなりexceptに飛ばされた。exceptの中に書かないといけない

#4/20 オンラインマッピングの形ができた。あとオーダーのQRコード化、クライアントまでの移動（手フリ）←前川くんがなんかできてそうやから聞いて導入してみる
#キッチンでの物体把持などは、てさげかばんで、バーマンが入れてくれるからそこのステートはいらないかも
#QRコードのやつは、qr_reader_clientをsmachの中に打ち込んで、qr_reader_serverは別ターミナルで立ち上げる
#そして、動作内容はreco_command.pyのような感じらしい。あとしっかり動いてるかどうかの返り値はqr_reader.srvでboolとstringで判別してるらしい
#一応、qrのサーバーとかその他諸々がうまいこと行かなかった場合、cloneしたら治るかもしれない
# server.py系はrosrun gpsr ~~~.pyで行ける
#大きい手提げかばん用意する
#QRコードプリントする
#移動系の○○へ移動しますを初回だけ発言させる。レイズハンドの認識を導入
#おまじない
#rosrun hector_mapping hector_mapping _map_size:=2048 _map_resolution:=0.05 _pub_map_odom_transform:=false _scan_topic:=/hsrb/base_scan _use_tf_scan_transformation:=false _map_update_angle_thresh:=2.0 _map_update_distance_thresh:=0.10 _scan_subscriber_queue_size:=1 _update_factor_free:=0.39 _update_factor_occupied:=0.85 _base_frame:=base_range_sensor_link map:=/update_map
#rziz
#rosrun rviz rviz  -d `rospack find hsrb_common_launch`/config/hsrb_display_full_hsrb.rviz
#4/27仮にhuman_detectionが５回回して反応しなかったら、決め打ちの値まで移動して、クライアント側から近寄ってきてもらって、という流れにする
