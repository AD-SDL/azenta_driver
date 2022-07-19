# ROS libraries 
import rclpy
from rclpy.node import Node

# Time Library 
import time

# ROS Messages and Services
from peeler_utils.srv import *
from peeler_utils.msg import *

# OT2_workcell_manager API
from ot2_workcell_manager_client.worker_info_api import *
from ot2_workcell_manager_client.worker_info_api import (
    _get_node_info,
    _get_node_list,
    get_node_info,
)

# Scheduler client
from scheduler_client.block_to_robot_conversion import *
from scheduler_client.block_to_robot_conversion import convert_block_name
'''
 This is an API that will begin a transfer request from_node to_node on the designated peeler_name_or_id. 

 Note: item is currently unused as we don't have anything programmed for it yet so it is just ignored
'''
def add_work_to_peeler(self):  #TODO: do something with item
    
# TODO: Start the work if it is in Queued state 
    # get_node_info(self, "P")

    # Select a node
    # id = -1 # Init 
    try:
        if get_node_info(self, "P")["state"] != self.state["QUEUED"]:
            self.logger.warning("Can't start the peeling job. Peeler is not in QUEUED state!")
            return
        

      
    #     # Get node information
    #     #target_node = self.search_for_node(id)  # See if id robot exists
    #     target_node = peeler_name_or_id

    #     # Error checking
    #     if target_node["type"] == "-1":  # No such node
    #         self.get_logger().error("id: %s doesn't exist" % id)
    #         return self.status["ERROR"]

    #     node_type = target_node["type"]  # These will be needed to access the service
    #     id = target_node["id"]


    except Exception as e:
        self.get_logger().error("Error occured: %r" % (e,))
        return self.status["ERROR"]

    # create client that calls file handler service on OT-2 module

    # Client setup
    send_cli = self.create_client(
        StartWorkPeeler, "/%s/%s/add_work_peeler" % (node_type, id)
    )  # format of service is /{node_type}/{id}/{service name}
    while not send_cli.wait_for_service(timeout_sec=2.0):
        self.get_logger().info("Service not available, trying again...")

    # Client ready
    # TODO: replacement parameter?
    
    # Create a request
    send_request = StartWorkPeeler.Request()

    # Call Service to load module
    future = send_cli.call_async(send_request)

    # Waiting on future
    while future.done() == False:
        time.sleep(1)  # timeout 1 second

    if future.done():
        try:
            response = future.result()

            # Error handling - TODO: if an error occured we want to deal with that separately 
            if (
                response.status == response.ERROR
                or response.status == response.FATAL
            ):  # Some error occured
                raise Exception
        except Exception as e:
            self.get_logger().error("Error occured %r" % (e,)) #TODO: Maybe handle this as error and not as waiting
            status = self.status["WAITING"]   # Retry
        else:
        
            self.get_logger().info(
                "Peeler was successful to peel the plate %s"
                % (peeler_name_or_id['name'])
            )
            status = self.status["SUCCESS"]
       



# Middleman function to segway to peeling call in retry function
def _load_peeling(peeler_name_or_id, block_name):
    return add_work_to_peeler(peeler_name_or_id, block_name)  # self, from_name_or_id, to_name_or_id, item, peeler_id


# dud main function
def main_null():
    print("This is not meant to have a main")
