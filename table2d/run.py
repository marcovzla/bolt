#!/usr/bin/env python
from speaker import Speaker
from planar import Vec2, BoundingBox
from landmark import (GroupLineRepresentation,
                      PointRepresentation,
                      RectangleRepresentation,
                      Circle,
                      CircleRepresentation,
                      SurfaceRepresentation,
                      Scene,
                      Landmark,
                      ObjectClass,
                      Color)
from random import random
import pickle
import adapter

if __name__ == '__main__':
    # poi = Vec2(float(sys.argv[1]), 0)
    # l = LineRepresentation()

    # f = l.get_line_features(poi)

    # print 'dist_start = {dist_start}, dist_end = {dist_end}, dist_mid = {dist_mid}'.format(**f)
    # print 'dir_start = {dir_start}, dir_end = {dir_end}, dir_mid = {dir_mid}'.format(**f)

    # print 'Distance from POI to Start landmark is %f' % l.landmarks['start'].distance_to(poi)
    # print 'Distance from POI to End landmark is %f' % l.landmarks['end'].distance_to(poi)
    # print 'Distance from POI to Mid landmark is %f' % l.landmarks['mid'].distance_to(poi)
    # cups 7 cm in diameter
    # triangles are 6 by 10 cm

    speaker = Speaker(Vec2(0,0))
    scene = Scene(3)

    table = Landmark('table',
                     RectangleRepresentation(rect=BoundingBox([Vec2(-0.4,0.4), Vec2(0.4,1.0)])),
                     None,
                     ObjectClass.TABLE)

    obj1 = Landmark('green_cup',
                    RectangleRepresentation(rect=BoundingBox([Vec2(0.05-0.035,0.9-0.035), Vec2(0.05+0.035,0.9+0.035)]), landmarks_to_get=[]),
                    None,
                    ObjectClass.CUP,
                    Color.GREEN)

    obj2 = Landmark('blue_cup',
                    RectangleRepresentation(rect=BoundingBox([Vec2(0.05-0.035,0.7-0.035), Vec2(0.05+0.035,0.7+0.035)]), landmarks_to_get=[]),
                    None,
                    ObjectClass.CUP,
                    Color.BLUE)

    obj3 = Landmark('pink_cup',
                    RectangleRepresentation(rect=BoundingBox([Vec2(0-0.035,0.55-0.035), Vec2(0+0.035,0.55+0.035)]), landmarks_to_get=[]),
                    None,
                    ObjectClass.CUP,
                    Color.PINK)

    obj4 = Landmark('purple_prism',
                    RectangleRepresentation(rect=BoundingBox([Vec2(-0.3-0.03,0.7-0.05), Vec2(-0.3+0.03,0.7+0.05)]), landmarks_to_get=[]),
                    None,
                    ObjectClass.PRISM,
                    Color.PURPLE)

    obj5 = Landmark('orange_prism',
                    RectangleRepresentation(rect=BoundingBox([Vec2(0.3-0.03,0.7-0.05), Vec2(0.3+0.03,0.7+0.05)]), landmarks_to_get=[]),
                    None,
                    ObjectClass.PRISM,
                    Color.ORANGE)

    scene.add_landmark(table)

    for obj in (obj1, obj2, obj3, obj4, obj5):
        obj.representation.alt_representations = []
        scene.add_landmark(obj)

    # groups = adapter.adapt(scene)

    # for i,g in enumerate(groups):
    #     if (len(g) > 1):
    #         scene.add_landmark(Landmark('ol%d'%i, ObjectLineRepresentation(g), None, Landmark.LINE))

    # f = open('scene.pickle','wb')
    # pickle.dump(scene,f)
    # f.flush()
    # f.close()
    # del scene
    # f = open('scene.pickle','rb')
    # scene = pickle.load(f)

    #perspectives = [ Vec2(5.5,4.5), Vec2(6.5,6.0)]
    #speaker.talk_to_baby(scene, perspectives, how_many_each=10)


    dozen = 5000
    couple = 2
    for i in range(couple * dozen):
        location = Landmark( 'point', PointRepresentation(Vec2(random()*0.8-0.4,random()*0.6+0.4)), None, Landmark.POINT)
        trajector = location#obj2
        speaker.describe(trajector, scene, False, 1)
    # location = Vec2(5.68, 5.59)##Vec2(5.3, 5.5)
    # speaker.demo(location, scene)
    # all_desc = speaker.get_all_descriptions(location, scene, 1)


    # for i in range(couple * dozen):
    #     speaker.communicate(scene, False)

    # for desc in all_desc:
    #     print desc

    # r = RectangleRepresentation(['table'])
    # lmk = r.landmarks['l_edge']
    # print lmk.get_description()
    # print lmk.representation.landmarks['end'].get_description()
    # print r.landmarks['ul_corner'].get_description()

    # print r.landmarks['ul_corner'].distance_to( Vec2(0,0) )

    # representations = [r]
    # representations.extend(r.get_alt_representations())

    # location = Vec2(0,0)
    # landmarks_distances = []
    # for representation in representations:
    #     for lmk in representation.get_landmarks():
    #         landmarks_distances.append([lmk, lmk.distance_to(location)])

    # print 'Distance from POI to LLCorner landmark is %f' % r.landmarks['ll_corner'].distance_to(poi)
    # print 'Distance from POI to URCorner landmark is %f' % r.landmarks['ur_corner'].distance_to(poi)
    # print 'Distance from POI to LRCorner landmark is %f' % r.landmarks['lr_corner'].distance_to(poi)
    # print 'Distance from POI to ULCorner landmark is %f' % r.landmarks['ul_corner'].distance_to(poi)
    # print 'Distance from POI to Center landmark is %f' % r.landmarks['center'].distance_to(poi)
    # print 'Distance from POI to LEdge landmark is %f' % r.landmarks['l_edge'].distance_to(poi)
    # print 'Distance from POI to REdge landmark is %f' % r.landmarks['r_edge'].distance_to(poi)
    # print 'Distance from POI to NEdge landmark is %f' % r.landmarks['n_edge'].distance_to(poi)
    # print 'Distance from POI to FEdge landmark is %f' % r.landmarks['f_edge'].distance_to(poi)
