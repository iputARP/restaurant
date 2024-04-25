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
            retV = RecognizeCommandsRequest.command
            rospy.loginfo(retV)
            if retV == "NO1":
                task = 0
                rospy.set_param("menu/object1", "Apple")  # 当日メニューの名前をここに入れる？
                rospy.set_param("menu/object2", "Orange")
                rospy.set_param("menu/number1","2")
                rospy.set_param("menu/number2","1")
                task_order = 0
            elif retV == "NO2":
                task = 1
                rospy.set_param("menu/object1", "Pringles")
                rospy.set_param("menu/number1","1")
                task_order = 1
            return RecognizeCommandsResponse(True, task, task_order)
        except Exception as e:
            rospy.loginfo(e)
            task = -1
            task_order = -1
            return RecognizeCommandsResponse(False, task, task_order)

if __name__=="__main__":
    RecognitionCommand()
    rospy.spin()
