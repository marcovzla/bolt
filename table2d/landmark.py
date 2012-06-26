#!/usr/bin/env python

import sys
from planar import Vec2
from planar import BoundingBox
from planar.line import LineSegment
from planar.line import Line
from random import choice
from speaker import Speaker


class Landmark(object):
    def __init__(self, name, representation, parent, descriptions):
        self.name = name
        self.representation = representation
        self.parent = parent
        self.descriptions = descriptions

    def __repr__(self):
        return self.get_description()

    def distance_to(self, point):
        if self.parent: point = self.parent.project_point(point)
        return self.representation.distance_to(point)

    def get_description(self):
        desc = 'the ' + choice(self.descriptions)

        if self.parent:
            p_desc = self.parent.get_description()
            if p_desc:
                desc += ' of ' + p_desc

        return desc


class AbstractRepresentation(object):
    def __init__(self, descriptions=['']):
        self.alt_representations = []
        self.parent_landmark = None
        self.descriptions = descriptions
        self.landmarks = {}

    def get_alt_representations(self):
        result = self.alt_representations

        for al in self.alt_representations:
            result.extend(al.get_alt_representations())

        return result

    def project_point(self, point):
        if self.parent_landmark is None:
            return self.my_project_point(point)
        else:
            return self.parent_landmark.parent.project_point(point)

    def my_project_point(self, point):
        raise NotImplementedError

    def distance_to(self, point):
        raise NotImplementedError

    def get_description(self):
        if self.parent_landmark:
            return self.parent_landmark.get_description()

        return 'the ' + choice(self.descriptions)

    def get_landmarks(self):
        result = self.landmarks.values()

        for landmark in self.landmarks.values():
            result.extend( landmark.representation.get_landmarks() )

        return result


class PointRepresentation(AbstractRepresentation):
    def __init__(self, point, descriptions=['point']):
        super(PointRepresentation, self).__init__(descriptions)
        self.location = point
        self.alt_representations = []
        self.landmarks = {}

    def my_project_point(self, point):
        return Vec2(self.location.x, self.location.y)

    def distance_to(self, point):
        return self.location.distance_to(point)


class LineRepresentation(AbstractRepresentation):
    def __init__(self, orientation='height', line=LineSegment.from_points([Vec2(0, 0), Vec2(1, 0)]), descriptions=['line']):
        super(LineRepresentation, self).__init__(descriptions)
        self.line = line
        self.alt_representations = [PointRepresentation(self.line.mid, descriptions)]
        words = [['near end','this end','my end'], ['middle','center'], ['far end','that end','other end']] if orientation == 'height' \
           else [['left side'], ['middle','center'], ['right side']]

        self.landmarks = \
            {
                'start': Landmark('start', PointRepresentation(self.line.start), self, words[0]),
                'end':   Landmark('end',   PointRepresentation(self.line.end),   self, words[2]),
                'mid':   Landmark('mid',   PointRepresentation(self.line.mid),   self, words[1]),
            }

        for lmk in self.landmarks.values():
            lmk.representation.parent_landmark = lmk

    def my_project_point(self, point):
        return self.line.line.project(point)

    def distance_to(self, point):
        return self.line.distance_to(point)


class RectangleRepresentation(AbstractRepresentation):
    def __init__(self, rect=BoundingBox([Vec2(0, 0), Vec2(1, 2)]), descriptions=['rectangle']):
        super(RectangleRepresentation, self).__init__(descriptions)

        # creates an elongated rectangle pointing upwards
        self.rect = rect
        self.alt_representations = [LineRepresentation('width',
                                                        LineSegment.from_points([Vec2(self.rect.min_point.x, self.rect.center.y),
                                                                                 Vec2(self.rect.max_point.x, self.rect.center.y)]),
                                                        descriptions),
                                    LineRepresentation('height',
                                                        LineSegment.from_points([Vec2(self.rect.center.x, self.rect.min_point.y),
                                                                                 Vec2(self.rect.center.x, self.rect.max_point.y)]),
                                                        descriptions)]
        lrc = Vec2(self.rect.min_point.x + self.rect.width, self.rect.min_point.y)
        ulc = Vec2(self.rect.max_point.x - self.rect.width, self.rect.max_point.y)

        self.landmarks = \
            {
                'll_corner': Landmark('ll_corner', PointRepresentation(self.rect.min_point), self, ['lower left corner']),
                'ur_corner': Landmark('ur_corner', PointRepresentation(self.rect.max_point), self, ['upper right corner']),
                'lr_corner': Landmark('lr_corner', PointRepresentation(lrc), self, ['lower right corner']),
                'ul_corner': Landmark('ul_corner', PointRepresentation(ulc), self, ['upper left corner']),
                'center':    Landmark('center',    PointRepresentation(self.rect.center), self, ['center']),
                'l_edge':    Landmark('l_edge',    LineRepresentation('height', LineSegment.from_points([self.rect.min_point, ulc])), self, ['left edge']),
                'r_edge':    Landmark('r_edge',    LineRepresentation('height', LineSegment.from_points([lrc, self.rect.max_point])), self, ['right edge']),
                'n_edge':    Landmark('n_edge',    LineRepresentation('width', LineSegment.from_points([self.rect.min_point, lrc])), self, ['near edge']),
                'f_edge':    Landmark('f_edge',    LineRepresentation('width', LineSegment.from_points([ulc, self.rect.max_point])), self, ['far edge']),
            }

        for lmk in self.landmarks.values():
            lmk.representation.parent_landmark = lmk

    def my_project_point(self, point):
        return point

    def distance_to(self, point):
        return min([lmk.representation.distance_to(point) for lmk in self.landmarks.values()])



class Scene(object):
    def __init__(self):
        self.landmarks = {}

    def add_landmark(self, lmk):
        self.landmarks[lmk.name] = lmk

    def set_viewer_location(self, point):
        self.view_loc = point


if __name__ == '__main__':
        # poi = Vec2(float(sys.argv[1]), 0)
        # l = LineRepresentation()

        # f = l.get_line_features(poi)

        # print 'dist_start = {dist_start}, dist_end = {dist_end}, dist_mid = {dist_mid}'.format(**f)
        # print 'dir_start = {dir_start}, dir_end = {dir_end}, dir_mid = {dir_mid}'.format(**f)

        # print 'Distance from POI to Start landmark is %f' % l.landmarks['start'].distance_to(poi)
        # print 'Distance from POI to End landmark is %f' % l.landmarks['end'].distance_to(poi)
        # print 'Distance from POI to Mid landmark is %f' % l.landmarks['mid'].distance_to(poi)

        speaker = Speaker(Vec2(5.5,5))
        scene = Scene()

        table = Landmark('table',
                         RectangleRepresentation(rect=BoundingBox([Vec2(5,5), Vec2(6,7)]), descriptions=['table', 'table surface']),
                         None,
                         ['table', 'table surface'])

        obj1 = Landmark('obj1',
                         RectangleRepresentation(rect=BoundingBox([Vec2(5,5), Vec2(5.1,5.1)])),
                         None,
                         ['cup', 'blue cup'])

        obj2 = Landmark('obj2',
                         RectangleRepresentation(rect=BoundingBox([Vec2(5.5,6), Vec2(5.6,6.1)])),
                         None,
                         ['bottle'])

        scene.add_landmark(table)
        scene.add_landmark(obj1)
        scene.add_landmark(obj2)

        location = Vec2(5.3, 5.5)
        speaker.describe(location, scene)

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
