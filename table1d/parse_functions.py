import os
import sys
import json
from post_parse_functions import modify_parse

sys.path.append(os.path.expanduser('~/github/stanford-corenlp-python'))
from corenlp import StanfordCoreNLP
corenlp = StanfordCoreNLP()

def parse_sentence(s):
    """Returns a dictionary with the parse results returned by
    the Stanford parser for the provided sentence."""
    return json.loads(corenlp.parse(s, verbose=False))['sentences'][0]

def get_parse(s):
    """Returns a dictionary with the parse results returned by
    the Stanford parser for the provided sentence."""

    sparse = parse_sentence(s)['parsetree']
    mparse = modify_parse(sparse)
    return mparse
