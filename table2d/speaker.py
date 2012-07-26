from relation import DistanceRelationSet, ContainmentRelationSet, OrientationRelationSet, VeryCloseDistanceRelation
from numpy import array, random, arange, zeros, indices, log, argmin, set_printoptions
from random import choice
from matplotlib import pyplot as plt
from landmark import PointRepresentation, LineRepresentation, RectangleRepresentation
from planar import Vec2, BoundingBox
import sys
from textwrap import wrap
import language_generator

class Speaker(object):
    def __init__(self, location):
        self.location = location

    def get_head_on_viewpoint(self, landmark):
        axes = landmark.get_primary_axes()
        axis = axes[ argmin([axis.distance_to(self.location) for axis in axes]) ]
        head_on = axis.project(self.location)
        return head_on

    def describe(self, poi, scene, visualize=False, max_level=-1):
        scenes = scene.get_child_scenes(poi) + [scene]

        all_landmarks = []

        for s in scenes:
            for scene_lmk in s.landmarks.values():
                all_landmarks.append([s, scene_lmk])

                representations = [scene_lmk.representation]
                representations.extend(scene_lmk.representation.get_alt_representations())

                for representation in representations:
                    for lmk in representation.get_landmarks(max_level):
                        all_landmarks.append([s, lmk])

        sceness, landmarks = zip( *all_landmarks )
        # for ld in all_landmarks:
        #     print ld


        relset = choice([DistanceRelationSet,ContainmentRelationSet, OrientationRelationSet])()
        index = relset.sample_landmark(landmarks, poi)

        sampled_scene = sceness[index]
        sampled_landmark = landmarks[index]
        head_on = self.get_head_on_viewpoint(sampled_landmark)
        sampled_relation = relset.sample_relation(head_on, sampled_landmark, poi)

        # sampled_landmark = sampled_scene.landmarks['obj2'].representation.landmarks['ul_corner']
        # relset = DistanceRelationSet()
        # sampled_relation = relset.relations[10]
        # print 'distance',sampled_landmark.distance_to(poi)
        # print 'probability', sampled_relation.probability(poi,sampled_landmark)


        description = str(poi) + '; ' + sampled_relation.get_description() + " " + sampled_landmark.get_description(head_on)
        print 'OLD: ' + description

        print 'NEW: ' + str(poi) + '; ' + language_generator.describe(head_on, sampled_landmark, sampled_relation)

        if visualize: self.visualize(sampled_scene, poi, head_on, sampled_landmark, type(sampled_relation), description)

    def talk_to_baby(self, scene, perspectives, how_many_each=10000):

        max_recurse_level = 4
        for recurse_level in range(max_recurse_level):
            for i in range(how_many_each):
                perspective = choice(perspectives)
                self.location = perspective
                lmk = choice(scene.landmarks.values())
                level = 0
                while level < recurse_level:
                    representations = [lmk.representation]+lmk.representation.get_alt_representations()
                    landmarks = []
                    for representation in representations:
                        landmarks.extend( representation.landmarks.values() )
                    if len(landmarks) == 0:
                        break
                    lmk = choice(landmarks)
                    level += 1
                head_on = self.get_head_on_viewpoint(lmk)
                print perspective, lmk.uuid, lmk.get_description(head_on)

    def demo(self, poi, scene):

        # Sentence 1
        # [0.25562221863528939, 1.0, 3.9120230054287899, Scene(3), table, <landmark.RectangleRepresentation>,
        #    m_surf, <relations.on object at 0x35cb350>, ['on the middle of the table']]
        '''
        sampled_landmark = scene.landmarks['table'].representation.landmarks['m_surf']
        relset = ContainmentRelationSet()
        sampled_relation = relset.relations[0]
        print 'distance',sampled_landmark.distance_to(poi)
        print 'probability', sampled_relation.probability(poi,sampled_landmark)
        head_on = self.get_head_on_viewpoint(sampled_landmark)
        description = str(poi) + '; ' + sampled_relation.get_description() + " " + sampled_landmark.get_description(head_on)
        print description
        self.visualize(scene, poi, head_on, sampled_landmark, sampled_relation, description)

        # Sentence 2
        # [0.21714724095161927, 1.0, 4.6051701859882321, Scene(3,), table, <landmark.RectangleRepresentation>,
        #    n_surf, <relations.on object at 0x35a4910>, ['on the near half of the table']]

        sampled_landmark = scene.landmarks['table'].representation.landmarks['n_surf']
        relset = ContainmentRelationSet()
        sampled_relation = relset.relations[0]
        print 'distance',sampled_landmark.distance_to(poi)
        print 'probability', sampled_relation.probability(poi,sampled_landmark)
        head_on = self.get_head_on_viewpoint(sampled_landmark)
        description = str(poi) + '; ' + sampled_relation.get_description() + " " + sampled_landmark.get_description(head_on)
        print description
        self.visualize(scene, poi, head_on, sampled_landmark, sampled_relation, description)

        # [0.21382721267862911, 0.99950034539156474, 4.6743365022194832, Scene(3), obj2, <landmark.RectangleRepresentation>,
        #    obj2, <relations.not_is_not_adjacent object at 0x3e42e10>, ['not very far from the bottle', 'not quite far from the bottle', 'not really far from the bottle']]

        sampled_landmark = scene.landmarks['obj2']
        relset = DistanceRelationSet()
        sampled_relation = relset.relations[11]
        print 'distance',sampled_landmark.distance_to(poi)
        print 'probability', sampled_relation.probability(poi,sampled_landmark)
        head_on = self.get_head_on_viewpoint(sampled_landmark)
        description = str(poi) + '; ' + sampled_relation.get_description() + " " + sampled_landmark.get_description(head_on)
        print description
        self.visualize(scene, poi, head_on, sampled_landmark, sampled_relation, description)

        # [0.18873916581775263, 1.0, 5.2983173665480985, Scene(3), table, <landmark.RectangleRepresentation>,
        #    table, <relations.on object at 0x37f1710>, ['on the table']]

        sampled_landmark = scene.landmarks['table']
        relset = ContainmentRelationSet()
        sampled_relation = relset.relations[0]
        print 'distance',sampled_landmark.distance_to(poi)
        print 'probability', sampled_relation.probability(poi,sampled_landmark)
        head_on = self.get_head_on_viewpoint(sampled_landmark)
        description = str(poi) + '; ' + sampled_relation.get_description() + " " + sampled_landmark.get_description(head_on)
        print description
        self.visualize(scene, poi, head_on, sampled_landmark, sampled_relation, description)

        # [0.21978422782979082, 0.99950034539156474, 4.5476436378574689, Scene(3), obj2, <landmark.RectangleRepresentation>,
        #    lr_corner, <relations.not_is_not_adjacent object at 0x3e18a50>, ['not very far from the near corner of the right half of the bottle', 'not quite far from the near corner of the right half of the bottle', 'not really far from the near corner of the right half of the bottle']]

        sampled_landmark = scene.landmarks['obj2'].representation.landmarks['r_surf'].representation.landmarks['lr_corner']
        relset = DistanceRelationSet()
        sampled_relation = relset.relations[11]
        print 'distance',sampled_landmark.distance_to(poi)
        print 'probability', sampled_relation.probability(poi,sampled_landmark)
        head_on = self.get_head_on_viewpoint(sampled_landmark)
        description = str(poi) + '; ' + sampled_relation.get_description() + " " + sampled_landmark.get_description(head_on)
        print description
        self.visualize(scene, poi, head_on, sampled_landmark, sampled_relation, description)
        '''

        sampled_landmark = scene.landmarks['table'].representation.landmarks['ll_corner']
        head_on = self.get_head_on_viewpoint(sampled_landmark)
        relset = DistanceRelationSet()
        sampled_relation = relset.relations[0](head_on,sampled_landmark,poi)
        print 'distance',sampled_landmark.distance_to(poi)
        print 'probability', sampled_relation.is_applicable()
        description = str(poi) + '; ' + sampled_relation.get_description() + " " + sampled_landmark.get_description(head_on)
        print description
        self.visualize(scene, poi, head_on, sampled_landmark, sampled_relation, description, step=0.1)

        sampled_landmark = scene.landmarks['table'].representation.landmarks['ll_corner']
        head_on = self.get_head_on_viewpoint(sampled_landmark)
        relset = OrientationRelationSet()
        sampled_relation = relset.relations[0](head_on,sampled_landmark,poi)
        print 'distance',sampled_landmark.distance_to(poi)
        print 'probability', sampled_relation.is_applicable()
        description = str(poi) + '; ' + sampled_relation.get_description() + " " + sampled_landmark.get_description(head_on)
        print description
        self.visualize(scene, poi, head_on, sampled_landmark, sampled_relation, description, step=0.1)


    def get_all_descriptions(self, poi, scene, max_level=-1):
        all_desc = []
        scenes = scene.get_child_scenes(poi) + [scene]
        counter = 0
        for s in scenes:
            for scene_lmk in s.landmarks.values():
                representations = [scene_lmk.representation]
                representations.extend(scene_lmk.representation.get_alt_representations())

                for representation in representations:
                    for lmk in representation.get_landmarks(max_level)+[scene_lmk]: # we have a leaf landmark at current level
                        head_on = self.get_head_on_viewpoint(lmk)
                        lmk_desc = lmk.get_description(head_on)

                        for relset_f in [DistanceRelationSet,ContainmentRelationSet, OrientationRelationSet]:
                            relset = relset_f()

                            for relation in relset.relations: # we have a relation
                                entropy = self.get_entropy(self.get_probabilities(s, relation, head_on, lmk, 0.1))
                                relation = relation(head_on, lmk, poi)
                                applies = relation.is_applicable()

                                if applies:
                                    def create_desc(adverb, prob):
                                        desc = [adverb + rd + ' ' + lmk_desc for rd in relation.words]
                                        score = prob*applies / entropy
                                        all_desc.append( [score, prob, entropy, s, scene_lmk, representation, lmk, relation, desc] )
                                        sys.stderr.write('[%d] %f, %f, %f\n' % (counter, score, prob, entropy))
                                        sys.stderr.flush()

                                    if hasattr(relation, 'measurement') and not isinstance(relation, VeryCloseDistanceRelation):
                                        m_probs = relation.measurement.evaluate_all(relation.distance)

                                        for prob,adverb in m_probs:
                                            create_desc(adverb + ' ', prob)
                                            counter += 1
                                    else:
                                        create_desc('', 1.0)
                                        counter += 1


        return reversed(sorted(all_desc))

    def get_probabilities(self, scene, relation, perspective, landmark, step=0.02):
        scene_bb = scene.get_bounding_box()
        scene_bb = scene_bb.inflate( Vec2(scene_bb.width*0.5,scene_bb.height*0.5) )

        xs = arange(scene_bb.min_point.x, scene_bb.max_point.x, step)
        ys = arange(scene_bb.min_point.y, scene_bb.max_point.y, step)

        probabilities = zeros(  ( len(ys),len(xs) )  )
        for i,x in enumerate(xs):
            for j,y in enumerate(ys):
                rel = relation( perspective, landmark, Vec2(x,y) )
                probabilities[j,i] = rel.is_applicable()

        return probabilities


    def get_entropy(self, probabilities):
        probabilities += 1e-15
        probabilities = probabilities/sum(probabilities.flatten())
        return sum( (probabilities * log( 1./probabilities)).flatten() )

    def visualize(self, scene, poi, head_on, sampled_landmark, sampled_relation, description, step=0.02):

        relation = type(sampled_relation)

        plt.figure( figsize=(6,8) )
        #plt.subplot(1,2,1)
        scene_bb = scene.get_bounding_box()
        scene_bb = scene_bb.inflate( Vec2(scene_bb.width*0.5,scene_bb.height*0.5) )
        plt.axis([scene_bb.min_point.x, scene_bb.max_point.x, scene_bb.min_point.y, scene_bb.max_point.y])


        xs = arange(scene_bb.min_point.x, scene_bb.max_point.x, step)
        ys = arange(scene_bb.min_point.y, scene_bb.max_point.y, step)

        probabilities = zeros(  ( len(ys),len(xs) )  )
        for i,x in enumerate(xs):
            for j,y in enumerate(ys):
                rel = relation( head_on, sampled_landmark, Vec2(x,y) )
                rel.measurement.degree = sampled_relation.measurement.degree
                rel.measurement.word = sampled_relation.measurement.word
                probabilities[j,i] = rel.is_applicable()
                # print rel.distance, probabilities[j,i]

        set_printoptions(threshold='nan')
        #print probabilities

        x = array( [list(xs-step*0.5)]*len(ys) )
        y = array( [list(ys-step*0.5)]*len(xs) ).T

        print self.get_entropy(probabilities)
        plt.pcolor(x, y, probabilities, cmap = 'jet', edgecolors='none', alpha=0.7)
        plt.colorbar()

        for lmk in scene.landmarks.values():
            if isinstance(lmk.representation, RectangleRepresentation):
                rect = lmk.representation.rect
                xs = [rect.min_point.x,rect.min_point.x,rect.max_point.x,rect.max_point.x]
                ys = [rect.min_point.y,rect.max_point.y,rect.max_point.y,rect.min_point.y]
                plt.fill(xs,ys,facecolor='none',linewidth=2)
                plt.text(rect.min_point.x+0.01,rect.max_point.y+0.02,lmk.descriptions[0])

        plt.plot(self.location.x,
                 self.location.y,
                 'bx',markeredgewidth=2)

        plt.plot(poi.x,poi.y,'rx',markeredgewidth=2)
        plt.text(poi.x+0.01,
                 poi.y+0.02,'POI')

        plt.plot(head_on.x,head_on.y,'ro',markeredgewidth=2)
        plt.text(head_on.x+0.02,head_on.y+0.01,'perspective')

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
        title = "Probability of location given description:\n" + description
        plt.suptitle('\n'.join(wrap(title,50)))


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
