import datetime
import hashlib
import json
from urllib.parse import urlparse
from uuid import uuid4

import requests
from flask import Flask, jsonify, request

'''
    Module 1
    B1: khởi tạo chuỗi blockchain
    B2: Tạo function tạo mới một khối block
    B3: Tạo function hash một khối block 
    B4: Tạo function bằng chứng công việc proof
    B5: Tạo function check khối chuỗi blockchain   
'''
'''
    Module 2: connect, lấy danh sách network, lấy blockchain, replace chain 
    b1: Tạo function add_transactions
'''


# Build a block chain

class Blockchain:
    # Khởi tạo chuỗi blockchain
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof = 1, previous_hash = '0')
        self.nodes = set()

    # Tạo mới một khối block
    def create_block(self, proof, previous_hash):
        block = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof': proof,
                 'previous_hash': previous_hash,
                 'transactions': self.transactions}
        self.transactions = []
        self.chain.append(block)
        return block

    # Lây khối cuối cùng của chuỗi block
    def get_previous_block(self):
        return self.chain[-1]

    # Bằng chứng công việc trả về một số sau khi check được sô đo thỏa mãn
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(
                str(new_proof ** 2 - previous_proof ** 2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof

    # Mã hóa chuỗi thành một chuỗi 256 bit
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

        # Check khối chuỗi blockchain
        # kiểm tra nếu previous_hash của khối hiện tại khác với
        # chuỗi hash được trả về sau khi hash dữ liệu của khối trước đó
        # thì trả về False

    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(
                str(proof ** 2 - previous_proof ** 2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True

    # Tạo một transactions (Tạo mới một giao dịch)
    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({'sender': sender,
                                  'receiver': receiver,
                                  'amount': amount})
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1

    # Thêm một node mới vào danh sách nodes
    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    '''
        self.nodes : danh sách các chuỗi nodes
        longest_chain: chuỗi block chain dài nhất
        max_length: độ dài của chuỗi được lấy là độ dài của chuỗi hiện tại
    '''
    '''
        Duyệt qua từng nodes có trong danh sách các nodes
        Sử dụng api get_chain để có thể lấy thông tin và dài của blockchain 
        tại node đó.
        Kiểm tra độ dài của từng node trong danh dách các network đó.
        Nếu node nào dài nhất thì lấy dữ liệu cảu node đó
    '''

    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False


# Part 2: Mining our blockchain
# Creating a web App
app = Flask(__name__)

# Creating ann address for the node on port
node_address = str(uuid4()).replace('-', '')

# Creating a blockchain
blockchain = Blockchain()


# Mining a new block
@app.route('/mine_block', methods = ['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction(sender = node_address, receiver = 'Kirill',
                               amount = 1)
    block = blockchain.create_block(proof, previous_hash)
    response = {'message': 'Congratulations, you just mined a block!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'transactions': block['transactions']}
    return jsonify(response), 200


# Getting the full blockchain
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    if request.method == 'GET':
        response = {'chain': blockchain.chain, 'length': len(blockchain.chain)}
        return jsonify(response), 200


# Check toàn bộ các khối trong chuỗi blockchain
@app.route('/is_valid', methods = ['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': 'All good. The Blockchain is valid!!!'}
    else:
        response = {'message': 'We have a problem. The Blockchain is not valid'}
    return jsonify(response), 200


# Adding a new transaction to the Blockchain
#     api tạo mới một transactions
#     Lấy thông tin được nhập vào
#     Kiểm tra thông tin của các trường có trong transactions_keys. Nếu không tồn
#     tại một trong 3 trường đó thì trả về lỗi

@app.route('/add_transactions', methods = ['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all(key in json for key in transaction_keys):
        return 'Some elements of the transaction are missing!!!', 400
    index = blockchain.add_transaction(json['sender'], json['receiver'],
                                       json['amount'])
    response = {'message': f'This transaction will be added to Block {index}'}
    return jsonify(response), 201


# Part 3: Decentralizing our blockchain
# Connecting new nodes

'''
    Trả về danh sách các nodes
'''


@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return 'No node', 400
    for node in nodes:
        blockchain.add_node(node)
    response = {
        'message': 'All nodes now connected. The hadCoin Blockchain nơ contains the ...',
        'total_nodes': list(blockchain.nodes)}
    return jsonify(response), 201


# replacing the chain by the longest chain if needed
# api replace chain gọi vào function replace chain nếu return True thì có
# dữ liệu được cập nhật trả về dữ liệu sau khi được cập nhật. Còn không
# trả về dữ liệu cũ

@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {
            'message': 'The nodes had different chains so the chain was replaced by the longest...',
            'new_chain': blockchain.chain}
    else:
        response = {'message': 'All good. The chain is the largest one.',
                    'actual_chain': blockchain.chain}
    return jsonify(response), 200

# Running the app
app.run(host = '127.0.0.1', port = 5001, debug = True)
