#!/usr/bin/env python

import csv
import sys
from collections import defaultdict
from operator import itemgetter

import string
import re

#filename = 'parsetrees.csv'
#parseindex = 1
#filename = 'groups.csv'
#parseindex = 2

join_spaces = " ".join
'''
phrases_replacements = [(" (NN close)) (PP (TO to)", ") (PP close to"),
                        ("(RB far) (PP (IN from)", "(PP far from"),
                        ("(PP (TO to) (NP (NP (DT the) (NN left)) (PP (IN of)", "(PP (PP (PP to the left of"),
                        ("(JJ next) (PP (TO to)", "(PP next to"),
                        ("(PP (TO to) (NP (NP (DT the) (NN right)) (PP (IN of)", "(PP (PP (PP to the right of"),
                        ("(PP (IN in) (NP (NP (NN front)) (PP (IN of)", "(PP (PP (PP in front of)"),
                        ("(PP (IN in) (NP (NP (DT the) (NN middle)) (PP (IN of)", "(PP (PP (PP in the middle of)"),
                        ("(PP (IN in) (NP (DT the) (NN middle))) (PP (IN of)", "(PP (PP in the middle of)"),
                        ("(PP (IN in) (NP (DT the) (NN middle)", "(PP (PP (PP in the middle)"),
                        ("(PP (IN in) (NP (NP (DT the) (NN center)) (PP (IN of)", "(PP (PP (PP in the center of)"),
                        ("(PP (IN in) (NP (DT the) (NN center))) (PP (IN of)", "(PP (PP in the center of)"),
                        ("(PP (IN in) (NP (DT the) (NN center)", "(PP (PP (PP in the center)"),
                        ("(PP (IN in) (NP (DT the) (NN back)", "(PP (PP (PP in the back)"),
                        ("(PP (IN in) (NP (DT the) (NN front)", "(PP (PP (PP in the front)"),
                       ]
'''
def replace_phrases(statement, phrases):
    for phrase, replacement in phrases:
        statement = statement.replace(phrase, replacement)
    return statement

def regex_replace_phrases(statement, regex_phrases):
    for phrase, replacement in regex_phrases:
        statement = re.sub(phrase, replacement, statement)
    return statement

def listify(statement):

    assert( statement[0][0] == "(" )
    l = [ statement[0][1:] ]

    rest = statement[1:]
    while rest != []:
        if rest[0][0] == "(":
            ll, rest = listify(rest)
            l.append(ll)
        else:
            token,sep,remainder = rest[0].partition(")")

            if token:
                l.append( token )

            if remainder:
                rest[0] = remainder
            else:
                rest = rest[1:]

            if sep:
                return l, rest

def collapse(statement, words):
    newstatement = []
    for i,term in enumerate(statement):
        if isinstance(term, list):
            newstatement.extend( collapse(term, words) )
        else:
            newstatement.append(term)

    anything = [word for word in words if word in newstatement]
    if anything:
        return newstatement[1:]
    else:
        return newstatement[0:1]

def sentence(statement):
    newstatement = []
    for i,term in enumerate(statement):
        if isinstance(term, list):
            newstatement.extend( sentence(term) )
        else:
            newstatement.append(term)

    return newstatement[1:]

def ngrams(tokens, MIN_N, MAX_N, count, mustcontain):
    assert( isinstance(mustcontain, set) )
    n_tokens = len(tokens)
    for i in xrange(n_tokens):
        for j in xrange(i+MIN_N, min(n_tokens, i+MAX_N)+1):
            if len( mustcontain.intersection(tokens[i:j]) ) > 0:
                if (j-i) not in count:
                    count[j-i] = defaultdict(int)
                count[j-i][join_spaces(tokens[i:j])] += 1

def ngrams2(tokens, MIN_N, MAX_N):
    toreturn = set()
    n_tokens = len(tokens)
    for i in xrange(n_tokens):
        for j in xrange(i+MIN_N, min(n_tokens, i+MAX_N)+1):
            toreturn.add( join_spaces(tokens[i:j]) )
    return toreturn

'''

words = set(['above','across','after','against','along','alongside','amid','amidst','among','amongst','at','atop','back','before','behind','below','beneath','beside','between','beyond','bottom','by','center','close','down','far','front','inside','left','middle','near','next','off','on','opposite','out','outside','over','right','top','toward','towards','under','underneath','up'])



with open(filename) as f:
    reader = csv.reader(f)
    collapsed = []
    count = {}
    minn, maxn = 3, 7

    for line in reader:
        l = replace_phrases(line[parseindex], phrases_replacements)
        ll = listify(l.split())[0]
        c = collapse(ll,words)
        ngrams(c,minn,maxn,count,words)

    tophowmany = 20
    topngrams = {}
    for key in count:
        topngrams[key] = [ x[0] for x in sorted(count[key].iteritems(), key=itemgetter(1), reverse=True)[:tophowmany] ]


    f.seek(0)
    print "Index,Sentence,Parse,Collapsed,Common",
    for i in range(maxn,minn-1,-1):
        print str(i)+"-grams,",
    print
    for line in reader:
        l = replace_phrases(line[parseindex], phrases_replacements)
        ll = listify(l.split())[0]
        c = collapse(ll,words)
        s = join_spaces( sentence(ll) )

        sys.stdout.write( line[0]+',"'+s+'","'+line[parseindex]+'","'+join_spaces(c)+'",')
        maxn,minn = 7,3
        for i in range(maxn,minn-1,-1):
            ng = ngrams2(c,i,i)
            present = ngrams2(c,i,i).intersection(topngrams[i])
            if present != set([]):
                sys.stdout.write('"'+str(list(present))+'"')
            sys.stdout.write(',')
        print

#        ngrams(c, minn, maxn, count)



#n_grams = sorted(count.iteritems(), key=itemgetter(1), reverse=True)
n_grams = sorted(count.iteritems(), key=lambda a:(len(a[0].split()),-a[1]) )

n_gramss = {}
for n_gram, count in n_grams:
    length = len(n_gram.split())
    if length not in n_gramss:
        n_gramss[length] = []
    n_gramss[length].append((n_gram,count))

sys.stdout.write( ',' )
for key in n_gramss.keys():
    sys.stdout.write( str(key)+',,,' )
print

n_gramss = map( None, *(n_gramss.values()) )

for row in n_gramss:
    sys.stdout.write( ',' )
    for n_gram in row:
        if n_gram == None:
            sys.stdout.write(',,,')
        else:
            sys.stdout.write( '"'+n_gram[0]+'",'+str(n_gram[1])+',,' )
    sys.stdout.write('\n')

#for n_gram in n_grams:
#    sys.stdout.write( str(len(n_gram[0].split()))+',"'+n_gram[0]+'",'+str(n_gram[1])+'\n' )
'''
