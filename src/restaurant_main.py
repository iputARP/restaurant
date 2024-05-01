#--------------------------------------------------------------------------------------------------------
#概要：smate_moduleをimportして各クラスを継承する。継承したクラスを用いて、smachステートを作成と
#      システムの起動を本ファイルで行う。実際の動作処理はすべてstate_module内にて編集よろしくおねがいします。
#
#Date 2024/06/16
#author 岡崎（ok210058）,池田（ok210127）
#--------------------------------------------------------------------------------------------------------

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


import rospy
import smach
import smach_ros

#ステートモジュールの呼び出し。呼びさし先で、実際の処理を記述
from state_moduel.init_state import Init                 #初期化クラス
from state_moduel.vision_client_state import Vision_client     #人認識クラス
from state_moduel.recognition_state import Recognition         #QR読み取りクラス
from state_moduel.go_to_client_state import Go_to_client       #クライアントへの移動クラスDD
from state_moduel.go_to_client2_state import Go_to_client2     #クライアントへの移動クラスDD
from state_moduel.voice_order_state import Voice_order         #音声から命令を読み取るクラス
from state_moduel.judge_order_state import Judge_order         #音声から命令を読み取るクラス
from state_moduel.go_to_kitchen_state import Go_to_kitchen     #キッチンに移動するクラス
from state_moduel.tell_order_state import Tell_order           #従業員に注文を伝えるクラス
from state_moduel.back_to_kitchen_state import Back_to_kitchen #キッチンに戻るクラス
from state_moduel.give_to_client_state import Give_to_client


if __name__ == '__main__':

    #smachを用いたステートマシンの作成    
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



