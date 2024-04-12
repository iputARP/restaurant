#! /usr/bin/env python3

import rospy
from marti_common_msgs.msg import StringArrayStamped
from gpsr.srv import ObjectCount, ObjectCountResponse, ObjectCountRequest

class ObjectCounter:
    def __init__(self):
        self.subscriber = None
        self.category = {"food":    ["potted_meat_can", "mustard_bottle", "banana", "orange", "master_chef_can",
                                     "peach", "apple", "tuna_fish_can", "pear", "sugar_box", "plum", "cracker_box",
                                     "lemon", "gelatin_box", "tomato_soup_can", "strawberry", "pringles"],

                         "kitchen": ["windex_bottle", "bleach_cleanser", "sponge", "pitcher_base", "skillet_lid",
                                     "plate", "bowl", "fork", "spatula", "mug"],

                         "tool":    ["large_marker", "large_clamp", "clamp, material, mesh", "extra_large_clamp"],

                         "shape":   ["mini_soccer_ball", "softball", "baseball", "tennis_ball", "racquetball",
                                     "golf_ball", "b_marbles", "a_cups", "b_cups", "d_cups", "f_cups", "i_cups",
                                     "j_cups", "foam_brick", "dice", "chain"],

                         "task":    ["rubiks_cube", "a_colored_wood_blocks", "nine_hole_peg_test", "a_toy_airplane",
                                     "b_toy_airplane", "c_toy_airplane", "d_toy_airplane", "e_toy_airplane",
                                     "b_lego_duplo", "c_lego_duplo", "d_lego_duplo", "e_lego_duplo", "f_lego_duplo",
                                     "g_lego_duplo"],

                         "discard": ["skillet", "skillet_lid", "hammer", "adjustable_wrench", "power_drill", "knife",
                                     "padlock", "phillips_screwdriver", "flat_screwdriver"],
                         }
        self.all_items = []
        for sublist in self.category.values():
            for item in sublist:
                self.all_items.append(item)

        self.all_items_count = {item: 0 for item in self.all_items}
        self.all_items_count["others"] = 0

        self.callback_counter = 0

    def register_service(self):
        rospy.loginfo("register service")
        rospy.Service("object_counter_server", ObjectCount, self.exec)

    def callback(self,msg):
        self.msg = msg
        self.detected_object_list = msg.strings

        for item in self.detected_object_list:
            if item in self.all_items:
                self.all_items_count[item] += 1
            else:
                self.all_items_count["others"] += 1

        self.callback_counter += 1

        rospy.loginfo(f"detected_object_list: {self.detected_object_list}")


    def exec(self,req):
        self.all_items_count = {item: 0 for item in self.all_items}
        self.all_items_count["others"] = 0
        self.callback_counter = 0

        self.subscriber = rospy.Subscriber("hsrb_visions/object_list", StringArrayStamped, self.callback)
        rospy.sleep(5)
        self.subscriber.unregister()

        if self.callback_counter == 0:
            return ObjectCountResponse(0)
        else:
            threshold = rospy.get_param("gpsr/detected_object_threshold", 0.8)
            if threshold < 0:
                threshold = 0.0
            elif 1.0 < threshold:
                threshold = 1.0
            else:
                threshold = threshold

            # threshold以上認識されれば確定
            count = 0
            check_key = []
            request_category = self.category[req.category]
            for key, value in self.all_items_count.items():
                count_rate = value / self.callback_counter
                rate_calc = count_rate
                while (key in request_category) and (rate_calc > threshold):
                    check_key.append(key)
                    count += 1
                    rate_calc -= 1

            rospy.loginfo(f"request_category: {request_category}")
            rospy.loginfo(f"all_items_count: {self.all_items_count}")
            rospy.loginfo(f"callback_counter: {self.callback_counter}")
            rospy.loginfo(f"detected_object_threshold: {threshold}")
            rospy.loginfo(f"check_key: {check_key}")
            rospy.loginfo(f"detected_object_count: {count}")
            return ObjectCountResponse(count)


if __name__=="__main__":
    rospy.init_node("object_counter_server",anonymous=True)
    object_count = ObjectCounter()
    object_count.register_service()

    rospy.spin()
