#!/usr/bin/env python

import sys
from planar import Vec2
from planar import BoundingBox
from planar.line import LineSegment
from planar.line import Line
from random import choice


class Landmark(object):
    def __init__(self, name, representation, parent, descriptions):
        self.name = name
        self.representation = representation
        self.parent = parent
        self.descriptions = descriptions

    def __repr__(self):
        return self.name

    def distance_to(self, point):
        if self.parent: point = self.parent.project_point(point)
        return self.representation.distance_to(point)

    def get_top_parent(self):
        top = self.parent
        if top is None: return self.representation
        if top.parent_landmark is None: return top
        return top.parent_landmark.get_top_parent()

    def get_description(self, perspective):
        top = self.get_top_parent()
        midpoint = top.landmarks['middle'].representation.location
        lr_line = Line.from_points([perspective, midpoint])
        nf_line = lr_line.perpendicular(midpoint)

        adj = ''
        if self.parent:
            parent_left = True
            parent_right = True
            parent_near = True
            parent_far = True

            for point in self.parent.get_points():
                if not lr_line.point_left(point):
                    parent_left = False
                if not lr_line.point_right(point):
                    parent_right = False
                if not nf_line.point_left(point):
                    parent_near = False
                if not nf_line.point_right(point):
                    parent_far = False
            parent_lr = parent_left or parent_right
            parent_nf = parent_near or parent_far

            self_left, self_right, self_near, self_far = True, True, True, True
            for point in self.representation.get_points():
                if not lr_line.point_left(point):
                    self_left = False
                if not lr_line.point_right(point):
                    self_right = False
                if not nf_line.point_left(point):
                    self_near = False
                if not nf_line.point_right(point):
                    self_far = False

            if not parent_nf:
                if self_near:
                    adj += 'near '
                if self_far:
                    adj += 'far '
            if not parent_lr:
                if self_left:
                    adj += 'left '
                if self_right:
                    adj += 'right '


        noun = choice(self.descriptions)
        desc = 'the ' + adj + noun

        if self.parent:
            p_desc = self.parent.get_description(perspective)
            if p_desc:
                desc += ' of ' + p_desc

        return desc


class AbstractRepresentation(object):
    def __init__(self, descriptions=['']):
        self.alt_representations = []
        self.parent_landmark = None
        self.descriptions = descriptions
        self.landmarks = {}
        self.num_dim = -1

    def get_alt_representations(self):
        result = self.alt_representations

        for al in self.alt_representations:
            result.extend(al.get_alt_representations())

        return result

    def get_points(self):
        raise NotImplementedError

    def project_point(self, point):
        if self.parent_landmark is None:
            return self.my_project_point(point)
        else:
            return self.parent_landmark.parent.project_point(point)

    def my_project_point(self, point):
        raise NotImplementedError

    def distance_to(self, point):
        raise NotImplementedError

    def get_description(self, perspective):
        if self.parent_landmark:
            return self.parent_landmark.get_description(perspective)

        return 'the ' + choice(self.descriptions)

    def get_landmarks(self):
        result = self.landmarks.values()

        for landmark in self.landmarks.values():
            result.extend( landmark.representation.get_landmarks() )

        return result

    def contains(self, other):
        raise NotImplementedError


class PointRepresentation(AbstractRepresentation):
    def __init__(self, point, descriptions=['point']):
        super(PointRepresentation, self).__init__(descriptions)
        self.location = point
        self.alt_representations = []
        self.landmarks = {}
        self.num_dim = 0

    def my_project_point(self, point):
        return Vec2(self.location.x, self.location.y)

    def distance_to(self, point):
        return self.location.distance_to(point)

    def contains(self, other):
        if other.num_dim > self.num_dim: return False
        return self.location == other.location

    def get_points(self):
        return [self.location]


