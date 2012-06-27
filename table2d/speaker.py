from relations import relations
from numpy import array, random
from matplotlib import pyplot as plt
from landmark import PointRepresentation, LineRepresentation, RectangleRepresentation

class Speaker(object):
    def __init__(self, location):
        self.location = location

    def describe(self, poi, scene):
        epsilon = 0.000001
        scenes = scene.get_child_scenes(poi) + [scene]
        print str(len(scenes)) + str(scenes)

        landmarks_distances = []

        for s in scenes:
            for scene_lmk in s.landmarks.values():
                landmarks_distances.append([s, scene_lmk, scene_lmk.distance_to(poi)])

                representations = []
                representations.extend(scene_lmk.representation.get_alt_representations())

                for representation in representations:
                    for lmk in representation.get_landmarks():
                        landmarks_distances.append([s, lmk, lmk.distance_to(poi)])

        sceness, landmarks, distances = zip( *landmarks_distances )
        print landmarks_distances
        scores = 1.0/(array(distances)**1.5 + epsilon)
        lm_probabilities = scores/sum(scores)
        index = lm_probabilities.cumsum().searchsorted( random.sample(1) )[0]
        sampled_scene = sceness[index]
        sampled_landmark = landmarks[index]

        rel_scores = []
        for relation in relations:
            rel_scores.append( relation.probability(poi, sampled_landmark) )
        rel_scores = array(rel_scores)
        rel_probabilities = rel_scores/sum(rel_scores)
        index = rel_probabilities.cumsum().searchsorted( random.sample(1) )[0]
        sampled_relation = relations[index]

        print poi,';', sampled_relation.get_description() + " " + sampled_landmark.get_description(self.location)
        self.visualize(sampled_scene, poi, sampled_landmark)


    def visualize(self, scene, poi, sampled_landmark):

        plt.figure( figsize=(10,5) )
        plt.subplot(1,2,1)
        plt.axis([4.3,6.7,4.5,7.5])

        print 'drawing scene ', len(scene.landmarks)
        for lmk in scene.landmarks.values():
            print 'drwaing ', lmk.name
            if isinstance(lmk.representation, RectangleRepresentation):
                rect = lmk.representation.rect
                xs = [rect.min_point.x,rect.min_point.x,rect.max_point.x,rect.max_point.x]
                ys = [rect.min_point.y,rect.max_point.y,rect.max_point.y,rect.min_point.y]
                plt.fill(xs,ys,facecolor='none',linewidth=2)

        plt.plot(self.location.x,
                 self.location.y,
                 'bx',markeredgewidth=2)

        plt.plot(poi.x,poi.y,'rx',markeredgewidth=2)

        if isinstance(sampled_landmark.representation, PointRepresentation):
            plt.plot(sampled_landmark.representation.location.x,
                     sampled_landmark.representation.location.y,
                     'r.',markeredgewidth=2)
        elif isinstance(sampled_landmark.representation, LineRepresentation):
            xs = [sampled_landmark.representation.line.start.x,sampled_landmark.representation.line.end.x]
            ys = [sampled_landmark.representation.line.start.y,sampled_landmark.representation.line.end.y]
            plt.fill(xs,ys,facecolor='none',edgecolor='red',linewidth=2)
        elif isinstance(sampled_landmark.representation, RectangleRepresentation):
            rect = sampled_landmark .representation.rect
            xs = [rect.min_point.x,rect.min_point.x,rect.max_point.x,rect.max_point.x]
            ys = [rect.min_point.y,rect.max_point.y,rect.max_point.y,rect.min_point.y]
            plt.fill(xs,ys,facecolor='none',edgecolor='red',linewidth=2)


        # rel_scores = []
        # for relation in relations:
        #     rel_scores.append( relation.probability(poi, sampled_landmark) )
        # rel_scores = array(rel_scores)
        # rel_probabilities = rel_scores/sum(rel_scores)
        # index = rel_probabilities.cumsum().searchsorted( random.sample(1) )[0]
        # sampled_relation = relations[index]

        # toprint = str(poi)+' ; '+sampled_relation.get_description() + " " + sampled_landmark.get_description()
        # print toprint
        # plt.suptitle(toprint)


        # plt.subplot(2,2,2)
        # plt.axis([0,1.5,-0.1,1.1])

        # xs = arange(0,3,0.01)
        # ys = {}
        # for relation in relations:
        #     name = relation.__class__.__name__
        #     plt.plot( xs, relation.distance_probability(xs) )
        # plt.axvline(x=distance,linewidth=2)
        # print distance


        plt.show()

# import sys
# if __name__ == '__main__':
#     if len(sys.argv) > 1:
#         howmany = int(sys.argv[1])
#     else:
#         howmany = 100
#     for i in range(howmany):
#         main()
