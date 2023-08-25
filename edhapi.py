#!/bin/python3
# This is a file that is just leeching off of the edhmaker.py for another project.
# It's not ideal but to be fair, I'm writing a dissertation proposal right now
# And I wanted to implement this is an afternoon as a break.
from os import path
import urllib.parse
from flask import Flask, jsonify
from flask_cors import CORS
from utilities.edhmaker import EDHMaker

app = Flask(__name__)
CORS(app)
deckgen = EDHMaker(None, path.dirname(__file__)+'/utilities/edhmaker_data')


@app.route("/edh")
def makeDeck():
    return jsonify(deckgen.makeDeck())

@app.route("/edh/colors/<colors>")
def makeColorDeck(colors):
    cid = []
    if colors != "none":
        cid = deckgen.tupleToColorID(colors)
    cmdrs = deckgen.getCMDROnColor(cid)
    response = jsonify(deckgen.makeDeck(cmdrList=cmdrs))
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

@app.route("/edh/commander/<commander1>")
def makeDeck1Commander(commander1):
    cmdrs = []
    #sc1 = urllib.parse.unquote(commander1) 
    cmdrs.append(deckgen.findBestCardMatch(commander1, deckgen.getLegalDict())[0])
    response = jsonify(deckgen.makeDeck(cmdrList=cmdrs))
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

@app.route("/edh/commander/<commander1>/<commander2>")
def makeDeck2Commanders(commander1, commander2):
    cmdrs = []
    #sc1 = urllib.parse.unquote(commander1)
    #sc2 = urllib.parse.unquote(commander2)
    cmdrs.append(deckgen.findBestCardMatch(commander1, deckgen.getLegalDict())[0])
    cmdrs.append(deckgen.findBestCardMatch(commander2, deckgen.getLegalDict())[0])
    response = jsonify(deckgen.makeDeck(cmdrList=cmdrs))
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=5001)
