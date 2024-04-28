#! /usr/bin/env python3

import rospy
rospy.loginfo("Starting human_pose_detector.py")
from visualization_msgs.msg import MarkerArray

class HumanPoseDetector:
    def __init__(self, area):
        self.area = area
        self.callback_count = 0
        self.human_coordinates = []
        self.human_coordinates_count = []
        self.human_poses = []
        self.filtered_coordinates = []
        self.filtered_poses = []
    def register_subscriber(self):
        self.subscriber = rospy.Subscriber("hsrb_visions/target_text_human_pose", MarkerArray, self.callback)
    def unregister_subscriber(self):
        self.subscriber.unregister()
    def callback(self, data):
        self.callback_count += 1
        markers = data.markers
        n = len(markers)
        m = len(self.human_coordinates)
        for i in range(n):
            xy = markers[i].pose.position
            tmp = (xy.x, xy.y)
            area = self.area
            x_min, y_min, x_max, y_max = area
            # 人がarea内にいるかチェック
            if (x_min <= tmp[0] <= x_max) and (y_min <= tmp[1] <= y_max):
                same = False
                for j in range(m):
                    comf = self.human_coordinates[j]
                    if abs(tmp[0]-comf[0]) < 0.5 and abs(tmp[1]-comf[1]) < 0.5:
                        same = True
                        self.human_coordinates_count[j] += 1
                        self.human_poses[j][markers[i].text] += 1
                if not same:
                    self.human_coordinates.append(tmp)
                    self.human_coordinates_count.append(0)
                    self.human_coordinates_count[-1] += 1

                    self.human_poses.append({
                        "Sitting on the Chair": 0,
                        "Waving both hands over head": 0,
                        "Raising one hand": 0,
                        "Standing": 0,
                        "Unknown": 0,
                    })
                    self.human_poses[-1][markers[i].text] += 1

    def get_callback_count(self):
        return self.callback_count

    def get_human_coordinates(self):
        human_coordinates = self.human_coordinates
        filtered_coordinates = self._filter_callback_count(human_coordinates)
        self.filtered_coordinates = filtered_coordinates
        return filtered_coordinates

    def get_human_pose(self):
        human_poses = self.human_poses
        poses = [max(human_pose, key=human_pose.get) for human_pose in human_poses]
        filtered_poses = self._filter_callback_count(poses)
        self.filtered_poses = filtered_poses
        return filtered_poses

    def _filter_callback_count(self, items):
        filtered_items = []
        human_coordinates_count = self.human_coordinates_count
        callback_count_threshold = self.callback_count // 10
        for num, item in zip(human_coordinates_count, items):
            if callback_count_threshold <= num:
                filtered_items.append(item)
        return filtered_items
