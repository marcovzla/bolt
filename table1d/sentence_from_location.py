#!/usr/bin/env python

from __future__ import division

from tabledb import *
from generate_relations import *
from numpy import *
from ast import literal_eval


sys.path.append(os.path.expanduser('~/github/stanford-corenlp-python'))
from corenlp import StanfordCoreNLP
corenlp = StanfordCoreNLP()

def get_context(loc, meaning = ()):
    if len(meaning):
        rel,deg,lmk_name,lmk_loc = meaning
    else:
        lmk_name, lmk_loc = sample_landmark(loc)
        rel, deg = sample_reldeg(loc, lmk_loc)
    rel_ctx = RelationContext.get_by(
        relation = rel,
        degree = deg)
    lmk_ctx = LandmarkContext.get_by(
        landmark_name = lmk_name,
        landmark_location = lmk_loc)
    ctx = Context.get_by(
        relation = rel_ctx,
        landmark = lmk_ctx)
    print "Landmark: %s" % lmk_name
    print "Relation: %s" % rel
    print "Degree: %s" % deg
    return(rel_ctx, lmk_ctx, ctx)

def get_expansion(rel_ctx, lmk_ctx, ctx, phr, role):
    phrase = Phrase.get_by(phrase = phr)
    ## exp_db = PhraseExpansion.query.filter_by(parent = phrase,
    ##                                          context = ctx)
    ## num_exp = exp_db.count()
    ## if num_exp == 0:
    if role == 'rel':
        exp_db = PhraseExpansion.query.filter_by(parent = phrase,
                                                 relation_context = rel_ctx)
    else:
        exp_db = PhraseExpansion.query.filter_by(parent = phrase,
                                                 landmark_context = lmk_ctx)
    num_exp = exp_db.count()
    if num_exp == 0:
        exp_db = PhraseExpansion.query.filter_by(parent = phrase)
        num_exp = exp_db.count()
    ## else:
    ##     exp_db = PhraseExpansion.query.filter_by(parent = phrase,
    ##                                              context = ctx)
    expn = categorical_sample(exp_db.all(), [1.0 / num_exp] * num_exp).expansion
    print "Expanding %s to %s" % (phr, expn)
    return(expn)

def get_words(rel_ctx, lmk_ctx, ctx, phr, expn, role):
    words = []
    phrase = Phrase.get_by(phrase = phr)
    for n in literal_eval(expn):
        if n in ['REL', 'LMK', 'PP', 'OFNP', 'OFNP1', 'OFNP2', 'NP']:
            expansion = get_expansion(rel_ctx, lmk_ctx, ctx, n, role)
            words += get_words(rel_ctx, lmk_ctx, ctx, n, expansion, role)
        else:
            pos = PartOfSpeech.get_by(pos = n, role = role)
            ## w_db = Word.query.filter_by(
            ##     phrase = phrase,
            ##     pos = pos,
            ##     relation_context = rel_ctx,
            ##     landmark_context = lmk_ctx,
            ##     context = ctx)
            ## num_w = w_db.count()
            ## if num_w == 0:
            if role == 'rel':
                w_db = Word.query.filter_by(
                    phrase = phrase,
                    pos = pos,
                    relation_context = rel_ctx)
                num_w = w_db.count()
            else:
                w_db = Word.query.filter_by(
                    phrase = phrase,
                    pos = pos,
                    landmark_context = lmk_ctx)
                num_w = w_db.count()
            w = categorical_sample(w_db.all(), [1.0 / num_w] * num_w).word
            words += [w]
    print "Expanding %s to %s" % (expn, words)
    return words

## if __name__ == '__main__':
##     import optparse
##     p = optparse.OptionParser()
##     p.add_option('--location', '-l', default=0.5)
##     opts, args = p.parse_args()

def generate_sentence(loc, meaning = ()):
    if len(meaning):
        try:
            rc,lc,c = get_context(None, meaning)
        except ValueError:
            print "Meaning has the wrong number of pieces"
    else:
        rc,lc,c = get_context(loc)
    rs = get_expansion(rc,lc,c,'REL','rel')
    ls = get_expansion(rc,lc,c,'LMK','lmk')
    rw = get_words(rc,lc,c,'REL',rs,'rel')
    lw = get_words(rc,lc,c,'LMK',ls,'lmk')
    sentence = ' '.join(rw + lw)
    return sentence
    
