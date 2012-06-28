from relations import DistanceRelationSet, ContainmentRelationSet
from numpy import array, random, arange, zeros, indices
from random import choice
from matplotlib import pyplot as plt
from landmark import PointRepresentation, LineRepresentation, RectangleRepresentation
from planar import Vec2, BoundingBox

class Speaker(object):
    def __init__(self, location):
        self.location = location

    def describe(self, poi, scene):
        scenes = scene.get_child_scenes(poi) + [scene]
        print str(len(scenes)) + str(scenes)

        landmarks_distances = []

        for s in scenes:
            for scene_lmk in s.landmarks.values():
                landmarks_distances.append([s, scene_lmk])

                representations = [scene_lmk.representation]
                representations.extend(scene_lmk.representation.get_alt_representations())

                for representation in representations:
                    for lmk in representation.get_landmarks():
                        landmarks_distances.append([s, lmk])

        sceness, landmarks= zip( *landmarks_distances )
        # for ld in landmarks_distances:
        #     print ld

        relset = choice([DistanceRelationSet,ContainmentRelationSet])()
        index = relset.sample_landmark(landmarks, poi)
       
        sampled_scene = sceness[index]
        sampled_landmark = landmarks[index]

        
        sampled_relation = relset.sample_relation(sampled_landmark, poi)

        description = str(poi) + '; ' + sampled_relation.get_description() + " " + sampled_landmark.get_description(self.location)
        print description
        self.visualize(sampled_scene, poi, sampled_landmark, sampled_relation, description)


    def visualize(self, scene, poi, sampled_landmark, sampled_relation, description):

        plt.figure( figsize=(10,5) )
        plt.subplot(1,2,1)
        scene_bb = scene.get_bounding_box()
        scene_bb = scene_bb.inflate( Vec2(scene_bb.width*0.5,scene_bb.height*0.5) )
        plt.axis([scene_bb.min_point.x, scene_bb.max_point.x, scene_bb.min_point.y, scene_bb.max_point.y])

        step = 0.02
        xs = arange(scene_bb.min_point.x, scene_bb.max_point.x, step)
        ys = arange(scene_bb.min_point.y, scene_bb.max_point.y, step)

        probabilities = zeros(  ( len(ys),len(xs) )  )
        for i,x in enumerate(xs):
            for j,y in enumerate(ys):
                probabilities[j,i] = sampled_relation.probability( Vec2(x,y), sampled_landmark )

        x = array( [list(xs-step*0.5)]*len(ys) )
        y = array( [list(ys-step*0.5)]*len(xs) ).T

        plt.pcolor(x, y, probabilities, cmap = 'jet', edgecolors='none', alpha=0.7)

        print 'drawing scene ', len(scene.landmarks)
        for lmk in scene.landmarks.values():
            print 'drawing ', lmk.name
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
        plt.suptitle(description)


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