class LineRepresentation(AbstractRepresentation):
    def __init__(self, orientation='height', line=LineSegment.from_points([Vec2(0, 0), Vec2(1, 0)]), descriptions=['line']):
        super(LineRepresentation, self).__init__(descriptions)
        self.line = line
        self.num_dim = 1
        self.alt_representations = [PointRepresentation(self.line.mid, descriptions)]
        words = [['end'], ['middle','center'], ['end']] if orientation == 'height' \
           else [['side'], ['middle','center'], ['side']]

        self.landmarks = \
            {
                'start':  Landmark('start',  PointRepresentation(self.line.start), self, words[0]),
                'end':    Landmark('end',    PointRepresentation(self.line.end),   self, words[2]),
                'middle': Landmark('middle', PointRepresentation(self.line.mid),   self, words[1]),
            }

        for lmk in self.landmarks.values():
            lmk.representation.parent_landmark = lmk

    def my_project_point(self, point):
        return self.line.line.project(point)

    def distance_to(self, point):
        return self.line.distance_to(point)

    def contains(self, other):
        if other.num_dim > self.num_dim: return False

        # Point
        if other.num_dim == 0:
            return self.line.contains_point(other)
        # Line
        elif other.num_dim == 1:
            return self.line.contains_point(other.line.start) and self.line.contains_point(other.line.end)

    def get_points(self):
        return [self.line.start,self.line.end]


class RectangleRepresentation(AbstractRepresentation):
    def __init__(self, rect=BoundingBox([Vec2(0, 0), Vec2(1, 2)]), descriptions=['rectangle']):
        super(RectangleRepresentation, self).__init__(descriptions)
        self.rect = rect
        self.num_dim = 2
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
                'll_corner': Landmark('ll_corner', PointRepresentation(self.rect.min_point), self, ['corner']),
                'ur_corner': Landmark('ur_corner', PointRepresentation(self.rect.max_point), self, ['corner']),
                'lr_corner': Landmark('lr_corner', PointRepresentation(lrc), self, ['corner']),
                'ul_corner': Landmark('ul_corner', PointRepresentation(ulc), self, ['corner']),
                'middle':    Landmark('middle',    PointRepresentation(self.rect.center), self, ['center']),
                'l_edge':    Landmark('l_edge',    LineRepresentation('height', LineSegment.from_points([self.rect.min_point, ulc])), self, ['edge']),
                'r_edge':    Landmark('r_edge',    LineRepresentation('height', LineSegment.from_points([lrc, self.rect.max_point])), self, ['edge']),
                'n_edge':    Landmark('n_edge',    LineRepresentation('width', LineSegment.from_points([self.rect.min_point, lrc])), self, ['edge']),
                'f_edge':    Landmark('f_edge',    LineRepresentation('width', LineSegment.from_points([ulc, self.rect.max_point])), self, ['edge']),
            }

        for lmk in self.landmarks.values():
            lmk.representation.parent_landmark = lmk

    def my_project_point(self, point):
        return point

    def distance_to(self, point):
        return min([lmk.representation.distance_to(point) for lmk in self.landmarks.values()])

    def contains(self, other):
        if other.num_dim > self.num_dim: return False
        if other.num_dim == 0:
            return self.rect.contains_point(other.location)
        if other.num_dim == 1:
            return self.rect.contains_point(other.line.start) and self.rect.contains_point(other.line.end)
        if other.num_dim == 2:
            if self.rect.min_point <= other.rect.min_point and self.rect.max_point >= other.rect.max_point: return True
            return False

    def get_points(self):
        return list(self.rect.to_polygon())

class Scene(object):
    def __init__(self, num_dim):
        self.num_dim = num_dim
        self.landmarks = {}

    def __repr__(self):
        return 'Scene(' + str(self.num_dim) + ', ' + str(self.landmarks) + ')'

    def add_landmark(self, lmk):
        self.landmarks[lmk.name] = lmk

    def get_child_scenes(self, location):
        scenes = []

        for lmk1 in self.landmarks.values():
            print 'checking ', lmk1.name
            if lmk1.representation.contains(PointRepresentation(location)):
                print lmk1.name, ' contains point ', location, ' lmk repr ', lmk1.representation, '\n\n'
                sc = Scene(lmk1.representation.num_dim)

                for lmk2 in self.landmarks.values():
                    if lmk1.representation.contains(lmk2.representation): sc.add_landmark(lmk2)

                scenes.append(sc)
        print len(scenes)
        return scenes


if __name__ == '__main__':
    table = Landmark('table',
                 RectangleRepresentation(rect=BoundingBox([Vec2(5,5), Vec2(6,7)]), descriptions=['table', 'table surface']),
                 None,
                 ['table', 'table surface'])

    print table.representation.landmarks['ul_corner'].get_description(Vec2(4,6))
