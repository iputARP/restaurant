#! /usr/bin/env python3
import time
import rospy
from human_pose_detector import HumanPoseDetector


rospy.init_node("human_pose_counter_test", anonymous=True)
rospy.loginfo("Starting human_pose_counter_test.py")

# areas = {area名: (x_min, y_min, x_max, y_max), ...}
areas = {"roomA": (0, 0, 4, 2), "roomB": (0, 2, 4, 6)}
room = "roomB"
pose = "Sitting on the Chair"

# 初期化時に人を認識する座標の範囲を指定する
hp_counter = HumanPoseDetector(areas[room])

time1 = time.time()
hp_counter.register_subscriber()
# roomを徘徊するなどの処理
rospy.sleep(1)
hp_counter.unregister_subscriber()
time2 = time.time()
rospy.loginfo(time2 - time1)

callback_count = hp_counter.get_callback_count()
rospy.loginfo(f"class register, callback_count: {callback_count}")
human_coordinates = hp_counter.get_human_coordinates()
poses = hp_counter.get_human_pose()
rospy.loginfo(f"human_coordinates: {human_coordinates}")
rospy.loginfo(f"human_poses: {poses}")
