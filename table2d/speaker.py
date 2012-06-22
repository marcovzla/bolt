from planar import Vec2, BoundingBox
from landmark import *
from relations import relations
from numpy import array, random

def main():

    location = Vec2(random.random(),random.random()*2)
    table = RectangleRepresentation()
    
    representations = dict( {'rectangle':table}, **table.get_line_representations() )
    
    epsilon = 0.000001
    landmarks_distances = []
    for name, representation in representations.items():
        landmarks_distances.extend( representation.distance_to_landmarks(location) )
    
    landmarks, distances = zip( *landmarks_distances )
    scores = 1.0/(array(distances)**1.5 + epsilon)
    lm_probabilities = scores/sum(scores)
    index = lm_probabilities.cumsum().searchsorted( random.sample(1) )[0]
    sampled_landmark = landmarks[index]
    
    rel_scores = []
    for relation in relations:
        rel_scores.append( relation.probability(location, sampled_landmark) )
    rel_scores = array(rel_scores)
    rel_probabilities = rel_scores/sum(rel_scores)
    index = rel_probabilities.cumsum().searchsorted( random.sample(1) )[0]
    sampled_relation = relations[index]
    
    print location,';', sampled_relation.get_description() + " " + sampled_landmark.get_description()


import sys
if __name__ == '__main__':
    if len(sys.argv) > 1:
        howmany = int(sys.argv[1])
    else:
        howmany = 100
    for i in range(howmany):
        main()
