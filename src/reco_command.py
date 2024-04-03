#! /usr/bin/env python3
import rospy
from gpsr.srv import RecognizeCommands,RecognizeCommandsRequest,RecognizeCommandsResponse



class RecognitionCommand:
    def __init__(self):
        rospy.init_node("RecognizeCommand",anonymous=True)

        rospy.Service("RecognizeCommandServer",RecognizeCommands,self.exec)

    def exec(self,RecognizeCommandsRequest):
        task = None
        try:
            retV = RecognizeCommandsRequest.command.split(" ")
            rospy.loginfo(retV)
            if retV[0] == "Go":
                task = 0
                if retV[11]=="place":
                    rospy.set_param("bring/gotoroom", retV[3])
                    rospy.set_param("bring/graspobject", retV[6])
                    rospy.set_param("bring/gotolocation", retV[9])
                    rospy.set_param("bring/destination", retV[15])
                else:
                    rospy.set_param("bring/gotoroom", retV[3])
                    rospy.set_param("bring/graspobject", retV[6])
                    rospy.set_param("bring/gotolocation", retV[9])
                    rospy.set_param("bring/destination", retV[14])
            elif retV[0] == "Tell":
                task = 1
                if retV[4] != "people":
                    rospy.set_param("vision/countcategory", retV[4])
                    rospy.set_param("vision/placepose", retV[9])
                else:
                    rospy.set_param("vision/countcategory", retV[7])
                    rospy.set_param("vision/placepose", retV[9])
            return RecognizeCommandsResponse(True, task)
        except Exception as e:
            rospy.loginfo(e)
            task=-1
            return RecognizeCommandsResponse(False,task)

if __name__=="__main__":
    RecognitionCommand()
    rospy.spin()
