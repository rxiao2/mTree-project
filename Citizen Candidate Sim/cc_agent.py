from tkinter import Y
from tkinter.filedialog import askdirectory
from mTree.microeconomic_system.environment import Environment
from mTree.microeconomic_system.institution import Institution
from mTree.microeconomic_system.agent import Agent
from mTree.microeconomic_system.directive_decorators import *
from mTree.microeconomic_system.message import Message

import importlib
import math
import random
import logging
import time
import datetime

#TODO: make a directive to accept request_standing reminder message
@directive_enabled_class
class CcAgent(Agent):
    """
    """ 
    def __init__(self):
        self.my_id = None      
        self.role = None  
        self.bliss_point = None
        self.cost = None
        self.rent = None
        self.multiplier = None
        self.institution_address = None
        self.environment_address = None
        self.benchmark = -10000 
        self.favoriate_candidate = []
        self.my_payoff = None


    def send_message(self, directive, receiver, payload, use_env = False):
        """
        Sends message
        use_env = True has method use environment address 
        """

        new_message = Message()
        new_message.set_sender(self.myAddress)
        new_message.set_directive(directive)
        new_message.set_payload(payload)
        if use_env:
            receiver = "Environment"
            receiver_address = self.environment_address
        else:
            receiver_address = self.institution_address
        self.send(receiver_address, new_message)


    @directive_decorator("init_agent")
    def init_agent(self, message: Message):
        """
        Recieve and store the class variables for the agents and 
        sends back a confirmation to the environment. 
        """

        self.environment_address = message.get_sender() # Save personal information/parameters
        payload = message.get_payload()
        self.my_id = payload['id']
        self.multiplier = payload['multiplier']
        self.cost = payload['cost']
        self.rent = payload['rent']
        self.bliss_point = payload['bliss_point']
        self.endowment = payload['endowment']
        
        self.log_message(f'Citizen {self.my_id} is ready with bliss point {self.bliss_point}')
        self.send_message("confirm_init", "Environment", None, True)


    @directive_decorator("identity_decision")
    def identity_decision(self, message: Message):
        """
        Agents choose their identity, either candidate or voter. 

        """
        self.institution_address = message.get_sender()

        if abs(self.bliss_point - 7) < 3:
            self.role = "candidate" 
            self.send_message("candidate_collection", "Institution", self.my_id)
        else:
            self.role = "voter"
            self.send_message("voter_collection", "Institution", self.my_id)


    @directive_decorator("vote")
    def vote(self, message: Message):
        """
        Vote for one candidate based on candidates' bliss points.
        """

        payload = message.get_payload()
        for candidate, policy in payload:
            utility = -abs(policy - self.bliss_point)
            if utility > self.benchmark:
                self.benchmark = utility
                self.favoriate_candidate = []
                self.favoriate_candidate.append(candidate)
            elif utility == self.benchmark:
                self.favoriate_candidate.append(candidate)
            else:
                pass

        self.my_vote = random.choice(self.favoriate_candidate)
        self.log_message(f'{self.my_id} prefers {self.favoriate_candidate}, and chooses {self.my_vote}')
        self.send_message("ballot", "Institution", self.my_vote)


    @directive_decorator("payoff")
    def payoff(self, message: Message):
        """
        Calculating payoff upon receiving the implemented policy.
        """

        payload = message.get_payload()
        if self.role == "candidate":       
            if payload[0] == (f'{self.my_id}'):         
                self.my_payoff = self.endowment + self.rent - self.cost  
                self.log_message(f"{self.my_id} is the president elected, earning {self.payoff}")
            else:
                self.my_payoff = self.endowment - self.cost - self.multiplier * abs(self.bliss_point-payload[1])
                self.log_message(f"{self.my_id} is a candidate, earning {self.payoff}")
        else:
            self.my_payoff = self.endowment - self.multiplier * abs(self.bliss_point-payload[1])
            self.log_message(f"{self.my_id} is a voter, earning {self.payoff}")
        self.send_message("end_election", "Institution", None)
