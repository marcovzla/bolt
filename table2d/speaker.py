from relations import relations
from numpy import array, random

class Speaker(object):
    def __init__(self, location):
        self.location = location

    def describe(self, location, scene):
        table = scene.landmarks['table'].representation

        representations = [table]
        representations.extend(table.get_alt_representations())

        epsilon = 0.000001
        landmarks_distances = []
        for representation in representations:
            for lmk in representation.get_landmarks():
                landmarks_distances.append([lmk, lmk.distance_to(location)])

        for obj in [scene.landmarks['obj1'], scene.landmarks['obj2']]:
            landmarks_distances.append([obj, obj.distance_to(location)])

        print landmarks_distances

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


# import sys
# if __name__ == '__main__':
#     if len(sys.argv) > 1:
#         howmany = int(sys.argv[1])
#     else:
#         howmany = 100
#     for i in range(howmany):
#         main()
