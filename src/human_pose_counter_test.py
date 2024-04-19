#! /usr/bin/env python3

import rospy
from human_pose_counter import HumanPoseCounter

rospy.init_node("human_pose_counter_test", anonymous=True)
rospy.loginfo("Starting human_pose_counter_test.py")
room = "roomA"
pose = "Sitting on the Chair"

hp_counter = HumanPoseCounter()
hp_counter.register_subscriber()
rospy.sleep(1)
count = hp_counter.get_count()
rospy.loginfo(f"class register, count: {count}")
human_coordinates, poses = hp_counter.get_human_coordinates()
rospy.loginfo(f"human_coordinates: {human_coordinates}")
rospy.loginfo(f"human_poses: {poses}")

hp_counter.unregister_subscriber()

