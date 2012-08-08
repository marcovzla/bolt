import os
import sys
import json
import random
import pprint
from functools import partial
from parsetools import listify, regex_replace_phrases

regex_replacement_phrases = [
    # remove FRAG
    (r'^\(ROOT \(FRAG (.+)\)\)', r'(ROOT \1)'),
    # P
    (r'\(PP \(IN on\) \(NP \(NP \(PRP\$ my\) \(NN side\)\) \(PP \(IN of\) (.+)\)\)\)',
     r'(PP (IN on) (PRP$ my) (NN side) (IN of) \1)'),
    ("\(PP \(IN on\) \(NP \(NP \(DT this\) \(NN side\)\) \(PP \(IN of\)",
     "(PP (P on this side of)"),
    (r'\(PP \(IN on\) \(NP \(NP \(DT the\) \(JJ other\) \(NN side\)\) \(PP \(IN of\)',
     r'(PP (P on the other side of)'),
    ("\(ADJP \(ADJP \(RB very\) \(RB close\)\) \(PP \(TO to\)",
     "(ADVP (RB very) (PP (P close to)"),
    ("\(ADVP \(RB far\) \(PP \(IN from\)", "(PP (P far from)"),
    ("\(ADVP \(RB close\) \(PP \(TO to\)", "(PP (P close to)"),
    # Other (Note: I changed the way OF-phrases are parsed.  --Colin)
    ("\(NP \(NP(?P<NP1>( \(.*?\))*)\) \(PP (?P<of>\(IN of\)) \(NP(?P<NP2>( \(.*?\))*)\)",
     "(OFNP (OFNP1\g<NP1>) (OF of) (OFNP2\g<NP2>))"),
    ("\(ADVP \(RB very\) \(PP ", "(PP (RB very) "),
    ("\(RB not\) \(PP ", "(PP (NEG not) "),
    (r'\(ADVP \(RB nearly\)\) \(PP ', '(PP (RB nearly) '),
    (r'\(ROOT \(ADJP \(JJR closer\) \(PP (.+)\)\)\)', r'(ROOT (PP (JJR closer) \1))'),
    (r'\(NP \(NP \(PRP me\)\) \(PP \(IN than\) (.+)\)\)', r'(PRP me) (IN than) \1'),
]

def to_list(parsetree):
    return listify(parsetree.encode('utf-8').split())[0]

pprinter = pprint.PrettyPrinter()
def pf(obj):
    return pprinter.pformat(obj)

def ngram_tokenizer(sent, n):
    """tokenizes `sent` and adds the right number of beginning of sentence
    and end of sentence tokens, given `n`."""
    return ['<s>'] * (n-1) + sent.split() + ['</s>'] * (n>1)

def ngrams(sent, n):
    """returns the ngrams found in `sent`"""
    tokens = ngram_tokenizer(sent, n)
    return [tuple(tokens[i:i+n]) for i in xrange(len(tokens)-n+1)]

unigrams = partial(ngrams, n=1)
bigrams = partial(ngrams, n=2)
trigrams = partial(ngrams, n=3)

def get_expansion(parse):
    return (parse[0], map(lambda(x): x[0], parse[1:]))

def get_phrases(chunk):
    phrase_tuples = []
    if chunk[0] in ['REL', 'LMK', 'NP', 'PP', 'OFNP', 'OFNP1', 'OFNP2']:
        phrase_tuples.append(get_expansion(chunk))
    for n in chunk[1:]:
        phrase_tuples += get_phrases(n)
    return(phrase_tuples)

def get_words_once(chunk, phrase):
    #formerly get_words()
    return [(' '.join(n[1:]), n[0], phrase) for n in chunk]

def get_words(chunk):
    #formerly lmk_words()
    word_tuples = []
    for n in chunk:
        if isinstance(n, list):
            if n[0] in ['REL', 'LMK', 'NP', 'PP', 'OFNP', 'OFNP1', 'OFNP2']:
                word_tuples += get_words(n)
            else:
                word_tuples += get_words_once([n], chunk[0])
        elif n in ['REL', 'LMK', 'NP', 'PP', 'OFNP', 'OFNP1', 'OFNP2']:
            continue
        else:
            word_tuples.append((n,n,chunk[0]))
    return word_tuples

def modify_parse(parse):
     # modify parsetree
     modparse = regex_replace_phrases(parse, regex_replacement_phrases)
     # listify parsetrees
     lparse = to_list(parse)
     lmodparse = to_list(modparse)
     # extract relation and landmark chunks of the parsetree
     rel_chunk = ['REL'] + lmodparse[1][1:-1]
     lmk_chunk = ['LMK'] + [lmodparse[1][-1]]
     rel_words = get_words(rel_chunk)
     lmk_words = get_words(lmk_chunk)
     rel_phrases = get_phrases(rel_chunk)
     lmk_phrases = get_phrases(lmk_chunk)
     return(rel_words, lmk_words, rel_phrases, lmk_phrases)
