import hashlib
import json
import os
import time

from flask import Flask, request
import requests

class Block:
    def __init__(self, index=0, transactions=[], timestamp=time.time(), previous_hash=0, nonce=0):
        """
        A function that initialize block.
        """
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce

    def compute_hash(self):
        """
        A function that return the hash of the block contents.
        """
        hasher = hashlib.sha256()
        hasher.update(str.encode(json.dumps({
            "index": self.index,
            "transactions": self.transactions,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
        })))
        return hasher.hexdigest()


class Blockchain:
    # difficulty of our PoW algorithm
    difficulty = 2

    def __init__(self, use_file=False):
        """
        A function that initialize blockchian.
        """
        self.unconfirmed_transactions = []
        self.chain = []
        if use_file and os.path.exists('chain.json'):
            # import chain from before
            chain_file = open('chain.json', 'r')
            print("Processing blockchain from disk...")
            decoded_file = json.loads(chain_file.read())
            disk_chain = decoded_file['chain']
            # Reconstruct our blockchain
            for block in disk_chain:
                self.chain.append(Block(
                    index=block['index'],
                    transactions=block['transactions'],
                    timestamp=block['timestamp'],
                    previous_hash=block['previous_hash'],
                    nonce=block['nonce']))
            # TODO: validate chain file
            # TODO: construct a tx map for all fish
            print("Processing complete!")
        if not os.path.exists('chain.json'):
            print("WARNING: chain.json does not exist. Mine a block to generate file.")

    def create_genesis_block(self):
        """
        A function to generate genesis block and appends it to
        the chain. The block has index 0, previous_hash as 0, and
        a valid hash.
        """
        genesis_block = Block()
        self.proof_of_work(genesis_block)
        self.chain.append(genesis_block)
        return genesis_block

    @property
    def last_block(self):
        return self.chain[-1]

    def add_block(self, block, proof):
        """
        A function that adds the block to the chain after verification.
        Verification includes:
        * Checking if the proof is valid.
        * The previous_hash referred in the block and the hash of latest block
          in the chain match.
        """
        if self.is_valid_proof(block, proof):
            self.chain.append(block)

    @staticmethod
    def proof_of_work(block):
        """
        Function that tries different values of nonce to get a hash
        that satisfies our difficulty criteria.
        """
        nonce = 0
        difficulty_zeros = '0' * Blockchain.difficulty
        while True:
            block.nonce = nonce
            block_hash = block.compute_hash()
            if block_hash.startswith(difficulty_zeros):
                break
            # Is this the best way to do it? Increment the nonce by one?
            # There may be better ways to reduce the search space by
            # incrementing some N or using a random integer.
            nonce += 1
        return block.compute_hash()

    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)

    @classmethod
    def is_valid_proof(cls, block, block_hash):
        """
        Check if block_hash is valid hash of block and satisfies
        the difficulty criteria.
        """
        return (block_hash.startswith('0' * Blockchain.difficulty) and
                block_hash == block.compute_hash())

    @classmethod
    def check_chain_validity(cls, chain):
        for block in chain:
            block_hash = block.compute_hash()
            if not cls.is_valid_proof(block, block_hash):
                raise Error("The chain is bad")
        return True

    def mine(self):
        """
        This function serves as an interface to add the pending
        transactions to the blockchain by adding them to the block
        and figuring out Proof Of Work.
        """
        if len(self.unconfirmed_transactions) == 0:
            return None
        previous_block = self.last_block
        previous_hash = previous_block.compute_hash()
        next_block = Block(
            index=len(self.chain),
            previous_hash=previous_hash,
            transactions=self.unconfirmed_transactions,
        )
        proof = Blockchain.proof_of_work(next_block)
        self.add_block(next_block, proof)
        self.export_chain()
        self.unconfirmed_transactions = [] # Reset
        return next_block

    def export_chain(self):
        chain_file = open('chain.json', 'w')
        chain_file.write(self.dump())
        chain_file.close()

    def dump(self):
        chain_data = []
        for block in blockchain.chain:
            chain_data.append(block.__dict__)
        return json.dumps({"length": len(chain_data),
                            "chain": chain_data,
                            "peers": list(peers)})


app = Flask(__name__)

# the node's copy of blockchain
blockchain = Blockchain(use_file=True)
blockchain.create_genesis_block()

# the address to other participating members of the network
peers = set()


