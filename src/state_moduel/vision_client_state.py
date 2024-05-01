import hsrb_interface
import rospy
import smach
from visualization_msgs.msg import MarkerArray

# ロボット機能を使うための準備
robot = hsrb_interface.Robot()
omni_base = robot.get('omni_base')
whole_body = robot.get('whole_body')
gripper = robot.get('gripper')
tts = robot.get('default_tts')


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