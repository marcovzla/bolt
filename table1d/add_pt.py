#!/usr/bin/env python

import os
import sys
import csv
import json

sys.path.append(os.path.expanduser('~/github/stanford-corenlp-python'))
from corenlp import StanfordCoreNLP
corenlp = StanfordCoreNLP()



# I propose this csv dialect for all our bolt csv files
# as a first step into standardizing our data files
csv.register_dialect('bolt',
        quoting=csv.QUOTE_ALL,
        doublequote=False,
        escapechar='\\',
        lineterminator='\n')



def parse_sentence(s):
    """Returns a dictionary with the parse results returned by
    the Stanford parser for the provided sentence."""
    return json.loads(corenlp.parse(s, verbose=False))['sentences'][0]



if __name__ == '__main__':
    with open('sentences.csv', 'rb') as fi, open('sentences2.csv', 'wb') as fo:
        reader = csv.reader(fi)
        writer = csv.writer(fo, 'bolt')

        # write headers
        headers = next(reader)
        writer.writerow(headers + ['PARSETREE'])

        for i,row in enumerate(reader, 1):
            parsetree = parse_sentence(row[-1])['parsetree']
            writer.writerow(row + [parsetree])
            print i
