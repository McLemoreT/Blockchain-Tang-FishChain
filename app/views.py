import datetime
import json

import requests
from flask import render_template, redirect, request

from app import app

# The node with which our application interacts, there can be multiple
# such nodes as well.
CONNECTED_NODE_ADDRESS = "http://127.0.0.1:8000"

posts = []


def fetch_posts():
    """
    Function to fetch the chain from a blockchain node, parse the
    data and store it locally.
    """
    get_chain_address = "{}/chain".format(CONNECTED_NODE_ADDRESS)
    response = requests.get(get_chain_address)
    if response.status_code == 200:
        content = []
        chain = json.loads(response.content)
        for block in chain["chain"]:
            for tx in block["transactions"]:
                tx["index"] = block["index"]
                tx["hash"] = block["previous_hash"]
                content.append(tx)

        global posts
        posts = sorted(content, key=lambda k: k['timestamp'],
                       reverse=True)


def fetch_fish(guid):
    """
    Function to fetch the chain from a blockchain node, parse the
    data and store it locally.
    """
    get_chain_address = "{}/fishtory?guid={}".format(CONNECTED_NODE_ADDRESS, guid)
    response = requests.get(get_chain_address)
    if response.status_code == 200:
        fish = json.loads(response.content)
        return fish
    else:
        print('Did not receive OK200: ' + response.status_code)


@app.route('/')
def index():
    fetch_posts()
    return render_template('index.html',
                           title='Fish: Decentralized '
                                 'Fish Sharing',
                           posts=posts,
                           node_address=CONNECTED_NODE_ADDRESS,
                           readable_time=timestamp_to_string)


@app.route('/fishtory')
def fishtory():
    guid = request.args.get('guid')
    if guid != None:
        fish = fetch_fish(guid)
    else:
        fish = []
    return render_template('fish.html',
                            title='What is up with my fish?',
                            fish=fish,
                            node_address=CONNECTED_NODE_ADDRESS,
                            readable_time=timestamp_to_string)


@app.route('/txn/regulator')
def txn_regulator():
    return render_template('regulator.html',
                            title='FishChain - Mint a fish',
                            node_address=CONNECTED_NODE_ADDRESS,
                            readable_time=timestamp_to_string)


@app.route('/txn/fisher')
def txn_fisher():
    return render_template('fisher.html',
                            title='FishChain - Catch a fish',
                            node_address=CONNECTED_NODE_ADDRESS,
                            readable_time=timestamp_to_string)


@app.route('/txn/grocer')
def txn_grocer():
    return render_template('grocer.html',
                            title='FishChain - Buy a fish',
                            node_address=CONNECTED_NODE_ADDRESS,
                            readable_time=timestamp_to_string)


@app.route('/txn/customer')
def txn_customer():
    return render_template('customer.html',
                            title='FishChain - Consume a fish',
                            node_address=CONNECTED_NODE_ADDRESS,
                            readable_time=timestamp_to_string)


def post_txn(post_object):
    # Submit a transaction
    new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)
    print(new_tx_address)
    print(post_object)

    requests.post(new_tx_address,
                  json=post_object,
                  headers={'Content-type': 'application/json'})

    return redirect('/')


@app.route('/submit/mint', methods=['POST'])
def submit_txn_mint():
    """
    Endpoint to create a new transaction via our application.
    """

    consumption = 0 # MINTED

    post_object = {
        'consumption': consumption,
    }
    return post_txn(post_object)


@app.route('/submit/fished', methods=['POST'])
def submit_txn_fished():
    """
    Endpoint to create a new transaction via our application.
    """
    guid = request.form["guid"]
    print('Guid ' + guid)
    fish = fetch_fish(guid)
    print(fish[0].get('consumption'))
    if fish[0].get('consumption') != 0:
        print("Fish not in state 0, is " + fish[0].get('consumption'))
        return redirect('/')

    speciesId = request.form["speciesId"]
    caughtLat = request.form["caughtLat"]
    caughtLong = request.form["caughtLong"]
    consumption = 1 # FISHED

    post_object = {
        'guid': guid,
        'speciesId': speciesId,
        'caughtLat': caughtLat,
        'caughtLong': caughtLong,
        'consumption': consumption,
    }
    return post_txn(post_object)


@app.route('/submit/sold', methods=['POST'])
def submit_txn_sold():
    """
    Endpoint to create a new transaction via our application.
    """

    guid = request.form["guid"]
    fish = fetch_fish(guid)
    if fish == None:
        # Error looking up fish. It might not exist?
        print("Fish is None")
        return redirect('/')

    lastConsumption = fish[len(fish) - 1].get('consumption')
    if lastConsumption != 1 and lastConsumption != 2:
        print("Fish must be state 1 or 2, is " + str(lastConsumption))
        return redirect('/')

    speciesId = fish[1].get('speciesId')
    caughtLat = fish[1].get('caughtLat')
    caughtLong = fish[1].get('caughtLong')
    consumption = 2 # SOLD

    post_object = {
        'guid': guid,
        'speciesId': speciesId,
        'caughtLat': caughtLat,
        'caughtLong': caughtLong,
        'consumption': consumption,
    }
    return post_txn(post_object)


@app.route('/submit/consumed', methods=['POST'])
def submit_txn_consumed():
    """
    Endpoint to create a new transaction via our application.
    """

    guid = request.form["guid"]
    fish = fetch_fish(guid)
    if fish == None:
        # Error looking up fish. It might not exist?
        print("Fish is None")
        return redirect('/')

    lastConsumption = fish[len(fish) - 1].get('consumption')
    if lastConsumption != 2:
        print("Fish must be state 2, is " + str(lastConsumption))
        return redirect('/')

    speciesId = fish[1].get('speciesId')
    caughtLat = fish[1].get('caughtLat')
    caughtLong = fish[1].get('caughtLong')
    consumption = 3 # CONSUMED

    post_object = {
        'guid': guid,
        'speciesId': speciesId,
        'caughtLat': caughtLat,
        'caughtLong': caughtLong,
        'consumption': consumption,
    }
    return post_txn(post_object)


def timestamp_to_string(epoch_time):
    return datetime.datetime.fromtimestamp(epoch_time).strftime('%H:%M')
