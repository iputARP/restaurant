#! /usr/bin/env python3

import rospy
from gpsr.srv import RecognizeCommands

if __name__=="__main__":
    rospy.init_node("reco_command_node",anonymous=True)

    try:
        rospy.wait_for_service("RecognizeCommandServer")

        exec = rospy.ServiceProxy("RecognizeCommandServer", RecognizeCommands)

        a = exec("Tell me how many people in the roomF are peace.")
        rospy.loginfo(a)
    except rospy.ServiceException as e:
        rospy.loginfo(e)



