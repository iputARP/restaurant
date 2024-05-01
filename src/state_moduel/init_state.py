import hsrb_interface
import rospy
import smach
import sys

# ロボット機能を使うための準備
robot = hsrb_interface.Robot()
omni_base = robot.get('omni_base')
whole_body = robot.get('whole_body')
gripper = robot.get('gripper')
tts = robot.get('default_tts')


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