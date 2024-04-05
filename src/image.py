#! /usr/bin/env python3

import rospy
from sensor_msgs.msg import Image
from gpsr.srv import QRCodeReader,QRCodeReaderRequest
class ImageData:
    def __init__(self):
        # rospy.Subscriber("/hsrb/head_center_camera/image_raw",Image,self.callback)
        rospy.Subscriber("/hsrb/head_l_stereo_camera/image_raw",Image,self.callback)


    def callback(self,msg):
        pass

    def register_service(self):
        pass


    def exec(self,QRCodeReaderRequest):
        pass
