from relation import DistanceRelationSet, ContainmentRelationSet, OrientationRelationSet, VeryCloseDistanceRelation
from numpy import array, arange, zeros, log, argmin, set_printoptions, random
from random import choice
from matplotlib import pyplot as plt
from landmark import PointRepresentation, LineRepresentation, GroupLineRepresentation, RectangleRepresentation, Landmark
from planar import Vec2
import sys
from textwrap import wrap
import language_generator
from landmark import Landmark



class Speaker(object):
    def __init__(self, location):
        self.location = location

    def get_head_on_viewpoint(self, landmark):
        axes = landmark.get_primary_axes()
        if len(axes) > 0:
            axis = axes[ argmin([axis.distance_to(self.location) for axis in axes]) ]
            return axis.project(self.location)
        else:
            print "Not getting head on viewpoint!!!"
            return self.location

    def describe(self, trajector, scene, visualize=False, max_level=-1, delimit_chunks=False):

        scenes = scene.get_child_scenes(trajector) + [scene]

        all_landmarks = []

        for s in scenes:
            for scene_lmk in s.landmarks.values():

                # Don't want to use the trajector as landmark
                if scene_lmk == trajector:
                    continue

                all_landmarks.append([s, scene_lmk])

                representations = [scene_lmk.representation]
                representations.extend(scene_lmk.representation.get_alt_representations())

                for representation in representations:
                    for lmk in representation.get_landmarks(max_level):
                        all_landmarks.append([s, lmk])

        sceness, landmarks = zip( *all_landmarks )

        sampled_landmark, sl_prob, sl_ent = self.sample_landmark( landmarks, trajector )
        # print '   ', sampled_landmark, sl_prob, sl_ent

        head_on = self.get_head_on_viewpoint(sampled_landmark)

        self.set_orientations(sampled_landmark, head_on)

        sampled_relation, sr_prob, sr_ent = self.sample_relation( trajector, scene.get_bounding_box(), head_on, sampled_landmark, step=0.1 )
        # print '   ', sampled_relation, sr_prob, sr_ent
        sampled_relation = sampled_relation( head_on, sampled_landmark, trajector )

        description = str(trajector.representation.middle) + '; ' + language_generator.describe(head_on, trajector, sampled_landmark, sampled_relation, delimit_chunks)
        print description

        if visualize: self.visualize(scene, trajector, head_on, sampled_landmark, sampled_relation, description, 0.01)
        return description

    def communicate(self, scene, visualize=False, max_level=-1, delimit_chunks=False):
        all_landmarks = []
        all_relations = []

        for scene_lmk in scene.landmarks.values():
            all_landmarks.append(scene_lmk)

            representations = [scene_lmk.representation]
            representations.extend(scene_lmk.representation.get_alt_representations())

            for representation in representations:
                all_landmarks.extend(representation.get_landmarks(max_level))

        for rset in [DistanceRelationSet,ContainmentRelationSet, OrientationRelationSet]:
            all_relations.extend(rset.relations)

        sampled_landmark = choice(all_landmarks)
        sampled_relation = choice(all_relations)
        perspective = self.get_head_on_viewpoint(sampled_landmark)
        self.set_orientations(sampled_landmark, perspective)

        trajector = self.sample_point_trajector( scene.landmarks['table'].representation.get_geometry().bounding_box,
                                                 sampled_relation,
                                                 perspective,
                                                 sampled_landmark)

        print sampled_landmark, self.get_landmark_probability( sampled_landmark, all_landmarks, trajector )
        print sampled_relation, self.get_relation_probability( sampled_relation, trajector, scene.get_bounding_box(), perspective, sampled_landmark, step=0.1)

        sampled_relation = sampled_relation(perspective, sampled_landmark, trajector)
        description = str(trajector) + '; ' + language_generator.describe(perspective, trajector, sampled_landmark, sampled_relation, delimit_chunks)
        print description

        if visualize: self.visualize(scene, trajector, perspective, sampled_landmark, sampled_relation, description, 0.1)

    def set_orientations(self, landmark, perspective):
        options = set()
        if landmark.parent and landmark.parent.parent_landmark:
            middle_lmk = Landmark('', PointRepresentation(landmark.parent.middle), landmark.parent, None)
            options = OrientationRelationSet.get_applicable_relations(perspective,
                                                                      middle_lmk,
                                                                      Landmark( None,
                                                                                PointRepresentation(landmark.representation.middle),
                                                                                None, None),
                                                                      use_distance=False)

            par_lmk = landmark.parent.parent_landmark
            if par_lmk.parent and par_lmk.parent.parent_landmark:
                par_middle_lmk = Landmark('', PointRepresentation(par_lmk.parent.middle), par_lmk.parent, None)
                trajector = Landmark('', PointRepresentation(par_lmk.representation.middle), None, None)
                par_options = OrientationRelationSet.get_applicable_relations(perspective, par_middle_lmk, trajector, use_distance=False)
            else:
                par_options = []

            options = set(options).difference(set(par_options))
            self.set_orientations(par_lmk, perspective)

        landmark.ori_relations = options

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

        '''
        sampled_landmark = scene.landmarks['table'].representation.landmarks['ll_corner']
        head_on = self.get_head_on_viewpoint(sampled_landmark)
        relset = DistanceRelationSet
        sampled_relation = relset.relations[0](head_on,sampled_landmark,poi)
        print 'distance',sampled_landmark.distance_to(poi)
        print 'probability', sampled_relation.is_applicable()
        description = str(poi) + '; ' + language_generator.describe(head_on, sampled_landmark, sampled_relation)
        print description
        self.visualize(scene, poi, head_on, sampled_landmark, sampled_relation, description, step=0.1)

        sampled_landmark = scene.landmarks['obj2'].representation.landmarks['r_edge']
        head_on = self.get_head_on_viewpoint(sampled_landmark)
        relset = OrientationRelationSet
        sampled_relation = relset.relations[0](head_on,sampled_landmark,poi)
        print 'distance',sampled_landmark.distance_to(poi)
        print 'probability', sampled_relation.is_applicable()
        description = str(poi) + '; ' + language_generator.describe(head_on, sampled_landmark, sampled_relation)
        print description
        self.visualize(scene, poi, head_on, sampled_landmark, sampled_relation, description, step=0.1)
        '''

    # broken!
    def get_all_descriptions(self, poi, scene, max_level=-1):
        '''
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
                        lmk_desc = language_generator.get_landmark_description(head_on, lmk)

                        for relset in [DistanceRelationSet,ContainmentRelationSet, OrientationRelationSet]:

                            for relation in relset.relations: # we have a relation
                                entropy = self.get_entropy(self.get_probabilities(s, relation, head_on, lmk, 0.1)[0])
                                relation = relation(head_on, lmk, poi)
                                applies = relation.is_applicable()

                                if applies:
                                    def create_desc(adverb, prob):
                                        desc = [adverb + rd + ' ' + lmk_desc for rd in language_generator(type(relation))]
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
        '''


    def get_probabilities_box(self, bounding_box, relation, perspective, landmark, step=0.02):
        xs = arange(bounding_box.min_point.x, bounding_box.max_point.x, step)
        ys = arange(bounding_box.min_point.y, bounding_box.max_point.y, step)

        probabilities = zeros( (len(ys), len(xs)) )
        points = zeros( (len(ys), len(xs)), dtype=object )

        for i,x in enumerate(xs):
            for j,y in enumerate(ys):
                p = Landmark( None, PointRepresentation( Vec2(x,y) ), None, None )
                points[j,i] = p
                rel = relation( perspective, landmark, p )
                probabilities[j,i] = rel.is_applicable()

        return probabilities, points

    def get_probabilities_points(self, points, relation, perspective, landmark):
        probabilities = zeros( (len(points)) )
        for i,p in enumerate(points):
            rel = relation( perspective, landmark, p )
            probabilities[i]  = rel.is_applicable()
        return probabilities

    def get_probabilities(self, scene, relation, perspective, landmark, step=0.02):
        scene_bb = scene.get_bounding_box()
        scene_bb = scene_bb.inflate( Vec2(scene_bb.width*0.5,scene_bb.height*0.5) )
        return self.get_probabilities_box(scene_bb, relation, perspective, landmark, step)

    def evaluate_trajector_likelihood(self, trajector, bounding_box, relation, perspective, landmark, step=0.02):
        probs, _ = self.get_probabilities_box(bounding_box, relation, perspective, landmark, step)
        rel = relation( perspective, landmark, trajector )
        trajector_prob = rel.is_applicable()
        return trajector_prob / (probs.sum() + trajector_prob) if trajector_prob else trajector_prob

    def sample_landmark(self, landmarks, trajector):
        ''' Weight by inverse of distance to landmark center and choose probabilistically  '''
        epsilon = 0.000001
        distances = array([trajector.distance_to( PointRepresentation(lmk.representation.middle) ) for lmk in landmarks])
        scores = 1.0/(array(distances)**1.5 + epsilon)
        # scores[distances == 0] = 0
        lm_probabilities = scores/sum(scores)
        index = lm_probabilities.cumsum().searchsorted( random.sample(1) )[0]

        return landmarks[index], lm_probabilities[index], self.get_entropy(lm_probabilities)

    def get_landmark_probability(self, sampled_landmark, landmarks, trajector):
        epsilon = 0.000001
        distances = array([trajector.distance_to( PointRepresentation(lmk.representation.middle) ) for lmk in landmarks])
        scores = 1.0/(array(distances)**1.5 + epsilon)
        # scores[distances == 0] = 0
        lm_probabilities = scores/sum(scores)
        return lm_probabilities[ landmarks.index(sampled_landmark) ], self.get_entropy(lm_probabilities)

    def sample_relation(self, trajector, bounding_box, perspective, landmark, step=0.02):
        """
        Sample a relation given a trajector and landmark.
        Evaluate each relation and probabilisticaly choose the one that is likely to
        generate the trajector given a landmark.
        """
        rel_scores = []
        rel_classes = []

        for s in [DistanceRelationSet, ContainmentRelationSet]:
            for rel in s.relations:
                rel_scores.append(self.evaluate_trajector_likelihood(trajector, bounding_box, rel, perspective, landmark, step))
                rel_classes.append(rel)

        ori_rel_scores = []
        for rel in OrientationRelationSet.relations:
            p = self.evaluate_trajector_likelihood(trajector, bounding_box, rel, perspective, landmark, step)
            if p > 0: ori_rel_scores.append( (p, rel) )

        if len(ori_rel_scores) > 1:
            assert( len(ori_rel_scores) == 2 )

            dists = []
            for p,rel in ori_rel_scores:
                dists.append( [rel(perspective, landmark, trajector).measurement.distance, p, rel] )
            dists = sorted(dists)
            dists[0][1] *= dists[0][0] / dists[1][0]

            rel_scores.append(dists[0][1])
            rel_scores.append(dists[1][1])
            rel_classes.append(dists[0][2])
            rel_classes.append(dists[1][2])

        rel_scores = array(rel_scores)
        rel_probabilities = rel_scores/sum(rel_scores)
        index = rel_probabilities.cumsum().searchsorted( random.sample(1) )[0]

        return rel_classes[index], rel_probabilities[index], self.get_entropy(rel_probabilities)

    def get_relation_probability(self, sampled_relation, trajector, bounding_box, perspective, landmark, step=0.02):
        rel_scores = []
        rel_classes = []

        for s in [DistanceRelationSet, OrientationRelationSet, ContainmentRelationSet]:
            for rel in s.relations:
                rel_scores.append(self.evaluate_trajector_likelihood(trajector, bounding_box, rel, perspective, landmark, step))
                rel_classes.append(rel)

        rel_scores = array(rel_scores)
        set_printoptions(threshold='nan')
        # print 'X',rel_scores
        rel_probabilities = rel_scores/sum(rel_scores)
        return rel_probabilities[ rel_classes.index(sampled_relation) ], self.get_entropy(rel_probabilities)

    def sample_point_trajector(self, bounding_box, relation, perspective, landmark, step=0.02):
        """
        Sample a point of interest given a relation and landmark.
        """
        #points = landmark.representation.sample_points(step=step)
        #probs = self.get_probabilities_points(points, relation, perspective, landmark)
        probs, points = self.get_probabilities_box(bounding_box, relation, perspective, landmark)
        probs /= probs.sum()
        index = probs.cumsum().searchsorted( random.sample(1) )[0]
        return Landmark( 'point', points.flatten()[index], None, Landmark.POINT )

    def get_entropy(self, probabilities):
        probabilities += 1e-15
        probabilities = probabilities/sum(probabilities.flatten())
        return -sum( (probabilities * log(probabilities)).flatten() )

    def visualize(self, scene, trajector, head_on, sampled_landmark, sampled_relation, description, step=0.02):

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
                rel = relation( head_on, sampled_landmark, Landmark('', PointRepresentation(Vec2(x,y)), None, None) )
                if hasattr(rel, 'measurement'):
                    rel.measurement.best_degree_class = sampled_relation.measurement.best_degree_class
                    rel.measurement.best_distance_class = sampled_relation.measurement.best_distance_class
                probabilities[j,i] = rel.is_applicable()
                # print rel.distance, probabilities[j,i]

        set_printoptions(threshold='nan')
        #print probabilities

        x = array( [list(xs-step*0.5)]*len(ys) )
        y = array( [list(ys-step*0.5)]*len(xs) ).T

        #print self.get_entropy(probabilities)
        plt.pcolor(x, y, probabilities, cmap = 'jet', edgecolors='none', alpha=0.7)
        plt.colorbar()

        for lmk in scene.landmarks.values():
            if isinstance(lmk.representation, GroupLineRepresentation):
                xs = [lmk.representation.line.start.x, lmk.representation.line.end.x]
                ys = [lmk.representation.line.start.y, lmk.representation.line.end.y]
                plt.fill(xs,ys,facecolor='none',linewidth=2)
            elif isinstance(lmk.representation, RectangleRepresentation):
                rect = lmk.representation.rect
                xs = [rect.min_point.x,rect.min_point.x,rect.max_point.x,rect.max_point.x]
                ys = [rect.min_point.y,rect.max_point.y,rect.max_point.y,rect.min_point.y]
                plt.fill(xs,ys,facecolor='none',linewidth=2)
                plt.text(rect.min_point.x+0.01,rect.max_point.y+0.02,lmk.name)

        plt.plot(self.location.x,
                 self.location.y,
                 'bx',markeredgewidth=2)

        traj_rep = trajector.representation
        if isinstance(traj_rep, GroupLineRepresentation):
            xs = [traj_rep.line.start.x, traj_rep.line.end.x]
            ys = [traj_rep.line.start.y, traj_rep.line.end.y]
            plt.fill(xs,ys,facecolor='none',linewidth=2)
        elif isinstance(traj_rep, RectangleRepresentation):
            rect = traj_rep.rect
            xs = [rect.min_point.x,rect.min_point.x,rect.max_point.x,rect.max_point.x]
            ys = [rect.min_point.y,rect.max_point.y,rect.max_point.y,rect.min_point.y]
            plt.fill(xs,ys,facecolor='none',linewidth=2)
        elif isinstance(traj_rep, PointRepresentation):
            plt.plot(traj_rep.location.x, traj_rep.location.y, 'bo', markeredgewidth=2)

        plt.text(traj_rep.middle.x+0.01,
                 traj_rep.middle.y+0.02,'trajector')

        '''
        plt.plot(poi.x,poi.y,'rx',markeredgewidth=2)
        plt.text(poi.x+0.01,
                 poi.y+0.02,'POI')
        '''

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
