#! /usr/bin/env python3
import rospy
from gpsr.srv import RecognizeCommands,RecognizeCommandsRequest,RecognizeCommandsResponse



class RecognitionCommand:
    def __init__(self):
        rospy.init_node("RecognizeCommand",anonymous=True)

        rospy.Service("RecognizeCommandServer",RecognizeCommands,self.exec)

    def exec(self,RecognizeCommandsRequest):
        rospy.loginfo(RecognizeCommandsRequest.command)
        task = None
        task_order = None
        try:
            retV = RecognizeCommandsRequest.command.split(" ")
            rospy.loginfo(retV)
            if retV[0] == "Go":
                task = 0
                if retV[11]=="place":
                    rospy.set_param("bring/gotoroom", retV[3])
                    rospy.set_param("bring/graspobject", retV[6])
                    rospy.set_param("bring/gotolocation", retV[9])
                    # .消してる
                    retV[15] = retV[15].strip(".")
                    rospy.set_param("bring/destination", retV[15])
                    task_order = 0
                else:
                    rospy.set_param("bring/gotoroom", retV[3])
                    rospy.set_param("bring/graspobject", retV[6])
                    rospy.set_param("bring/gotolocation", retV[9])
                    # .消してる
                    retV[14] = retV[14].strip(".")
                    rospy.set_param("bring/destination", retV[14])
                    task_order = 1
            elif retV[0] == "Tell":
                task = 1
                if retV[4] != "people":
                    rospy.set_param("vision/countcategory", retV[4])
                    # .消してる
                    retV[9] = retV[9].strip(".")
                    rospy.set_param("vision/placepose", retV[9])
                    task_order = 0
                else:
                    rospy.set_param("vision/countcategory", retV[7])
                    # .消してる
                    retV[9] = retV[9].strip(".")
                    rospy.set_param("vision/placepose", retV[9])
                    task_order = 1
            return RecognizeCommandsResponse(True, task,task_order)
        except Exception as e:
            rospy.loginfo(e)
            task = -1
            task_order = -1
            return RecognizeCommandsResponse(False,task,task_order)

if __name__=="__main__":
    RecognitionCommand()
    rospy.spin()
