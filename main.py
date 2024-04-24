import rospy
import smach
import smach_ros

from module import smach_state as st



if __name__ == '__main__':
    # まずは一言
    rospy.sleep(1.0)
    # ROSノードの立ち上げてステートマシンクラスのインスタンスを作る。outcomesに渡した文字列がこのステートマシンの終了状態
    #rospy.init_node('state_machine')
    sm_order = smach.StateMachine(outcomes=['success'])
    with sm_order:
        smach.StateMachine.add('INIT', Init(), transitions={'succeeded': 'VISION_CLIENT', 'failed': 'INIT'})
        smach.StateMachine.add('VISION_CLIENT', st.Vision_client(),
                               transitions={'succeeded': 'RECOGNITION', 'failed': 'VISION_CLIENT'})
        smach.StateMachine.add('RECOGNITION', st.Recognition(),
                               transitions={'succeeded': 'GO_TO_CLIENT', 'back': 'VISION_CLIENT',
                                            'failed': 'RECOGNITION'})
        smach.StateMachine.add('GO_TO_CLIENT', st.Go_to_client(),
                               transitions={'succeeded': 'VOICE_ORDER', 'failed': 'GO_TO_CLIENT'})
        smach.StateMachine.add('VOICE_ORDER', st.Voice_order(),
                               transitions={'succeeded': 'success', 'failed': 'VOICE_ORDER'})

    sm_delivery = smach.StateMachine(outcomes=['success'])
    with sm_delivery:
        smach.StateMachine.add('GO_TO_KITCHEN', st.Go_to_kitchen(),
                               transitions={'succeeded': 'VISION_OBJ', 'failed': 'GO_TO_KITCHEN'})
        smach.StateMachine.add('VISION_OBJ', st.Vision_obj(), transitions={'succeeded': 'GRASP', 'failed': 'VISION_OBJ'})
        smach.StateMachine.add('GRASP', st.Grasp(),
                               transitions={'succeeded': 'GO_TO_LOCATION', 'continue': 'GRASP', 'failed': 'GRASP'})
        smach.StateMachine.add('GO_TO_LOCATION', st.Go_to_location(),
                               transitions={'succeeded': 'VISION_DESK', 'failed': 'GO_TO_LOCATION'})
        smach.StateMachine.add('VISION_DESK', st.Vision_desk(),
                               transitions={'succeeded': 'RELEASE_OBJ', 'failed': 'VISION_DESK'})
        smach.StateMachine.add('RELEASE_OBJ', st.Release_obj(),
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



