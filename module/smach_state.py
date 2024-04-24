import hsrb_interface
import rospy
import smach
import smach_ros
import sys

from github.Reaction import Reaction
from hsrb_interface import geometry
import speech_recognition as sr #音声認識ライブラリ
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

        try:
            tts.say("成功")
            rospy.sleep(1)
            return 'succeeded'


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