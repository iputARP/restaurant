#!/usr/bin/env python3

import rospy
import smach
import smach_ros


# define state Foo
class Foo(smach.State):
    def __init__(self):
        smach.State.__init__(self,
                             outcomes=['outcome1', 'outcome2'],
                             input_keys=['foo_counter_in'],
                             output_keys=['foo_counter_out'])

    def execute(self, userdata):
        rospy.loginfo('Executing state FOO')
        if userdata.foo_counter_in < 3:
            userdata.foo_counter_out = userdata.foo_counter_in + 1
            return 'outcome1'
        else:
            return 'outcome2'


# define state Bar
class Bar(smach.State):
    def __init__(self):
        smach.State.__init__(self,
                             outcomes=['outcome1'],
                             input_keys=['bar_counter_in','bar_result'],
                             output_keys=['barbar'])

    def execute(self, userdata):
        rospy.loginfo('Executing state BAR')
        rospy.loginfo('Counter = %f' % userdata.bar_counter_in)
        rospy.loginfo(userdata.bar_result)
        userdata.barbar = 500
        # rospy.loginfo(userdata.barbar)
        return 'outcome1'

class AAA(smach.State):
    def __init__(self):
        smach.State.__init__(self,outcomes=["outcome0"],input_keys=["aaa_in","bbb_in","ccc_in"])

    def execute(self, userdata):
        rospy.loginfo(userdata.aaa_in)
        rospy.loginfo(userdata.bbb_in)
        rospy.loginfo(userdata.ccc_in)
        return 'outcome0'

def main():
    rospy.init_node('smach_example_state_machine')

    # Create a SMACH state machine
    sm = smach.StateMachine(outcomes=['outcome4'])
    sm.userdata.sm_counter = 0
    sm.userdata.sm_result = 30
    sm.userdata.sm_barbar = 0
    # Open the container
    with sm:
        # Add states to the container
        smach.StateMachine.add('FOO', Foo(),
                               transitions={'outcome1': 'BAR',
                                            'outcome2': 'AAA'},
                               remapping={'foo_counter_in': 'sm_counter',
                                          'foo_counter_out': 'sm_counter'})
        smach.StateMachine.add('BAR', Bar(),
                               transitions={'outcome1': 'FOO'},
                               remapping={'bar_counter_in': 'sm_counter',
                                          'bar_result':'sm_result',
                                          'barbar':'sm_barbar'})
        smach.StateMachine.add("AAA",AAA(),
                               transitions={"outcome0":"outcome4"},
                               remapping={"aaa_in":"sm_counter","bbb_in":"sm_result","ccc_in":"sm_barbar"})

    # Execute SMACH plan
    outcome = sm.execute()
    rospy.loginfo("end")


if __name__ == '__main__':
    main()
    # rospy.loginfo("end")