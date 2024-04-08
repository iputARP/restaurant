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
#import vosk #オフライン用音声認識ライブラリ
import tf2_ros
from geometry_msgs.msg import TransformStamped
from numpy import source

#VOSKのモデルパス ここはしょうへいから聞く
#MODEL_PATH =

# ロボット機能を使うための準備
robot = hsrb_interface.Robot()
omni_base = robot.get('omni_base')
whole_body = robot.get('whole_body')
gripper = robot.get('gripper')
tts = robot.get('default_tts')

# bottleのマーカの手前0.02[m],z軸回に-1.57回転させた姿勢
bottle_to_hand = geometry.pose(z=-0.02, ek=-1.57)

# handを0.1[m]上に移動させる姿勢
hand_up = geometry.pose(x=0.1)

# handを0.5[m]手前に移動させる姿勢
hand_back = geometry.pose(z=-0.5)

# 棚の場所（変更しないといけないかも）
shelf_pos = (3.3, 3.6, 1.57)
# 人に持ってゆく場所（変更しないといけないかも）
desk_pos = (1.9, 0.5, 1.57)

# マイクの取得　…　PCで代用中。HSR本体のマイクに切り替えが必要
r = sr.Recognizer()
mic = sr.Microphone()

object_class = 47 #yoloでのクラス分類...初期ではりんごを指定
class Init(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['succeeded','failed']) # 初期化における結果を事前に定義

    def execute(self, userdata):
        # 初期化中である状態をログに残す
        rospy.loginfo('初期化します')
        tts.say('初期化します')
        rospy.sleep(1)
        try:
            #gripper.command(1.0)
            #whole_body.move_to_go()
            rospy.loginfo('初期化に成功')
            tts.say('初期化に成功')
            rospy.sleep(1)
            # tts.say('初期化に成功')
            #tts.say('Initialization succeeded')            
            return 'succeeded' # 'succeeded'という結果を返す．    
        except:
            tts.say('初期化に失敗')
            rospy.logger('fail to init')
            sys.exit()
            return 'failed' # 'failed'という結果を返す

class Vision_client(smach.State):  ###手を振っている判断をもうちょっと考える
    def __init__(self):
        smach.State.__init__(self, outcomes=['succeeded','failed'])

    def execute(self, userdata):
        tts.say('クライアント認識を行います')
        rospy.sleep(1)
        try:
            tts.say('認識成功')
            return 'succeeded'
        except:
            tts.say('認識失敗')
            return 'failed'
class Recognition(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['succeeded','back','failed'])

    def execute(self, userdata):
        tts.say('オーダーとって来てもいいですか？')
        rospy.sleep(2)
        print('say something')
        while True:
            print('Say something.....')
            with mic as source:
                r.adjust_for_ambient_noise(source)  # 雑音対策
                # 音声データ取得
                audio_judge = r.listen(source)

            print('Now to recognize....')
            try: ## if文で認識できてるかできてないかでsucceedとcontinueを分けたい.もしかしたらcontinueがいらなくなるかもif文でバーマンにNoと言われたときのfailedも必要
                # 音声を認識し、文字起こし（オンライン）
                message_judge = r.recognize_google(audio_judge)
                print(message_judge)
                tts.say(message_judge)

                if r.recognize_google(audio_judge) == "yes":
                    tts.say('行ってきます')
                    rospy.sleep(1)
                    return 'succeeded'

                elif r.recognize_google(audio_judge) == "no":
                    tts.say('分かりました。待機します。')
                    rospy.sleep(1)
                    return 'back'

            except sr.UnknownValueError:

                tts.say("could not understand audio")
                rospy.sleep(1)
                tts.say("please say again")
                rospy.sleep(1)

                print("could not understand audio")

                return 'failed'

            except sr.RequestError as e:

                print("Could not request results from Google Speech Recognition service; {0}".format(e))
                return 'failed'

class Go_to_client(smach.State):
    def __init__(self):##手を振っているクライアントにTFをつけてそれをもとに動く？
        smach.State.__init__(self, outcomes=['succeeded','failed'])

    def execute(self, userdata):
        tts.say('客のところまで移動します')
        rospy.sleep(1)
        try:
            #omni_base.go_abs(shelf_pos[0], shelf_pos[1], shelf_pos[2], _MOVE_TIMEOUT)
            tts.say('移動しました')
            rospy.sleep(1)
            return 'succeeded'
        except:
            tts.say('移動に失敗')
            rospy.sleep(1)
            return 'failed'
class Voice_order(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['succeeded','failed'])

    def execute(self, userdata): ##　途中 if文の中でbreak文？タイマーでちょっと時間が経ったら進むこととする
        loop = 0
        count = 0
        seconds = 5

        #def timer(seconds):#5秒超えたらオーダーを終えたとみなす
         #   for i in range(seconds,0,-1):
          #      time.sleep(1)

        #with mic as source:
         #   r.adjust_for_ambient_noise(source)
          #  if count == 0:
           #     audio_order1 = r.listen(source)
            #    tts.say(audio_order1)

        try:
            tts.say("成功")
            rospy.sleep(1)
            return 'succeeded'
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

        except:
                tts.say("失敗")
                rospy.sleep(1)
                return 'failed'

