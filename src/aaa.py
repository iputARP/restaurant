#! /usr/bin/env python3

import rospy
from sensor_msgs.msg import Image
import cv2
from cv_bridge import CvBridge
from std_msgs.msg import String

class Qr_Reader:
    def __init__(self):
        self.qcd =cv2.QRCodeDetector()
        self.bridge = CvBridge()
        self.cmd = String()
        rospy.Subscriber("/hsrb/head_center_camera/image_raw", Image, self.callback)
        self.pub = rospy.Publisher("Command_String", String, queue_size=1)
        rospy.spin()

    def callback(self, msg):
        msg = self.bridge.imgmsg_to_cv2(msg)
        ret_qr, decoded_info, points, _ = self.qcd.detectAndDecodeMulti(msg)
        if ret_qr:
            for s, p in zip(decoded_info, points):
                if s:
                    rospy.loginfo(s)
                    self.cmd.data = s
                    self.pub.publish(self.cmd)

# def my_callback(msg):
#     qcd = cv2.QRCodeDetector()
#     bridge = CvBridge()
#     msg = bridge.imgmsg_to_cv2(msg)
#     str = String()
#     ret_qr, decoded_info, points, _ = qcd.detectAndDecodeMulti(msg)
#     if ret_qr:
#         for s, p in zip(decoded_info, points):
#             if s:
#                 print(s)
#                 str.data=s
#                 pub.publish(str)
#                 color = (0, 255, 0)
#             else:
#                 color = (0, 0, 255)


def main():
    rospy.init_node("qr_code_reader_node")
    Qr_Reader()
    rospy.spin()

if __name__ == "__main__":
    main()