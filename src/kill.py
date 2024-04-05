#! /usr/bin/env python3
import rospy
from subprocess import Popen
import time
if __name__=="__main__":
    # 切りたいノード名指定
    p=Popen('exec python3 /home/taishin/catkin_ws/src/GPSR/src/process.py',shell=True)
    n=Popen('exec python3 ~/catkin_ws/src/GPSR/src/process1.py',shell=True)
    # waitkey = input("type some key then kill process")
    time.sleep(3)
    p.kill()
    time.sleep(3)
    n.kill()
