import os
import sys
import json
from post_parse_functions import modify_parse

# sys.path.append(os.path.expanduser('~/github/stanford-corenlp-python'))
# from corenlp import StanfordCoreNLP
# corenlp = StanfordCoreNLP()

# we will connect to StanfordCoreNLP as a server
# NOTE it has to be running
import jsonrpc
server = jsonrpc.ServerProxy(jsonrpc.JsonRpc20(),
                             jsonrpc.TransportTcpIp(addr=("127.0.0.1",
                                                          8080)))

def parse_sentence(s):
    """Returns a dictionary with the parse results returned by
    the Stanford parser for the provided sentence."""
    return json.loads(server.parse(s))['sentences'][0]

def get_parse(s):
    """Returns a dictionary with the parse results returned by
    the Stanford parser for the provided sentence."""

    sparse = parse_sentence(s)['parsetree']
    mparse = modify_parse(sparse)
    return mparse
