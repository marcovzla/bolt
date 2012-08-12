#!/usr/bin/env python
from speaker import Speaker
from planar import Vec2, BoundingBox
from landmark import GroupLineRepresentation, RectangleRepresentation, SurfaceRepresentation, Scene, Landmark
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

    speaker = Speaker(Vec2(5.5,4.5))
    scene = Scene(3)

    table = Landmark('table',
                 RectangleRepresentation(rect=BoundingBox([Vec2(5,5), Vec2(6,7)])),
                 None,
                 Landmark.TABLE)

    obj1 = Landmark('obj1',
                 RectangleRepresentation(rect=BoundingBox([Vec2(5,5), Vec2(5.1,5.1)])),
                 None,
                 Landmark.CUP)

    obj2 = Landmark('obj2',
                 RectangleRepresentation(rect=BoundingBox([Vec2(5.5,6), Vec2(5.6,6.1)])),
                 None,
                 Landmark.BOTTLE)

    obj3 = Landmark('obj3',
                 RectangleRepresentation(rect=BoundingBox([Vec2(4.5,4.5), Vec2(4.8,4.8)])),
                 None,
                 Landmark.CHAIR)

    scene.add_landmark(table)
    scene.add_landmark(obj1)
    scene.add_landmark(obj2)
    # scene.add_landmark(obj3)

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

    perspectives = [ Vec2(5.5,4.5), Vec2(6.5,6.0)]
    #speaker.talk_to_baby(scene, perspectives, how_many_each=10)


    dozen = 12
    couple = 1
    for i in range(couple * dozen):
        location = Vec2(random()+5,random()*2+5)#Vec2(5.68, 5.59)##Vec2(5.3, 5.5)
        # speaker.describe(location, scene, False, 2)
    # location = Vec2(5.68, 5.59)##Vec2(5.3, 5.5)
    # speaker.demo(location, scene)
    # all_desc = speaker.get_all_descriptions(location, scene, 1)


    for i in range(couple * dozen):
        speaker.communicate(scene, False)

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
