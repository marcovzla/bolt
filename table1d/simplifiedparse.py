#!/usr/bin/env python

import os
import sys
import csv
import json

#sys.path.append(os.path.expanduser('~/github/stanford-corenlp-python'))
from corenlp import StanfordCoreNLP

from parsetools import listify, replace_phrases, regex_replace_phrases

from generate_relations import *

corenlp = StanfordCoreNLP()

def parse_sentence(s):
    """Returns a dictionary with the parse results returned by
    the Stanford parser for the provided sentence."""
    return json.loads(corenlp.parse(s, verbose=False))['sentences'][0]


regex_replacement_phrases = [
                        # P
                        ("\(PP \(IN on\) \(NP \(NP \(DT this\) \(NN side\)\) \(PP \(IN of\)", "(PP (P on this side of)"),
                        ("\(ADJP \(ADJP \(RB very\) \(RB close\)\) \(PP \(TO to\)", "(ADVP (RB very) (PP (P close to)"),
                        ("\(ADVP \(RB far\) \(PP \(IN from\)", "(PP (P far from)"),
                        ("\(ADVP \(RB close\) \(PP \(TO to\)", "(PP (P close to)"),
                        # Other
                        ("\(NP \(NP(?P<NP1>( \(.*?\))*)\) \(PP (?P<of>\(IN of\)) \(NP(?P<NP2>( \(.*?\))*)\)", "(NP (NP\g<NP1>) of (NP\g<NP2>))"),
                        ("\(ADVP \(RB very\) \(PP ","(PP (RB very) "),
                        ("\(RB not\) \(PP ","(PP (RB not) "),
                       ]

chainlength = 2
def count(listified, parent, countbys):

    if parent:
        expansion = parent+"->"
    else:
        expansion = ""
    expansion += listified[0]+"->"

    for item in listified[1:]:
        if isinstance(item, list):
            this = item[0]
            count(item,listified[0], countbys)
        else:
            this = item
    expansion += this
    for key, countby in countbys:
        if expansion in counts[key]:
            counts[key][expansion]+=countby
        else:
            counts[key][expansion]=countby


if __name__ == '__main__':
    with open('sentences.csv') as f:
        reader = csv.reader(f)
        next(reader)  # skip headers

        rownum=0
        
        counts = {}
        location = 0.5
        countbys = zip( *compute_landmark_posteriors(location) )
        for landmark,landmarkname in ((0.1,'beginning'),(0.5,'middle'),(0.9,'end')):
            reldeg, posterior = compute_rel_posteriors(location,landmark)
            reldeg = [landmarkname+"-"+rel+""+str(deg) for rel,deg in reldeg]
            posterior = posterior.reshape((12,))
            countbys += zip(reldeg,posterior)
        for key, trash in countbys:
            counts[key] = {}
        
        for row in reader:
            location, region, nearfar, precise, phrase = row
            parse = parse_sentence(phrase)['parsetree']
            parse = regex_replace_phrases(parse,regex_replacement_phrases)
            
            print phrase
            print parse
            listified = listify(parse.encode('utf-8').split())
            print listified
            location = float(location)/100.0
            countbys = zip( *compute_landmark_posteriors(location) )
            for landmark,landmarkname in ((0.1,'beginning'),(0.5,'middle'),(0.9,'end')):
                reldeg, posterior = compute_rel_posteriors(location,landmark)
                reldeg = [landmarkname+"-"+rel+""+str(deg) for rel,deg in reldeg]
                posterior = posterior.reshape((12,))
                countbys += zip(reldeg,posterior)
            
            count(  listified[0],None,countbys )
            print ('-' * 50)+str(rownum)
            rownum+=1
            if rownum >= 100:
                break

        print counts
        print "dict size: "+str(len(counts))
