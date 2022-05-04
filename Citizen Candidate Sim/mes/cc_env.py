
from mTree.microeconomic_system.environment import Environment
from mTree.microeconomic_system.institution import Institution
from mTree.microeconomic_system.agent import Agent
from mTree.microeconomic_system.directive_decorators import *
from mTree.microeconomic_system.message import Message #Message class allows you to create and send messages

import logging #Allows you to log messages to log files
import math
import random
import time
import datetime
import sympy

@directive_enabled_class
class CcEnvironment(Environment):
    """
    """

    def __init__(self):
        self.state = {}
        self.agents_ready = 0
        self.number_of_agents = None
        self.bliss_point_set = None
        self.institution_address = None
        self.agent_payload = None

    def send_message(self, directive, receiver, payload):
        """
        Sends message
        """

        new_message = Message()
        new_message.set_sender(self.myAddress)
        new_message.set_directive(directive)
        new_message.set_payload(payload)
        receiver_address = self.address_book.select_addresses(
            {"short_name": receiver})
        self.send(receiver_address, new_message)

    @directive_decorator("start_environment")
    def start_environment(self, message: Message):
        """
        This method starts the environment (automatically through mTree_runner)
        """

        self.state['endowment'] = self.get_property("endowment")
        self.state['rent'] = self.get_property("rent")
        self.state['cost'] = self.get_property("cost")
        self.state['bliss_point'] = self.get_property("bliss_point")
        self.state['multiplier'] = self.get_property("multiplier")
        self.number_of_agents = len(self.state['bliss_point'])
        self.bliss_point_set = self.state['bliss_point']
        self.log_message(f'The number of agents is {self.number_of_agents}; bliss point set is {self.bliss_point_set}')

        institutional_payload = {'bliss_point':self.state['bliss_point']}
        self.send_message("init_institution", "cc_ins.CcInstitution 1", institutional_payload)

        for i in range(self.number_of_agents): # self.shutdown_mes() #Used for testing
            agent_payload = {"id": i+1,
                "bliss_point": self.state['bliss_point'][i],
                'rent':self.state['rent'],
                'cost':self.state['cost'],
                'multiplier':self.state['multiplier'],
                'endowment':self.state['endowment']}
            self.send_message("init_agent", f"cc_agent.CcAgent {i+1}",
                                 agent_payload)
            self.log_message(f"Citizen {agent_payload['id']} is endowed with bliss point {self.bliss_point_set[i]}")


    @directive_decorator("confirm_init")
    def confirm_init(self, message: Message):
        """
        Receives confirmation from the agents and the institutions that they are finished initializing. 
        """
        
        self.agents_ready += 1
        if self.agents_ready == (self.number_of_agents + 1):
            self.agents_ready = 0
            self.log_message(f"All agents and institution are ready!")
            self.send_message("start_election", "cc_ins.CcInstitution 1", None)

