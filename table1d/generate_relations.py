from __future__ import division

from numpy import *
from scipy.stats import beta, norm
from itertools import product
from functools import partial

def categorical_sample(values, probs):
    index = random.multinomial(1, probs).nonzero()[0][0]
    value = values[index]
    return(value)

def compute_landmark_posteriors(loc, lmk_names = ['beginning', 'middle', 'end'],
                    lmk_locs = array([0.0, 0.5, 1.0]),
                    prior = array([1, 1, 1]),
                    sigma = 1/4):
    joint = prior * norm.pdf(lmk_locs, loc, sigma)
    posterior = joint / sum(joint)
    return (lmk_names,posterior)

def sample_landmark(loc, lmk_names = ['beginning', 'middle', 'end'],
                    lmk_locs = array([0.0, 0.5, 1.0]),
                    prior = array([1, 1, 1]),
                    sigma = 1/4):
    """
    Randomly chooses a landmark location from the dictionary provided,
    with a bias to choose one nearby to loc

    Parameters
    -----
    loc : (float) a location near which the landmark should be
    lmk_names: (list of strs) a list of landmark labels
    lmk_locs:  (float array) an array of real-valued landmark locations
    prior: (numeric) any prior preferences for landmarks
    sigma : (float) standard deviation of the Gaussian used to bias the selection

    Value
    -----
    Returns a tuple with landmark label (string) and landmark location (float)

    """
    joint = prior * norm.pdf(lmk_locs, loc, sigma)
    posterior = joint / sum(joint)
    which = random.multinomial(1,posterior).nonzero()[0][0]
    key = lmk_names[which]
    lmk = lmk_locs[which]
    return((key,lmk))

def compute_loc_dens(loclmk, reldeg,
                     degprecision = {0: 10.0, 1: 50.0, 2: 100.0}
                     ):
    """
    Evaluate density function for a location, relation and degree

    Parameters
    ----------
    loclmk : (2-tuple)
        (1) (float) location on the table between 0 and 1
        (2) (float) reference location on the table (e.g., 0.5 for the middle)
    reldeg : (2-tuple)
        (1) name of a relation (str) ---
            'is-adjacent':     nearby
            'is-not-adjacent': not nearby
            'is-greater':      past in the oriented interval
            'is-less':         previous in the oriented interval
        (2) precision of relation (int) ---
            0 : low precision
            1 : moderate precision
            2 : high precision
    degprecision : (dict) translating qualitative degrees into
        a+b parameter in beta distribution, or into 1/b in the case
        of convex relations (e.g., is-not-adjacent)

    Value
    -----
    Returns a density (float) corresponding to the likelihood of the
    location given the landmark and relation-degree
    """
    loc, lmk = loclmk
    rel, deg = reldeg
    prec = degprecision[deg]
    if rel == 'is-greater':
        # fit entire distribution past point
        support_width = 1.0 - lmk
        if support_width == 0.0:
            return 0.0
        else:
            loc = (loc - lmk) / support_width
        lmk = 0.0
    elif rel == 'is-less':
        # fit entire distribution previous to point
        support_width = lmk
        if support_width == 0.0:
            return 0.0
        else:
            loc = loc / support_width
        lmk = 1.0
    else:
        # otherwise use the entire interval
        support_width = 1
    if rel == 'is-adjacent':
        peak = lmk
        a = peak * (prec - 2) + 1
        b = prec - a
    else:
        # in this case, the peak is really a trough
        b = 1 / prec
        peak = min(lmk, 1 - lmk)
        a = (peak*(2*prec - 1) - prec) / (prec*(peak - 1))
        if lmk > 0.5: a,b = b,a
    loc = loc * 0.99 + 0.005
    ## Useful for debugging
    #print "Location: %0.3f \n Alpha: %0.3f \n Beta: %0.3f" % (loc, a, b)
    return beta.pdf(loc, a, b) / support_width

