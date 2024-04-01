#! /usr/bin/env python3

import rospy
from sensor_msgs.msg import Image
from image import ImageData
from gpsr.srv import PoseDetection,PoseDetectionRequest,PoseDetectionResponse
from cv_bridge import CvBridge
import cv2

class Person_Pose_Detection(ImageData):
    def __init__(self):
        self.bridge = CvBridge()
        self.image_data = Image()
        super().__init__()

    def register_service(self):
        rospy.loginfo("register service")
        rospy.Service("person_pose_detection_server",PoseDetection,self.exec)

    def callback(self,msg):
        self.image_data = msg


    # 仕様
    # 手を上げたことを認識したら、True,しなかったら、Falseで返すような処理の流れでお願いします。
    # mediapipeを使う想定なので、ROSメッセージをcv2で使える形に変えているので、cv_image_dataを使ってください
    def exec(self,req):
        # rosのsensor_msgs/Image型のデータ(image_data)をcv2で処理できる型に変換
        cv_image_data = self.bridge.imgmsg_to_cv2(self.image_data)


        # 以下野村くん作成
        try:
            return PoseDetectionResponse(True)
        except Exception as e:
            return PoseDetectionResponse(False)

if __name__ == "__main__":
    rospy.init_node("person_pose_detection_server",anonymous=True)
    person_detect_server = Person_Pose_Detection()
    person_detect_server.register_service()
    rospy.spin()