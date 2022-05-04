from mTree.microeconomic_system.environment import Environment
from mTree.microeconomic_system.institution import Institution
from mTree.microeconomic_system.agent import Agent
from mTree.microeconomic_system.directive_decorators import *
from mTree.microeconomic_system.message import Message

import math
import random
import logging
import time
import datetime

@directive_enabled_class
class CcInstitution(Institution):
    """
    Institution runs an election.  It requests citizen to choose their identity; 
    then it asks voters to vote for one candidate; finally, a candidate is elected.
    """
    
    def __init__(self):
        self.environment_address = None
        self.agent_id = None
        self.voter = []
        self.candidate_address = []
        self.voter_address = []
        self.candidate_set = {}
        self.candidate_votes = None
        self.citizen = None
        self.counter = 0
        self.number_of_agents = 0
        self.bliss_point_set = None
        self.votes_benchmark = 0
        self.electeds = None

    def send_message(self, directive, receiver, payload, use_env = False):
        """Sends message
           use_env = True has method use environment address """
        new_message = Message()
        new_message.set_sender(self.myAddress)
        new_message.set_directive(directive)
        new_message.set_payload(payload)
        if use_env:
            receiver = "Environment"
            receiver_address = self.environment_address
        else:
            receiver_address = self.address_book.select_addresses(
                               {"short_name": receiver})
        self.send(receiver_address, new_message)


    @directive_decorator("init_institution")
    def init_institution(self, message: Message):
        """
        Initiate institution
        """
        self.log_message(f'Institution initializing ...')
        self.environment_address = message.get_sender() # Save the environment address 
        self.bliss_point_set = message.get_payload()['bliss_point'] 
        self.number_of_agents = len(self.bliss_point_set)
        self.send_message("confirm_init","Environment", None, True)

    @directive_decorator("start_election")
    def start_election(self, message: Message):
        """
        Sends requests of identity decision to each agent. 
        """

        self.log_message(f'The election begins')
        for i in range(self.number_of_agents):
            receiver = f'cc_agent.CcAgent {i+1}'
            print(receiver)
            self.send_message("identity_decision", receiver, None) 


    @directive_decorator("candidate_collection")
    def candidate_collection(self, message: Message):
        """
        Collect candidate information
        """

        self.counter +=1
        self.candidate_address.append(message.get_sender()) # Document the addresses of candidates
        
        agent_id = message.get_payload()
        self.candidate_set[f'{agent_id}']=self.bliss_point_set[agent_id-1] # Document each candidate's id and bliss point
        self.log_message(f"Citizen {agent_id} chooses to be a candidate.") # Report decisions

        if self.number_of_agents == self.counter: # Confirm that all agents finished identity decision
            self.counter = 0
            self.send_candidate_inf(self, self.candidate_set) # Prepare to send candidate information to voters
            self.log_message(f"all agents finish identity selection")

    @directive_decorator("voter_collection")
    def voter_collection(self, message: Message):
        """
        Collect voter information
        """
        
        self.counter +=1
        self.voter_address.append(message.get_sender()) # Document the addresses of voters

        agent_id = message.get_payload()
        self.log_message(f"Citizen {agent_id} chooses to be a voter.") # Report decisions 

        if self.number_of_agents == self.counter: # Confirm that all agents finished identity decision
            self.counter = 0
            self.send_candidate_inf(self, self.candidate_set) # Prepare to send candidate information to voters
            self.log_message(f"all agents finish identity selection")


    @directive_decorator("send_candidate_inf")        
    def send_candidate_inf(self, candidates, message: Message):
        '''
        Send the list of candidates to voters and ask them 
        to choose one candidate to vote.
        If no voters or no candidates, the game ends.
        '''

        if self.voter_address == []:
            self.shutdown_mes()
        elif self.candidate_address == []:
            self.shutdown_mes()
        else:
            for voter in self.voter_address:
                self.send_message("vote", voter, candidates, False)
            self.log_message(f"Candidate information has been sent to voters.")         
            self.candidate_votes = self.candidate_set # Make another dictionary, similar to candidate_set, for collecting votes.
            for candidate in self.candidate_votes.keys():
                self.candidate_votes[candidate] = 0

    @directive_decorator("ballot")
    def ballot(self, message: Message):            
        '''
        Collect votes and determines elected president.
        '''

        vote = message.get_payload()
        for candidate in self.candidate_votes.keys():
            if candidate == vote:
               self.candidate_votes[candidate] += 1
               self.counter += 1
        if self.counter == len(self.voter_address):
            self.counter == 0
            self.electeds = [keys for keys,values in self.candidate_votes.items() if values == max(self.candidate_votes.values())] # This is a list including all keys with the highest value in a dictionary.
            president = random.choice(self.electeds)
            payload = [president, self.candidate_set[president]]
            for agent in self.address_book.get_addresses(): # Send the elected president/policy to all citizen
                self.send_message("payoff", agent, payload, False) 
    
    @directive_decorator("end_election")
    def end_election(self, message: Message): 
        """
        Shut down the system once all citizen get their payoffs.
        """

        self.counter += 1
        if self.counter == self.number_of_agents:
            self.shutdown_mes()

