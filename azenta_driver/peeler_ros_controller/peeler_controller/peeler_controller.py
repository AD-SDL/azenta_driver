# ROS Library
from signal import sigpending
import rclpy
from rclpy.node import Node

# OS library !!!!! Must be below ROS msgs below ROS libraries 
import os
import os.path
from os import path

# Other
from threading import Thread, Lock
import time
from pathlib import Path
import importlib.util
from random import random

# ROS messages and services
from workcell_interfaces.srv import *
from workcell_interfaces.msg import *

# OT2_workcell_manager API
from ot2_workcell_manager_client.retry_api import *
from ot2_workcell_manager_client.register_api import *
from ot2_workcell_manager_client.register_api import _get_id_name
from ot2_workcell_manager_client.worker_info_api import *
from ot2_workcell_manager_client.worker_info_api import (
    _get_node_info,
    _get_node_list,
    get_node_info,
)

# peeler Library
from peeler_client.publish_peeler_state import *
from peeler_client.publish_peeler_state import _update_peeler_state
from peeler_client.publish_peeler_state import heartbeat_transmitter

# peeler driver
# import peeler_driver_pkg.peeler_driver
# from peeler_driver_pkg.peeler_driver import peeler_transfer


# TODO: figure out how to integrate peeler code
'''
    This is the peelerTransferHandler class. The purpose of this class is to execute tasks running on the Manager's queue and alert the system of state changes and program status. 

    It is undecided if this package is directly running on the peeler or if it will follow the same model as the OT2 
'''
class PeelerController(Node):
    def __init__(self, name):

        # Node creation
        super().__init__("peeler_transfer_handler_" + name)  # User specifies name
        self.name = name
        self.type = "peeler"

        # Lock creation

        # Readabilty
        self.state = {  # TODO maybe a sync with the master
            "BUSY": 1,
            "READY": 0,
            "ERROR": 2,
            "QUEUED": 3,
            "COMPLETED": 4
        }
        self.status = {
            "ERROR": 1,
            "SUCCESS": 0,
            "WARNING": 2,
            "FATAL": 3,
            "COMPLETED": 4,
            "WAITING": 10,
        }

        # State of the peeler
        self.current_state = self.state["READY"]
        self.state_lock = Lock()

        # Path setup
        path = Path()
        self.home_location = str(path.home())
        self.module_location = self.home_location + "/ot2_ws/src/ot2_workcell/OT2_Modules/"

        # Create clients

        # Get ID and confirm name from manager
        args = []
        args.append(self)
        status = retry(self, _get_id_name, 1000, 2, args)  # 1000 retries 2 second timeout
        if status == self.status["ERROR"]:
            self.get_logger().fatal("Unable to get id from peeler manager, exiting...")
            self.set_state(self.state["ERROR"]) # Set system state to ERROR

        # Create services

        # Sub to topics
        self.state_reset_sub = self.create_subscription(PeelerReset, "/peeler/peeler_state_reset",self.state_reset_callback, 10)
        self.state_reset_sub # prevent unused variable warning

        #  peeler State Syncronization topic 
        self.state_sync = self.create_subscription(PeelerStateUpdate, "/peeler/peeler_state_update", self.peeler_state_update_callback, 10)
        self.state_sync # prevent unused variable warning
        self.start_work_service = self.create_service(StartWorkPeeler, "/peeler/start_work_peeler", self.start_work_handler)
        # Initialization Complete
        
        self.get_logger().info(
            "peeler Transfer handler for ID: %s name: %s initialization completed"
            % (self.id, self.name)
        )

        # Kill thread 
        self.dead = False 
        
        # Create a thread to run heartbeat_transmitter
        heartbeat_thread = Thread(target=heartbeat_transmitter, args=(self,))
        heartbeat_thread.start()

    def start_work_handler(self, request, response): #TODO
        print("Do some job ......")
        # set state to busy
        # start peeling
        # Done peeling
        # set state to completed
        #return response # this response only has status

    '''
        Retrieves the next transfer to run in the queue
        No need to lock the peeler this is done by the manager
        
        We send a message to master that we are busy when we take a new job
    '''
    # def get_next_transfer(self): #?
    #     # Get the next transfer - Create client and wait for service
    #     get_next_transfer_cli = self.create_client(
    #         GetNextTransfer, "/peeler/%s/get_next_transfer" % self.id
    #     )
    #     while not get_next_transfer_cli.wait_for_service(timeout_sec=2.0):
    #         if(self.dead == True): # Force thread to kill
    #              return self.status['FATAL']
    #         self.get_logger().info("Service not available, trying again...")

    #     # Create request
    #     request = GetNextTransfer.Request()

    #     # Call the cli
    #     next_transfer = ""
    #     future = get_next_transfer_cli.call_async(request)
    #     while future.done() == False:
    #         if(self.dead == True): # Force thread to kill
    #             return self.status['FATAL']
    #         time.sleep(1)  # 1 second timeout
    #     if future.done():
    #         try:
    #             response = future.result()

    #             if (response.status == response.ERROR or response.status == response.FATAL):
    #                 raise Exception("Next transfer request failed")
    #             elif response.status == response.WAITING: 
    #                 return self.status["WAITING"]
    #         except Exception as e:
    #             self.get_logger().error("Error occured %r" % (e,))
    #             return self.status["ERROR"]
    #         else:
    #             next_transfer = (
    #                 response.next_transfer.splitlines()
    #             )  # Breaks up based on newlines

    #     # Get transfer data - Retrieve from and to from the first identifier
    #     transfer_request = next_transfer[0].split()  # Split based on whitespaces
    #     from_name = transfer_request[0]
    #     to_name = transfer_request[1]
    #     job = "transfer" # Not implemented as of right now TODO

    #     # Get node information
    #     to_entry = get_node_info(self, to_name)
    #     from_entry = get_node_info(self, from_name)

    #     # Error checking
    #     if to_entry["type"] == "-1":  # Doesn't exist
    #         self.get_logger().error("node: %s doesn't exist with master" % to_name)
    #         return self.status["ERROR"]
    #     if from_entry["type"] == "-1":  # Doesn't exist
    #         self.get_logger().error("node: %s doesn't exist with master" % from_name)
    #         return self.status["ERROR"]

    #     # Update state and let it be know that we are busy
    #     self.set_state(self.state["BUSY"]) # Set system state to BUSY 

    #     # Do the transfer
    #     try:
    #         self.get_logger().info(
    #             "Attempting to transfer complete transfer %s" % str(next_transfer)
    #         )
    #         output_msg = peeler_transfer(job, from_name, to_name) # Do an peeler transfer TODO: error handling
    #         self.get_logger().info("Transfer %s is complete" % str(next_transfer))
    #     except Exception as e:
    #         '''
    #          At this point it is safe to exit
    #          The reason why is because we still only have one entry in the transfer_queue, and no entry
    #          In the completed queue, which means the system is still in the same state it started in
    #         '''
    #         self.get_logger().error("Error occured: %r" % (e,))
    #         return self.status["ERROR"] # Alert to error, thread will alert system to ERROR
    #     else:
    #         self.set_state(self.state["READY"]) # System is READY again 

    #     # Add to completed queue - Create pub
    #     completed_transfer_pub = self.create_publisher(
    #         CompletedTransfer, "/peeler/%s/completed_transfer" % self.id, 10
    #     )
    #     time.sleep(1)  # Wait for it

    #     # Create msg - Using identifiers
    #     msg = CompletedTransfer()
    #     msg.identifier_cur = next_transfer[0]
    #     msg.identifier_other = next_transfer[1]

    #     # Publish
    #     completed_transfer_pub.publish(msg)

    #     return self.status["SUCCESS"]

    # Helper function
    def set_state(self, new_state):
        args = []
        args.append(self)
        args.append(new_state)
        status = retry(self, _update_peeler_state, 1, 0, args) # if it fails it usually isn't something that will be fixed upon a retry
        if status == self.status["ERROR"] or status == self.status["FATAL"]:
            self.get_logger().error(
                "Unable to update state with manager, continuing but the state of the peeler may be incorrect"
            )

    # Service to update the state of a node
    def peeler_state_update_callback(self, msg):
        # Check if it was for this id 
        if(msg.id != self.id):
            return 

        # Prevent changing state when in an error state
        if(self.current_state == self.state['ERROR']):
            self.get_logger().error("Can't change state, the state of peeler %s is already error"%msg.id)
            return # exit out of function

        # set state
        self.state_lock.acquire()
        self.current_state = msg.state
        self.state_lock.release()

   # Function to reset the state of the transfer handler
    def state_reset_callback(self, msg):
        # Check for ID
        if(self.id != msg.id):
            return

        self.get_logger().warning("Resetting state of id: %s..."%msg.id)

        # set state
        self.state_lock.acquire()
        self.current_state = msg.state
        self.state_lock.release()

    # Function to constantly poll manager queue for transfers
    '''
        Upon error to this thread, the get_next_transfer infinite loop will terminate with the respective nodes being alerted of an error occuring. However, all services of the node 
        and subscribers will remain operational, but the only way to restart the peeler would require restarting the entire node, it might be beneficial to add restart capabilties. 

        TODO: It might make sense to have it poll at a higher or lower frequency this is up to testing, or change this to something configurable by the launch file
    '''
    def run(self): #?
        # Runs every 3 seconds
        while rclpy.ok():
            time.sleep(3)
            try: 
                status = self.get_next_transfer()

                if(status == self.status['ERROR']):
                    raise Exception("Unexpected Error occured in peelerTransferHandler get_next_transfer operation")
            except Exception as e: 
                self.get_logger().error("Error occured: %r" % (e,))
                self.set_state(self.state['ERROR']) # Alert system that state is error 
                return; # exit out 
            except: # Catch other errors 
                self.set_state(self.state['ERROR']) # Alert system that state is error 
                return; # exit out 
            else: 
                if(status == self.status['FATAL']):
                    return; # Exit out we are terminating 

def main(args=None):
    rclpy.init(args=args)

    peeler_transfer_node = peelerTransferHandler("Temp")
    try:
        spin_thread = Thread(target=peeler_transfer_node.run, args=())
        spin_thread.start()

        rclpy.spin(peeler_transfer_node)
    except Exception as e:
        peeler_transfer_node.get_logger().error("Error %r" % (e,))
    except:
        peeler_transfer_node.get_logger().fatal("Terminating...")

    # End
    peeler_transfer_node.dead = True # Force kill
    spin_thread.join()
    peeler_transfer_node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
