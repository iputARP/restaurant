#! /usr/bin/env python3

import rospy

if __name__=="__main__":
    rospy.init_node("process1")
    while True:
        rospy.loginfo("world")
