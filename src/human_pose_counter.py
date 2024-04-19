#! /usr/bin/env python3

import rospy
rospy.loginfo("Starting human_pose_counter.py")
from visualization_msgs.msg import MarkerArray

class HumanPoseCounter:
    def __init__(self):
        self.count = 0
        self.human_coordinates = []
        self.human_poses = []
    def register_subscriber(self):
        self.subscriber = rospy.Subscriber("hsrb_visions/target_text_human_pose", MarkerArray, self.callback)
    def unregister_subscriber(self):
        self.subscriber.unregister()
    def callback(self, data):
        self.count += 1
        markers = data.markers
        n = len(markers)
        m = len(self.human_coordinates)
        tmp_human_coordinates = [markers[i].pose.position.y for i in range(n)]
        same = False
        for i in range(n):
            tmp = tmp_human_coordinates[i]
            for j in range(m):
                comf = self.human_coordinates[j]
                if abs(tmp-comf) < 0.3:
                    same = True
                    self.human_poses[j][markers[i].text] += 1
            if not same:
                self.human_coordinates.append(tmp)
                self.human_poses.append({
                    "Sitting on the Chair": 0,
                    "Waving both hands over head": 0,
                    "Raising one hand": 0,
                    "Standing": 0,
                    "Unknown": 0,
                })

        # rospy.loginfo(f"data.markers.pose.position.y_list: {tmp_human_coordinates}")
        # rospy.loginfo(f"左の人のy座標: {data.markers[0].pose.position.y}")


        # rospy.loginfo(f"右の人のy座標: {data.markers[1].pose.position.y}")
    def get_count(self):
        return self.count

    def get_human_coordinates(self):
        human_coordinates = self.human_coordinates
        poses = [max(human_pose, key=human_pose.get) for human_pose in self.human_poses]
        rospy.loginfo(self.human_poses)
        return human_coordinates, poses