def compute_rel_posteriors(lmk,loc,
                           rels = ['is-adjacent', 'is-not-adjacent', 'is-greater', 'is-less'],
                           rel_prior = array([1,1,1,1]),
                           degs = [0,1,2],
                           deg_prior = array([1,1,1]),
                           verbose = False
                           ):
    """
    Compute posterior probabilities of each relation-degree,
    given a location and a landmark.

    Parameters
    ----------
    loc : (float) the location in question
    lmk : (float) the location of the landmark
    rels : (str list) names of possible relations
    degs : (int list) degrees being considered (keys of 
        deglocation and degprecision args of compute_loc_dens)
    rel_prior : (array) prior weights for the relations
    deg_prior : (array) prior weights for the degrees
    
    Value
    -----
    Returns a tuple with (1) relation-degree combinations and
    (2) an array of posterior probabilities of those combinations
    """
    loclmk = (loc,lmk)
    numrels = len(rels)
    numdegs = len(degs)
    numpairs = numrels * numdegs
    reldegs = list(product(rels, degs))
    # Assume the prior weights have independent influence
    prior = outer(rel_prior, deg_prior).ravel()
    likelihood = [compute_loc_dens(loclmk, rd) for rd in reldegs]
    joint = prior * likelihood
    posterior = joint / sum(joint)
    if verbose:
        for j in range(numpairs):
            print "%-25s: \t %-6.6f" % (str(reldegs[j]), posterior[j])
    return(reldegs, posterior)

def sample_reldeg(lmk,loc,
                  rels = ['is-adjacent', 'is-not-adjacent', 'is-greater', 'is-less'],
                  rel_prior = array([1,1,1,1]),
                  degs = [0,1,2],
                  deg_prior = array([1,1,1])
                  ):
    """
    Randomly sample a relation-degree pair, given a location and landmark location

    Parameters
    ----------
    loc : (float) the location in question
    lmk : (float) the location of the landmark
    rels : (str list) names of possible relations
    degs : (int list) degrees being considered (keys of 
        deglocation and degprecision args of compute_loc_dens)
    """ 
    reldegs, posterior = compute_rel_posteriors(lmk,loc,
                                                rels, rel_prior,
                                                degs, deg_prior)
    # This seems inefficient
    return(reldegs[random.multinomial(1, posterior).nonzero()[0][0]])

def generate_relation(loc, lmk_names = ['beginning', 'middle', 'end'],
                      lmk_locs = array([0.0, 0.5, 1.0]),
                      lmk_prior = array([1, 1, 1]),
                      rels = ['is-adjacent', 'is-not-adjacent', 'is-greater', 'is-less'],
                      rel_prior = array([1,1,1,1]),
                      degs = [0,1,2],
                      deg_prior = array([1,1,1]),
                      sigma = 1/4):
    lmk_name, lmk_loc = sample_landmark(loc, lmk_names, lmk_locs, lmk_prior, sigma)
    reldeg = sample_reldeg(loc, lmk_loc, rels, rel_prior, degs, deg_prior)
    return(lmk_name, reldeg)

def get_lmk_rel_probs(loc, lmk_names = ['beginning','middle','end'],
                      lmk_locs = array([0.0, 0.5, 1.0]),
                      lmk_prior = array([1,1,1]),
                      rels = ['is-adjacent', 'is-not-adjacent', 'is-greater', 'is-less'],
                      rel_prior = array([1,1,1,1]),
                      degs = [0,1,2],
                      deg_prior = array([1,1,1]),
                      sigma = 1/4):
    labels = list(product(lmk_names, rels, degs))
    lmk_probs = compute_landmark_posteriors(loc, lmk_names, lmk_locs, lmk_prior, sigma)[1]
    get_rel_posteriors = partial(compute_rel_posteriors, loc = loc, rels = rels,
                                 rel_prior = rel_prior, degs = degs, deg_prior = deg_prior)
    all_rel_probs = concatenate([map(get_rel_posteriors, lmk_locs)[k][1] for k in range(len(lmk_names))])
    joint_probs = concatenate([lmk_probs]*len(rels)*len(degs)) * all_rel_probs
    table = [(labels[i], joint_probs[i]) for i in range(len(labels))]
    return(table)
    
    
    
