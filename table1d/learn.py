#!/usr/bin/env python

import os
import sys
import csv
import json

sys.path.append(os.path.expanduser('~/github/stanford-corenlp-python'))
from corenlp import StanfordCoreNLP

corenlp = StanfordCoreNLP()

def parse_sentence(s):
    """Returns a dictionary with the parse results returned by
    the Stanford parser for the provided sentence."""
    return json.loads(corenlp.parse(s, verbose=False))['sentences'][0]

if __name__ == '__main__':
    with open('sentences.csv') as f:
        reader = csv.reader(f)
        next(reader)  # skip headers
        for row in reader:
            location, region, nearfar, precise, phrase = row
            parse = parse_sentence(phrase)
            
            print phrase
            print parse['parsetree']
            print '-' * 50
