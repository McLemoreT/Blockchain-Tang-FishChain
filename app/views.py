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
        content = []
        fish = json.loads(response.content)
        return fish


@app.route('/')
def index():
    fetch_posts()
    return render_template('index.html',
                           title='Fish: Decentralized '
                                 'fish sharing',
                           posts=posts,
                           node_address=CONNECTED_NODE_ADDRESS,
                           readable_time=timestamp_to_string)


@app.route('/fishtory')
def fishtory():
    guid = request.args.get('guid')
    fish = fetch_fish(guid)
    return render_template('fish.html',
                            title='What is up with my fish?',
                            fish=fish,
                            node_address=CONNECTED_NODE_ADDRESS,
                            readable_time=timestamp_to_string)


@app.route('/submit', methods=['POST'])
def submit_textarea():
    """
    Endpoint to create a new transaction via our application.
    """
    guid = request.form["guid"]
    speciesId = request.form["speciesId"]
    caughtLat = request.form["caughtLat"]
    caughtLong = request.form["caughtLong"]
    consumption = request.form["consumption"]

    post_object = {
        'guid': guid,
        'speciesId': speciesId,
        'caughtLat': caughtLat,
        'caughtLong': caughtLong,
        'consumption': consumption,
    }

    # Submit a transaction
    new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)
    print(new_tx_address)

    requests.post(new_tx_address,
                  json=post_object,
                  headers={'Content-type': 'application/json'})

    return redirect('/')


def timestamp_to_string(epoch_time):
    return datetime.datetime.fromtimestamp(epoch_time).strftime('%H:%M')
