#! /usr/bin/env python3

import rospy
from std_srvs.srv import Trigger
from gpsr.srv import QRCodeReader
from sensor_msgs.msg import Image



rospy.init_node("qr_reader_client",anonymous=True)
rospy.wait_for_service("qr_reader_server")

exec = rospy.ServiceProxy("qr_reader_server",QRCodeReader)

# rospy.Subscriber("/hsrb/head_center_camera/image_raw", Image, callback,callback_args=exec)


try:
    a = exec()
    rospy.loginfo(a)
except rospy.ServiceException as e:
    rospy.loginfo(e)


