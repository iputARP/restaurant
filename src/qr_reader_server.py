#! /usr/bin/env python3

import rospy
from std_srvs.srv import Trigger,TriggerResponse
import cv2
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from image import ImageData
from gpsr.srv import QRCodeReader,QRCodeReaderResponse,QRCodeReaderRequest

class QR_Reader(ImageData):
    def __init__(self):
        self.qcd =cv2.QRCodeDetector()
        self.bridge = CvBridge()
        self.image_data = Image()
        super().__init__()

    def register_service(self):
        rospy.loginfo("register service")
        rospy.Service("qr_reader_server", QRCodeReader, self.exec)

    def callback(self,msg):
        self.image_data=msg

    # 仕様:
    # 5秒間実行。５秒立っても認識できない場合、falseを返すようにする。
    # 一つ前の認識データと、処理した認識データが同じなら、trueを返す。この判定処理は５回ほど繰り返すこととする。
    def exec(self,req):
        # rosのsensor_msgs/Image型のデータ(image_data)をcv2で処理できる型に変換
        #cv_image_dataを使って、qr_codeを読むやつを作成してください。
        cv_image_data = self.bridge.imgmsg_to_cv2(self.image_data)

        # qrのデータ保存用
        qr_recog_data = None

        # 以下東くん作成
        try:
            rospy.loginfo("qr_reader_server exec")
            return QRCodeReaderResponse(True,qr_recog_data)
        except Exception as e:
            return QRCodeReaderResponse(False, f"failed recognition {e}")


#
# class QR_Reader:
#     def __init__(self):
#         rospy.init_node("qr_reader_server",anonymous=True)
#         self.qcd =cv2.QRCodeDetector()
#         self.bridge = CvBridge()
#         s = rospy.Service("qr_reader_server",QRCodeReader, self.exec)
#         rospy.spin()
#
#
#     # 仕様:
#     # 5秒間実行。５秒立っても認識できない場合、falseを返すようにする。
#     # 一つ前の認識データと、処理した認識データが同じなら、trueを返す。この判定処理は５回ほど繰り返すこととする。
#     def exec(self,QRCodeReaderRequest):
#         # rosのsensor_msgs/Image型のデータ(image_data)をcv2で処理できる型に変換
#         #cv_image_dataを使って、qr_codeを読むやつを作成してください。
#         cv_image_data = self.bridge.imgmsg_to_cv2(QRCodeReaderRequest.image_data)
#
#         # qrのデータ保存用
#         qr_recog_data = None
#
#         # 以下東くん作成
#         try:
#             rospy.loginfo("qr_reader_server exec")
#             return QRCodeReaderResponse(True,qr_recog_data)
#         except Exception as e:
#             return QRCodeReaderResponse(False, f"failed recognition {e}")



if __name__=="__main__":
    rospy.init_node("qr_reader_serber",anonymous=True)
    qr=QR_Reader()
    qr.register_service()
    rospy.spin()
