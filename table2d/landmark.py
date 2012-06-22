#!/usr/bin/env python

import sys
from planar import Vec2
from planar import BoundingBox
from planar.line import LineSegment
from planar.line import Line

class Landmark(object):
    def __init__(self, name, words, data, parent):
        # if we want to create a Point type landmark
        if isinstance(data, Vec2):
            self.type_str = 'PointLandmark'
        # if we are creating a Line type landmark
        elif isinstance(data, LineSegment):
            self.type_str = 'LineLandmark'

        self.name_str = name
        self.type = data
        self.parent = parent
        self.words = words

    def __str__(self):
        return '%s %s %s' % (self.type_str, self.words, self.type)

    def __repr__(self):
        return self.__str__()

    def distance_to(self, point):
        return self.type.distance_to(point)

    def get_description(self):
        return 'the ' + self.words


class LineRepresentation(object):
    def __init__(self, orientation='height', line=LineSegment.from_points([Vec2(0, 0), Vec2(1, 0)])):
        self.line = line
        words = ['near end', 'middle', 'far end'] if orientation == 'height' else ['left side', 'middle', 'right side']
        self.landmarks = \
            {
                'start': Landmark('start', words[0], self.line.start, self),
                'end':   Landmark('end',   words[2], self.line.end, self),
                'mid':   Landmark('mid',   words[1], self.line.mid, self)
            }

    def project_point(self, point):
        return self.line.line.project(point)

    def distance_to_landmarks(self, point):
        projected = self.line.line.project(point)
        result = []

        for name, obj in self.landmarks.items():
            result.append( (obj, obj.distance_to(projected)) )

        return result

    def distance_to_start(self, point):
        return self.landmarks['start'].distance_to(point)

    def distance_to_end(self, point):
        return self.landmarks['end'].distance_to(point)

    def distance_to_mid(self, point):
        return self.landmarks['mid'].distance_to(point)

    def get_line_features(self, poi):
        dist_start = poi.distance_to(self.landmarks['start'].type)
        dist_end = poi.distance_to(self.landmarks['end'].type)
        dist_mid = poi.distance_to(self.landmarks['mid'].type)

        tl = Line.from_normal(self.line.direction, self.landmarks['start'].type.x)
        dir_start = -1 if tl.point_left(poi) else 1

        tl = Line.from_normal(self.line.direction, self.landmarks['end'].type.x)
        dir_end = -1 if tl.point_left(poi) else 1

        tl = Line.from_normal(self.line.direction, self.landmarks['mid'].type.x)
        dir_mid = -1 if tl.point_left(poi) else 1

        return {
                'dist_start': dist_start,
                'dist_mid': dist_mid,
                'dist_end': dist_end,
                'dir_start': dir_start,
                'dir_mid': dir_mid,
                'dir_end': dir_end,
               }

class RectangleRepresentation(object):
    def __init__(self):
        # creates an elongated rectangle pointing upwards
        self.rect = BoundingBox([Vec2(0, 0), Vec2(1, 2)])

        lrc = Vec2(self.rect.min_point.x + self.rect.width, self.rect.min_point.y)
        ulc = Vec2(self.rect.max_point.x - self.rect.width, self.rect.max_point.y)

        self.landmarks = \
            {
                'll_corner': Landmark('ll_corner', 'lower left corner',  self.rect.min_point, self),
                'ur_corner': Landmark('ur_corner', 'upper right corner', self.rect.max_point, self),
                'lr_corner': Landmark('lr_corner', 'lower right corner', lrc, self),
                'ul_corner': Landmark('ul_corner', 'upper left corner',  ulc, self),
                'center':    Landmark('center',    'center',             self.rect.center, self),
                'l_edge':    Landmark('l_edge',    'left edge',          LineSegment.from_points([self.rect.min_point, ulc]), self),
                'r_edge':    Landmark('r_edge',    'right edge',         LineSegment.from_points([lrc, self.rect.max_point]), self),
                'n_edge':    Landmark('n_edge',    'near edge',          LineSegment.from_points([self.rect.min_point, lrc]), self),
                'f_edge':    Landmark('f_edge',    'far edge',           LineSegment.from_points([ulc, self.rect.max_point]), self),
            }

    def get_line_representations(self):
        w_repr = LineRepresentation('width', LineSegment.from_points([Vec2(self.rect.min_point.x, self.rect.center.y),
                                                                      Vec2(self.rect.max_point.x, self.rect.center.y)]))
        h_repr = LineRepresentation('height', LineSegment.from_points([Vec2(self.rect.center.x, self.rect.min_point.y),
                                                                       Vec2(self.rect.center.x, self.rect.max_point.y)]))
        return {'width': w_repr, 'height': h_repr}

    def project_point(self, point):
        return point

    def distance_to_landmarks(self, point):
        result = []

        for name, obj in self.landmarks.items():
            result.append( (obj, obj.distance_to(point)) )

        return result


if __name__ == '__main__':
        poi = Vec2(float(sys.argv[1]), 0)
        l = LineRepresentation()

        f = l.get_line_features(poi)

        print 'dist_start = {dist_start}, dist_end = {dist_end}, dist_mid = {dist_mid}'.format(**f)
        print 'dir_start = {dir_start}, dir_end = {dir_end}, dir_mid = {dir_mid}'.format(**f)

        print 'Distance from POI to Start landmark is %f' % l.landmarks['start'].distance_to(poi)
        print 'Distance from POI to End landmark is %f' % l.landmarks['end'].distance_to(poi)
        print 'Distance from POI to Mid landmark is %f' % l.landmarks['mid'].distance_to(poi)

        r = RectangleRepresentation()
        print 'Distance from POI to LLCorner landmark is %f' % r.landmarks['ll_corner'].distance_to(poi)
        print 'Distance from POI to URCorner landmark is %f' % r.landmarks['ur_corner'].distance_to(poi)
        print 'Distance from POI to LRCorner landmark is %f' % r.landmarks['lr_corner'].distance_to(poi)
        print 'Distance from POI to ULCorner landmark is %f' % r.landmarks['ul_corner'].distance_to(poi)
        print 'Distance from POI to Center landmark is %f' % r.landmarks['center'].distance_to(poi)
        print 'Distance from POI to LEdge landmark is %f' % r.landmarks['l_edge'].distance_to(poi)
        print 'Distance from POI to REdge landmark is %f' % r.landmarks['r_edge'].distance_to(poi)
        print 'Distance from POI to NEdge landmark is %f' % r.landmarks['n_edge'].distance_to(poi)
        print 'Distance from POI to FEdge landmark is %f' % r.landmarks['f_edge'].distance_to(poi)
