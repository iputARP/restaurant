#! /usr/bin/env python3

import rospy
from gpsr.srv import PoseDetection
rospy.init_node("pose_detection_client",anonymous=True)
rospy.wait_for_service("person_pose_detection_server")

exec = rospy.ServiceProxy("person_pose_detection_server",PoseDetection)

try:
    a = exec()
    rospy.loginfo(a)
except rospy.ServiceException as e:
    rospy.loginfo(e)