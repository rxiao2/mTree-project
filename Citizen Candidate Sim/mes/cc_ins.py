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

    Messages Received: 
    - init_institution, from Environment, payload = {'standing_bid': standing_bid, 
                                                    'standing_ask': standing_ask,}
    - start_bargaining, from Environment, payload = agent_addresses
    - end_bargaining, from Environment, payload = None
    - request_standing from agent, payload = None
    - bid, from Buyer Agent, payload = (bid, buyer_short_name)
    - ask, from Seller Agent, payload = (ask, seller_short_name)

    Messages Sent:
    - institution_confirm_init, to Environment, payload = None
    - contract, to Environment, payload = {'price': price, 
                                           'buyer_id': buyer_short_name,       
                                           'seller_id': seller_short_name,}
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
        self.votes_count = 0
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
        Messages Handled :
        - init_institution
            sender: Environment 
            payload: dict = {'starting_bid': int, 'starting_ask': int}

        Messages Sent: 
        - institution_confirm_init
            receiver: Environment, 
            payload:  None
        """
        self.log_message(f'Institution initializing ...')
        self.environment_address = message.get_sender() #saves the environment address 
        self.bliss_point_set = message.get_payload()['bliss_point']
        self.number_of_agents = len(self.bliss_point_set)

    @directive_decorator("start_election")
    def start_election(self, message: Message):
        """
        Messages Handled :
        - start_period
            sender: Environment 
            payload:    Agent addresses 

        Messages Sent: 
         - start_round
            receiver: Agents 
            payload:   Institution address 
        """
        self.log_message(f'The election begins')
        for i in range(self.number_of_agents):
            self.send_message("identity_decision", f'cc_agent.CcAgent {i+1}', None) 


    @directive_decorator("candidate_collection")
    def candidate_collection(self, message: Message):
        """
        Sends the standing bid or ask to agents.

        Messages Handled :
        - request_standing
            sender: Agent 
            payload:    None 

        Messages Sent: 
         - standing
            sender: Institution 
            payload: (self.standing_bid, self.standing_ask) 
        """

        self.counter +=1
        self.candidate_address.append(message.get_sender()) 
        
        agent_id = message.get_payload()
        self.candidate_set[f'{agent_id}']=self.bliss_point_set[agent_id-1]
        self.log_message(f"Citizen {agent_id} chooses to be a candidate.")

        if self.num_of_citizen == self.counter:
            self.counter = 0
            self.send_candidate_inf(self, self.candidate_set)
            self.log_message(f"all agents finish identity selection")

    @directive_decorator("voter_collection")
    def voter_collection(self, message: Message):
        """
        Sends the standing bid or ask to agents. 
        """
        
        self.counter +=1
        self.voter_address.append(message.get_sender())

        agent_id = message.get_payload()
        self.log_message(f"Citizen {agent_id} chooses to be a voter.")

        if self.num_of_citizen == self.counter:
            self.counter = 0
            self.send_candidate_inf(self, self.candidate_set)
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
           
            self.candidate_votes = self.candidate_set
            for candidate in self.candidate_votes.keys():
                self.candidate_votes[candidate] = 0

    @directive_decorator("ballot")
    def ballot(self, message: Message):            
        '''
        Calculate votes and determines elected candidates.
        '''
        self.shutdown_mes()
        vote = message.get_payload()
        for candidate in self.candidate_votes.keys():
            if candidate == vote:
               self.candidate_votes[candidate] += 1
               self.votes_count += 1
        if self.votes_count == len(self.voter_address):
            self.electeds = [keys for keys,values in self.candidate_votes.items() if values == max(self.candidate_votes.values())]
            president = random.choice(self.electeds)
            payload = [president, self.candidate_set[president]]
            for agent in self.address_book.get_addresses():
                self.send_message("payoff", agent, payload, False) 
    
    @directive_decorator("end_election")
    def end_election(self, message: Message): 
        self.counter += 1
        if self.counter == self.num_of_citizen:
            self.shutdown_mes()

