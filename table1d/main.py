#!/usr/bin/env python

import random



def get_landmark(location):
    """Returns the best landmark given the location.
    
    A landmark is an abstract object that represents one of three
    special locations in the table. These locations are the center
    and both ends."""
    # TODO



def get_relation(location, landmark):
    """Returns an object that represents the kind of relationship
    between the location of interest and the landmark, given the
    distance between them."""
    # TODO



def get_landmark_description(landmark, precise):
    """Returns a description for `landmark`. If `landmark` is one
    of the ends of the table, we only specify which one it is if
    `precise` is set to `True`."""
    # TODO



def get_relation_description(relation, precise):
    """Returns a description for `relation`."""
    # TODO



def merge_descriptions(landmark_desc, relation_desc):
    """Returns a correct sentence for the descriptions."""
    # TODO



def generate_sentence(landmark, relation, precise):
    """Returns a sentence that describes a location on the table
    indirectly. It does this by describing a relation to a landmark."""
    landmark_desc = get_landmark_description(landmark, precise)
    relation_desc = get_relation_description(relation, precise)
    return merge_descriptions(landmark_desc, relation_desc)



def get_sentence(location, precise):
    """Returns a sentence that describes a location on the table."""
    landmark = get_landmark(location)
    relation = get_relation(location, landmark)
    return generate_sentence(landmark, relation, precise)



def get_location_distribution(sentence):
    """Returns a `dict` in which each key represents a location
    and its value represents the probability that `sentence` is
    referring to that particular location."""
    # TODO



def get_location(sentence):
    """Returns a location given a sentence."""
    return weighted_choice(get_location_distribution(sentence))



# as seen on http://stackoverflow.com/a/6432628
def weighted_choice(dist):
    """Gets a `dict` of probabilities and returns one of its keys
    based on its probability.

        >>> dist = {'a': .1, 'b': .2, 'c': .3, 'd': .4}

        >>> [weighted_choice(dist) for _ in xrange(5)]
        ['c', 'b', 'b', 'c', 'd']

        >>> from collections import Counter
        >>> Counter(weighted_choice(dist) for _ in xrange(10**5))
        Counter({'d': 40198, 'c': 29931, 'b': 19938, 'a': 9933})
    """
    r = random.random()
    total = 0
    for val,prob in dist.iteritems():
        total += prob
        if total > r:
            return val
    raise Exception('distribution not normalized: {dist}'.format(dist=dist))



# as seen on http://old.nabble.com/Re%3A-Plotting-histogram-with-dictionary-values-p30986949.html
def plot_histogram(dist):
    """Gets a `dict` with labels in its keys and frequencies in its values
    and plots it as a histogram.
    
        >>> dist = {'a': .1, 'b': .2, 'c': .3, 'd': .4}

        >>> plot_histogram(dist)
    """
    # don't import this stuff unless we actually want to plot something
    import numpy as np
    import matplotlib.pyplot as plt

    x = dist.keys()
    y = dist.values()
    xlocs = np.arange(len(x))

    fig = plt.figure()
    ax = fig.gca()
    ax.bar(xlocs + 0.6, y)
    ax.set_xticks(xlocs + 1)
    ax.set_xticklabels(x)
    ax.set_xlim(0.0, xlocs.max() + 2)

    plt.show()



if __name__ == '__main__':
    while True:
        user_input = raw_input('> ')

        try:
            # if the user specified a location
            location = int(user_input)

            # do we want to be precise or ambiguous?
            precise = weighted_choice({True: .8, False: .2})

            print 'A good description for location %s is:' % location
            print '\t"%s"' % get_sentence(location, precise)

        except ValueError:
            # if the user wrote a sentence
            dist = get_location_distribution(user_input)
            plot_histogram(dist)
            location = weighted_choice(dist)
            print 'I bet you are talking about location %s' % location

        print  # empty line
