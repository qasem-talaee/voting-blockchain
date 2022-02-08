import hashlib
import json
import time
import requests

class BlockChain():
    
    def __init__(self, first_node):
        self.chain = []
        self.current_votes = []
        self.new_block(proof=100, previous_hash=1)
        self.nodes = set()
        self.nodes.add(first_node)
    
    def url_request(self, url):
        try:
            r = requests.get(url).json()
        except:
            return 0
        else:
            return r
    
    def update_nodes(self):
        len_node = len(self.nodes)
        for i in range(len_node):
            response = self.url_request('http://{node}/nodes'.format(node=list(self.nodes)[i]))
            if response != 0 and int(response['length']) > len_node:
                self.nodes = set()
                self.nodes = set(response['nodes'])
                len_node = len(self.nodes)
    
    def person_id_check_chain(self, person_id):
        chain_len = len(self.chain)
        for i in range(chain_len):
            for j in range(len(self.chain[i]['votes'])):
                if self.chain[i]['votes'][j]['person_id'] == person_id:
                    return False
        return True
    
    def update_current_votes(self):
        for node in self.nodes:
            response = self.url_request('http://{node}/current-votes'.format(node=node))
            if response != 0:
                for new_vote in response['current_votes']:
                    if new_vote not in self.current_votes:
                        self.current_votes.append(new_vote)
        for i in range(len(self.current_votes)):
            if not self.person_id_check_chain(self.current_votes[i]['person_id']):
                del self.current_votes[i]
    
    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True
    
    def resolve_conflicts(self):
        """
        This is our Consensus Algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.
        """
        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = self.url_request('http://{node}/chain'.format(node=node))

            if response != 0:
                length = response['length']
                chain = response['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
    
    def update_block(self):
        self.update_nodes()
        self.resolve_conflicts()
        self.update_current_votes()
      
    def new_vote(self, person_id, vote):
        self.update_block()
        if self.valid_person_id(person_id):
            self.current_votes.append({
                'person_id': hashlib.sha256(str(person_id).encode()).hexdigest(),
                'vote': vote,
            })
            return True
        else:
            return False
    
    def valid_person_id(self, person_id):
        id_hash = hashlib.sha256(str(person_id).encode()).hexdigest()
        current_vote_len = len(self.current_votes)
        for i in range(current_vote_len):
            if self.current_votes[i]['person_id'] == id_hash:
                return False
        chain_len = len(self.chain)
        for i in range(chain_len):
            for j in range(len(self.chain[i]['votes'])):
                if self.chain[i]['votes'][j]['person_id'] == id_hash:
                    return False
        return True
    
    def new_block(self, proof, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'votes': self.current_votes,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        self.current_votes = []
        self.chain.append(block)
        return block
    
    def hash(self, block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    
    def last_block(self):
        return self.chain[-1]
    
    def pow(self, last_proof):
        proof = 0
        while self.valid_proof(last_proof, proof) == False:
            proof += 1
        return proof
    
    def valid_proof(self, last_proof, proof):
        guess = '{last_proof}{proof}'.format(last_proof=last_proof, proof=proof).encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == '0000'