# endpoint to submit a new transaction. This will be used by
# our application to add new data (posts) to the blockchain
@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    tx_data = request.get_json()
    required_fields = ["guid", "speciesId", "caughtLat", "caughtLong", "consumption"]
    # TODO: Additional verification based on fishnet rules

    print("Adding txn for fish " + tx_data.get('guid'))

    for field in required_fields:
        if not tx_data.get(field):
            return "Invalid transaction data", 404

    tx_data["timestamp"] = time.time()

    blockchain.add_new_transaction(tx_data)

    return "Success", 201


# endpoint to return the node's copy of the chain.
# Our application will be using this endpoint to query
# all the posts to display.
@app.route('/chain', methods=['GET'])
def get_chain():
    return blockchain.dump()


# endpoint to request the node to mine the unconfirmed
# transactions (if any). We'll be using it to initiate
# a command to mine from our application itself.
@app.route('/mine', methods=['GET'])
def mine_unconfirmed_transactions():
    result = blockchain.mine()
    if not result:
        return "No transactions to mine"
    else:
        # Making sure we have the longest chain before announcing to the network
        chain_length = len(blockchain.chain)
        consensus()
        if chain_length == len(blockchain.chain):
            # announce the recently mined block to the network
            announce_new_block(blockchain.last_block)
        return "Block #{} is mined.".format(blockchain.last_block.index)


# endpoint to add new peers to the network.
@app.route('/register_node', methods=['POST'])
def register_new_peers():
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    # Add the node to the peer list
    peers.add(node_address)

    # Return the consensus blockchain to the newly registered node
    # so that he can sync
    return get_chain()


@app.route('/register_with', methods=['POST'])
def register_with_existing_node():
    """
    Internally calls the `register_node` endpoint to
    register current node with the node specified in the
    request, and sync the blockchain as well as peer data.
    """
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    data = {"node_address": request.host_url}
    headers = {'Content-Type': "application/json"}

    # Make a request to register with remote node and obtain information
    response = requests.post(node_address + "/register_node",
                             data=json.dumps(data), headers=headers)

    if response.status_code == 200:
        global blockchain
        global peers
        # update chain and the peers
        chain_dump = response.json()['chain']
        blockchain = create_chain_from_dump(chain_dump)
        peers.update(response.json()['peers'])
        return "Registration successful", 200
    else:
        # if something goes wrong, pass it on to the API response
        return response.content, response.status_code


def create_chain_from_dump(chain_dump):
    generated_blockchain = Blockchain()
    generated_blockchain.create_genesis_block()
    for idx, block_data in enumerate(chain_dump):
        if idx == 0:
            continue  # skip genesis block
        block = Block(block_data["index"],
                      block_data["transactions"],
                      block_data["timestamp"],
                      block_data["previous_hash"],
                      block_data["nonce"])
        proof = block_data['hash']
        added = generated_blockchain.add_block(block, proof)
        if not added:
            raise Exception("The chain dump is tampered!!")
    return generated_blockchain


# endpoint to add a block mined by someone else to
# the node's chain. The block is first verified by the node
# and then added to the chain.
@app.route('/add_block', methods=['POST'])
def verify_and_add_block():
    block_data = request.get_json()
    block = Block(block_data["index"],
                  block_data["transactions"],
                  block_data["timestamp"],
                  block_data["previous_hash"],
                  block_data["nonce"])

    proof = block_data['hash']
    added = blockchain.add_block(block, proof)

    if not added:
        return "The block was discarded by the node", 400

    return "Block added to the chain", 201


# endpoint to query unconfirmed transactions
@app.route('/pending_tx')
def get_pending_tx():
    return json.dumps(blockchain.unconfirmed_transactions)


def consensus():
    """
    Our naive consnsus algorithm. If a longer valid chain is
    found, our chain is replaced with it.
    """
    global blockchain

    longest_chain = None
    current_len = len(blockchain.chain)

    for node in peers:
        response = requests.get('{}chain'.format(node))
        length = response.json()['length']
        chain = response.json()['chain']
        if length > current_len and blockchain.check_chain_validity(chain):
            current_len = length
            longest_chain = chain

    if longest_chain:
        blockchain = longest_chain
        return True

    return False


def announce_new_block(block):
    """
    A function to announce to the network once a block has been mined.
    Other blocks can simply verify the proof of work and add it to their
    respective chains.
    """
    for peer in peers:
        url = "{}add_block".format(peer)
        headers = {'Content-Type': "application/json"}
        requests.post(url,
                      data=json.dumps(block.__dict__, sort_keys=True),
                      headers=headers)

# Uncomment this line if you want to specify the port number in the code
#app.run(debug=True, port=8000)
