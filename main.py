import requests
from flask import Flask, jsonify, request

from lib import blockchain

first_node = '127.0.0.1:8080'
app = Flask(__name__)
chain = blockchain.BlockChain(first_node=first_node)

@app.route('/init')
def init():
    return requests.get('http://{first_node}/add-nodes/{host}/{port}'.format(first_node=first_node, host=host, port=port)).json()

@app.route('/new-vote', methods=['POST'])
def new_vote():
    values = request.form
    if values['person_id'] == '' or values['vote'] == '':
        return 'Missing values', 400
    index = chain.new_vote(values['person_id'], values['vote'])
    if index:
        response = {'message': f'Your vote added to block'}
        return jsonify(response), 201
    else:
        response = {'message': f'You voted before'}
        return jsonify(response), 400

@app.route('/add-nodes/<host>/<port>', methods=['GET'])
def add_nodes(host, port):
    req_url = host + ':' + port
    chain.nodes.add(req_url)
    response = {
        'nodes': list(chain.nodes),
        'length': len(chain.nodes),
    }
    return jsonify(response), 201

@app.route('/nodes', methods=['GET'])
def nodes():
    response = {
        'nodes': list(chain.nodes),
        'length': len(chain.nodes),
    }
    return jsonify(response), 201

@app.route('/current-votes', methods=['GET'])
def current_votes():
    #chain.update_current_votes()
    response = {
        'current_votes': chain.current_votes,
        'length': len(chain.current_votes),
    }
    return jsonify(response), 201

@app.route('/chain')
def full_chain():
    #chain.resolve_conflicts()
    response = {
        'chain': chain.chain,
        'length': len(chain.chain), 
    }
    return jsonify(response), 200

@app.route('/update-block')
def update_block():
    chain.update_block()
    response = {'message': f'Everything is update'}
    return jsonify(response), 400

@app.route('/mine', methods=['GET'])
def mine():
    chain.update_block()
    if len(chain.current_votes) != 0:
        last_block = chain.last_block()
        last_proof = last_block['proof']
        proof = chain.pow(last_proof)
        
        pre_hash = chain.hash(last_block)
        block = chain.new_block(proof, pre_hash)
        response = {
            'message': "New Block Forged",
            'index': block['index'],
            'votes': block['votes'],
            'proof': block['proof'],
            'previous_hash': block['previous_hash'],
        }
        return jsonify(response), 200
    else:
        response = {'message': f'Do not exist vote(s) for mining'}
        return jsonify(response), 200

@app.route('/count-votes')
def count_votes():
    count = dict()
    chain.resolve_conflicts()
    len_chain = len(chain.chain)
    for i in range(len_chain):
        for j in range(len(chain.chain[i]['votes'])):
            for k in range(len(list(chain.chain[i]['votes'][j]['vote']))):
                if list(chain.chain[i]['votes'][j]['vote'])[k] == '1':
                    if str(k) not in count.keys():
                        count[str(k)] = 1
                    else:
                        count[str(k)] += 1
                    
    return jsonify(count), 400

if __name__ == '__main__':
    host = input('Enter your host : \n')
    port = input('Enter your port : \n')
    app.run(host=host, port=port)