class Go_to_kitchen(smach.State):#一旦タンスの左の一番置くの白テーブルをキッチンと見立てて、そこにプリングルスをおいてやってみる
    def __init__(self):
        smach.State.__init__(self, outcomes=['succeeded','failed'])

    def execute(self, userdata):

        try:
            tts.say("キッチン行ったよ")
            rospy.sleep(1)
            return 'succeeded'
        except:
            tts.say("キッチンいけませんでした")
            rospy.sleep(1)
            return 'failed'
class Vision_obj(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['succeeded','failed'])

    def execute(self, userdata):

        try:
            tts.say("物体認識成功")
            rospy.sleep(1)
            return 'succeeded'
        except:
            tts.say("物体認識失敗")
            rospy.sleep(1)
            return 'failed'
class Grasp(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['succeeded','continue', 'failed'])

    def execute(self, userdata):

        try:
            tts.say("物体把持成功")
            rospy.sleep(1)
            return 'succeeded'
        except:
            tts.say("物体認識失敗")
            rospy.sleep(1)
            return 'failed'
class Go_to_location(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['succeeded', 'failed'])

    def execute(self, userdata):

        try:
            tts.say("特定位置移動成功")
            rospy.sleep(1)
            return 'succeeded'
        except:
            tts.say("特定位置移動成功")
            rospy.sleep(1)
            return 'failed'
class Vision_desk(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['succeeded', 'failed'])

    def execute(self, userdata):

        try:
            tts.say("机認識成功")
            rospy.sleep(1)
            return 'succeeded'
        except:
            tts.say("机認識成功")
            rospy.sleep(1)
            return 'failed'
class Release_obj(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['succeeded','continue', 'failed'])

    def execute(self, userdata):

        try:
            tts.say("物体放下成功")
            rospy.sleep(1)
            return 'succeeded'
        except:
            tts.say("物体放下成功")
            rospy.sleep(1)
            return 'failed'

if __name__ == '__main__':
    # まずは一言
    rospy.sleep(5.0)
    tts.say('Hello')
    rospy.sleep(10.0)
    # ROSノードの立ち上げてステートマシンクラスのインスタンスを作る。outcomesに渡した文字列がこのステートマシンの終了状態
    #rospy.init_node('state_machine')
    sm_order = smach.StateMachine(outcomes=['success'])
    with sm_order:
        smach.StateMachine.add('INIT', Init(), transitions={'succeeded': 'VISION_CLIENT', 'failed': 'INIT'})
        smach.StateMachine.add('VISION_CLIENT', Vision_client(),
                               transitions={'succeeded': 'RECOGNITION', 'failed': 'VISION_CLIENT'})
        smach.StateMachine.add('RECOGNITION', Recognition(),
                               transitions={'succeeded': 'GO_TO_CLIENT', 'back': 'VISION_CLIENT',
                                            'failed': 'RECOGNITION'})
        smach.StateMachine.add('GO_TO_CLIENT', Go_to_client(),
                               transitions={'succeeded': 'VOICE_ORDER', 'failed': 'GO_TO_CLIENT'})
        smach.StateMachine.add('VOICE_ORDER', Voice_order(),
                               transitions={'succeeded': 'success', 'failed': 'VOICE_ORDER'})

    sm_delivery = smach.StateMachine(outcomes=['success'])
    with sm_delivery:
        smach.StateMachine.add('GO_TO_KITCHEN', Go_to_kitchen(),
                               transitions={'succeeded': 'VISION_OBJ', 'failed': 'GO_TO_KITCHEN'})
        smach.StateMachine.add('VISION_OBJ', Vision_obj(), transitions={'succeeded': 'GRASP', 'failed': 'VISION_OBJ'})
        smach.StateMachine.add('GRASP', Grasp(),
                               transitions={'succeeded': 'GO_TO_LOCATION', 'continue': 'GRASP', 'failed': 'GRASP'})
        smach.StateMachine.add('GO_TO_LOCATION', Go_to_location(),
                               transitions={'succeeded': 'VISION_DESK', 'failed': 'GO_TO_LOCATION'})
        smach.StateMachine.add('VISION_DESK', Vision_desk(),
                               transitions={'succeeded': 'RELEASE_OBJ', 'failed': 'VISION_DESK'})
        smach.StateMachine.add('RELEASE_OBJ', Release_obj(),
                               transitions={'succeeded': 'success', 'continue': 'ORDER', 'failed': 'RELEASE_OBJ'})

    all_sm = smach.StateMachine(outcomes=['SUCCEED']) # SUCCEEDが来たら終わり

    with all_sm:
        smach.StateMachine.add('SM_ORDER',sm_order,transitions={'success':'SM_DELIVERY'})
        smach.StateMachine.add('SM_DELIVERY',sm_delivery,transitions={'success':'SUCCEED'})

    sis = smach_ros.IntrospectionServer('server_name', all_sm, '/START')
    sis.start()
    rospy.sleep(1)

    result = all_sm.execute()
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
#オーダーとデリバリーで分けれていないから、一旦一色端にして作る。

