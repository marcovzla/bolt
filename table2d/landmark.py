#!/usr/bin/env python

import sys
from planar import Vec2
from planar import BoundingBox
from planar.line import LineSegment
from planar.line import Line
from random import choice
from uuid import uuid4

class Landmark(object):
    def __init__(self, name, representation, parent, descriptions):
        self.name = name
        self.representation = representation
        self.parent = parent
        self.descriptions = descriptions
        self.uuid = uuid4()

        self.representation.parent_landmark = self

        for alt_repr in representation.get_alt_representations():
            alt_repr.parent_landmark = self

    def __repr__(self):
        return self.name

    def get_primary_axes(self):
        return self.get_top_parent().get_primary_axes()

    def distance_to(self, point):
        #tpd = self.get_top_parent().distance_to(point)
        #if self.parent: point = self.parent.project_point(point)
        return self.representation.distance_to(point)# + tpd

    def get_top_parent(self):
        top = self.parent
        if top is None: return self.representation
        if top.parent_landmark is None: self.representation
        return top.parent_landmark.get_top_parent()

    def get_ancestor_count(self):
        top = self.parent
        if top is None: return 0
        if top.parent_landmark is None: return 0
        return 1 + top.parent_landmark.get_ancestor_count()

    def get_description(self, perspective):
        top = self.get_top_parent()
        midpoint = top.middle
        lr_line = Line.from_points([perspective, midpoint])
        nf_line = lr_line.perpendicular(midpoint)

        adj = ''
        if self.parent:
            parent_left = True
            parent_right = True
            parent_near = True
            parent_far = True

            for point in self.parent.get_points():
                if not (lr_line.point_left(point) or lr_line.contains_point(point)):
                    parent_left = False
                if not (lr_line.point_right(point) or lr_line.contains_point(point)):
                    parent_right = False
                if not (nf_line.point_left(point) or nf_line.contains_point(point)):
                    parent_near = False
                if not (nf_line.point_right(point) or nf_line.contains_point(point)):
                    parent_far = False
            parent_lr = parent_left or parent_right and not (parent_left and parent_right)
            parent_nf = parent_near or parent_far and not (parent_near and parent_far)

            self_left, self_right, self_near, self_far = True, True, True, True
            for point in self.representation.get_points():
                if not (lr_line.point_left(point) or lr_line.contains_point(point)):
                    self_left = False
                if not (lr_line.point_right(point) or lr_line.contains_point(point)):
                    self_right = False
                if not (nf_line.point_left(point) or nf_line.contains_point(point)):
                    self_near = False
                if not (nf_line.point_right(point) or nf_line.contains_point(point)):
                    self_far = False

            if not parent_nf:
                if self_near and not self_far:
                    adj += 'near '
                if self_far and not self_near:
                    adj += 'far '
            if not parent_lr:
                if self_left and not self_right:
                    adj += 'left '
                if self_right and not self_left:
                    adj += 'right '


        noun = choice(self.descriptions)
        desc = 'the ' + adj + noun

        if self.parent:
            p_desc = self.parent.get_description(perspective)
            if p_desc:
                desc += ' of ' + p_desc

        return desc

    def fetch_landmark(self, uuid):
        # print 'Fetching ',uuid, '  My uuid: ',self.uuid
        if self.uuid == uuid:
            result = self
        else:
            result = None
            for representation in [self.representation] + self.representation.alt_representations:
                for landmark in representation.landmarks.values():
                    result = landmark.fetch_landmark(uuid)
                    if result:
                        return result
        return result


class AbstractRepresentation(object):
    def __init__(self, descriptions=[''], alt_of=None):
        self.alt_representations = []
        self.parent_landmark = None
        self.descriptions = descriptions
        self.landmarks = {}
        self.num_dim = -1
        self.alt_of = alt_of
        self.uuid = uuid4()

    def get_primary_axes(self):
        raise NotImplementedError

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

    def get_landmarks(self, max_level=-1):
        if max_level == 0: return []
        result = self.landmarks.values()

        for landmark in self.landmarks.values():
            result.extend( landmark.representation.get_landmarks(max_level-1) )

        return result

    def contains(self, other):
        raise NotImplementedError


class PointRepresentation(AbstractRepresentation):
    def __init__(self, point, descriptions=['point'], alt_of=None):
        super(PointRepresentation, self).__init__(descriptions, alt_of)
        self.location = point
        self.alt_representations = []
        self.landmarks = {}
        self.num_dim = 0
        self.middle = point

    def my_project_point(self, point):
        return Vec2(self.location.x, self.location.y)

    def distance_to(self, point):
        return self.location.distance_to(point)

    def contains(self, other):
        if other.num_dim > self.num_dim: return False
        return self.location == other.location

    def get_points(self):
        return [self.location]

    def get_geometry(self):
        return self.location

    def get_primary_axes(self):
        return [Line(self.location, Vec2(1,0)), Line(self.location, Vec2(0,1))]

class LineRepresentation(AbstractRepresentation):
    def __init__(self, orientation='height', line=LineSegment.from_points([Vec2(0, 0), Vec2(1, 0)]), descriptions=['line'], alt_of=None):
        super(LineRepresentation, self).__init__(descriptions, alt_of)
        self.line = line
        self.num_dim = 1
        self.middle = line.mid
        self.alt_representations = [PointRepresentation(self.line.mid, descriptions, self)]
        words = [['end'], ['middle','center'], ['end']] if orientation == 'height' \
           else [['side'], ['middle','center'], ['side']]

        self.landmarks = \
            {
                'start':  Landmark('start',  PointRepresentation(self.line.start), self, words[0]),
                'end':    Landmark('end',    PointRepresentation(self.line.end),   self, words[2]),
                'middle': Landmark('middle', PointRepresentation(self.line.mid),   self, words[1]),
            }

    def my_project_point(self, point):
        return self.line.line.project(point)

    def distance_to(self, point):
        return self.line.distance_to(point)

    def contains(self, other):
        if other.num_dim > self.num_dim: return False

        # Point
        if other.num_dim == 0:
            return self.line.contains_point(other.location)
        # Line
        elif other.num_dim == 1:
            return self.line.contains_point(other.line.start) and self.line.contains_point(other.line.end)

    def get_geometry(self):
        return self.line

    def get_points(self):
        return [self.line.start,self.line.end]

    def get_primary_axes(self):
        return [self.line.line, self.line.line.perpendicular(self.line.mid)]


class RectangleRepresentation(AbstractRepresentation):
    def __init__(self, rect=BoundingBox([Vec2(0, 0), Vec2(1, 2)]),
                 descriptions=['rectangle'],
                 landmarks_to_get=['ll_corner','ur_corner','lr_corner','ul_corner','middle','l_edge','r_edge','n_edge','f_edge','l_surf','r_surf','n_surf','f_surf','m_surf'],
                 alt_of=None):
        super(RectangleRepresentation, self).__init__(descriptions, alt_of)
        self.rect = rect
        self.num_dim = 2
        self.middle = rect.center
        self.alt_representations = [LineRepresentation('width',
                                                        LineSegment.from_points([Vec2(self.rect.min_point.x, self.rect.center.y),
                                                                                 Vec2(self.rect.max_point.x, self.rect.center.y)],),
                                                        descriptions,
                                                        self),
                                    LineRepresentation('height',
                                                        LineSegment.from_points([Vec2(self.rect.center.x, self.rect.min_point.y),
                                                                                 Vec2(self.rect.center.x, self.rect.max_point.y)]),
                                                        descriptions,
                                                        self)]

        lrc = Vec2(self.rect.min_point.x + self.rect.width, self.rect.min_point.y)
        ulc = Vec2(self.rect.max_point.x - self.rect.width, self.rect.max_point.y)

        # self.constituents = {
        #         'll_corner': PointRepresentation(self.rect.min_point),
        #         'ur_corner': PointRepresentation(self.rect.max_point),
        #         'lr_corner': PointRepresentation(lrc),
        #         'ul_corner': PointRepresentation(ulc),
        #         'middle':    PointRepresentation(self.rect.center),
        #         'l_edge':    LineRepresentation('height', LineSegment.from_points([self.rect.min_point, ulc])),
        #         'r_edge':    LineRepresentation('height', LineSegment.from_points([lrc, self.rect.max_point])),
        #         'n_edge':    LineRepresentation('width', LineSegment.from_points([self.rect.min_point, lrc])),
        #         'f_edge':    LineRepresentation('width', LineSegment.from_points([ulc, self.rect.max_point])),

        #         'l_surf':    SurfaceRepresentation( BoundingBox([rect.min_point,
        #                                                                                Vec2(rect.min_point.x+rect.width/2.0,
        #                                                                                     rect.max_point.y)]),
        #                                                                   landmarks_to_get=['ll_corner','ul_corner','l_edge']),
        #         'r_surf':    SurfaceRepresentation( BoundingBox([Vec2(rect.min_point.x+rect.width/2.0,
        #                                                                                     rect.min_point.y),
        #                                                                                rect.max_point]),
        #                                                                   landmarks_to_get=['lr_corner','ur_corner','r_edge']),
        #         'n_surf':    SurfaceRepresentation( BoundingBox([rect.min_point,
        #                                                                                Vec2(rect.max_point.x,
        #                                                                                     rect.min_point.y+rect.height/2.0)]),
        #                                                                   landmarks_to_get=['ll_corner','lr_corner','n_edge']),
        #         'f_surf':    SurfaceRepresentation( BoundingBox([Vec2(rect.min_point.x,
        #                                                                                     rect.min_point.y+rect.height/2.0),
        #                                                                                rect.max_point]),
        #                                                                   landmarks_to_get=['ul_corner','ur_corner','f_edge']),

        #         'm_surf':    SurfaceRepresentation( BoundingBox([Vec2(rect.min_point.x+rect.width/4.0,
        #                                                                                     rect.min_point.y+rect.height/4.0),
        #                                                                                Vec2(rect.max_point.x-rect.width/4.0,
        #                                                                                     rect.max_point.y-rect.height/4.0)])),
        # }

        landmark_constructors = {
                'll_corner': '''Landmark('ll_corner', PointRepresentation(self.rect.min_point), self, ['corner'])''',
                'ur_corner': '''Landmark('ur_corner', PointRepresentation(self.rect.max_point), self, ['corner'])''',
                'lr_corner': '''Landmark('lr_corner', PointRepresentation(lrc), self, ['corner'])''',
                'ul_corner': '''Landmark('ul_corner', PointRepresentation(ulc), self, ['corner'])''',
                'middle':    '''Landmark('middle',    PointRepresentation(self.rect.center), self, ['center'])''',
                'l_edge':    '''Landmark('l_edge',    LineRepresentation('height', LineSegment.from_points([self.rect.min_point, ulc])), self, ['edge'])''',
                'r_edge':    '''Landmark('r_edge',    LineRepresentation('height', LineSegment.from_points([lrc, self.rect.max_point])), self, ['edge'])''',
                'n_edge':    '''Landmark('n_edge',    LineRepresentation('width', LineSegment.from_points([self.rect.min_point, lrc])), self, ['edge'])''',
                'f_edge':    '''Landmark('f_edge',    LineRepresentation('width', LineSegment.from_points([ulc, self.rect.max_point])), self, ['edge'])''',

                'l_surf':    '''Landmark('l_surf',    SurfaceRepresentation( BoundingBox([rect.min_point,
                                                                                       Vec2(rect.min_point.x+rect.width/2.0,
                                                                                            rect.max_point.y)]),
                                                                          landmarks_to_get=['ll_corner','ul_corner','l_edge']),
                                      self, ['half'])''',
                'r_surf':    '''Landmark('r_surf',    SurfaceRepresentation( BoundingBox([Vec2(rect.min_point.x+rect.width/2.0,
                                                                                            rect.min_point.y),
                                                                                       rect.max_point]),
                                                                          landmarks_to_get=['lr_corner','ur_corner','r_edge']),
                                      self, ['half'])''',
                'n_surf':    '''Landmark('n_surf',    SurfaceRepresentation( BoundingBox([rect.min_point,
                                                                                       Vec2(rect.max_point.x,
                                                                                            rect.min_point.y+rect.height/2.0)]),
                                                                          landmarks_to_get=['ll_corner','lr_corner','n_edge']),
                                      self, ['half'])''',
                'f_surf':    '''Landmark('f_surf',    SurfaceRepresentation( BoundingBox([Vec2(rect.min_point.x,
                                                                                            rect.min_point.y+rect.height/2.0),
                                                                                       rect.max_point]),
                                                                          landmarks_to_get=['ul_corner','ur_corner','f_edge']),
                                      self, ['half'])''',

                'm_surf':    '''Landmark('m_surf',    SurfaceRepresentation( BoundingBox([Vec2(rect.min_point.x+rect.width/4.0,
                                                                                            rect.min_point.y+rect.height/4.0),
                                                                                       Vec2(rect.max_point.x-rect.width/4.0,
                                                                                            rect.max_point.y-rect.height/4.0)])), self, ['middle'])''',
        }



        self.landmarks = {}
        for lmk_name in landmarks_to_get:
            if lmk_name in landmark_constructors:
                self.landmarks[lmk_name] = eval(landmark_constructors[lmk_name])

    def my_project_point(self, point):
        return point

    def distance_to(self, point):
        if self.contains(PointRepresentation(point)):
            return float('infinity')
        if len(self.landmarks) == 0:
            return self.rect.center.distance_to(point)
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

    def get_geometry(self):
        return self.rect

    def get_points(self):
        return list(self.rect.to_polygon())

    def get_primary_axes(self):
        return [Line.from_points([Vec2(self.rect.min_point.x, self.rect.center.y),
                                  Vec2(self.rect.max_point.x, self.rect.center.y)]),
                Line.from_points([Vec2(self.rect.center.x, self.rect.min_point.y),
                                  Vec2(self.rect.center.x, self.rect.max_point.y)])]

class SurfaceRepresentation(RectangleRepresentation):
    def __init__(self, rect=BoundingBox([Vec2(0, 0), Vec2(1, 2)]), descriptions=['rectangle'], landmarks_to_get=[]):
        super(SurfaceRepresentation, self).__init__(rect,descriptions,landmarks_to_get)

        self.alt_representations = []

    def distance_to(self, point):
        return float('infinity')




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
            if lmk1.representation.contains(PointRepresentation(location)):
                sc = Scene(lmk1.representation.num_dim)

                for lmk2 in self.landmarks.values():
                    if lmk1.representation.contains(lmk2.representation): sc.add_landmark(lmk2)

                scenes.append(sc)
        return scenes

    def get_bounding_box(self):
        return BoundingBox.from_shapes([lmk.representation.get_geometry() for lmk in self.landmarks.values()])

    def fetch_landmark(self, uuid):
        result = None
        for landmark in self.landmarks.values():
            result = landmark.fetch_landmark(uuid)
            if result:
                break
        return result

if __name__ == '__main__':
    viewpoint = Vec2(5.5,4)
    table = Landmark('table',
                 RectangleRepresentation(rect=BoundingBox([Vec2(5,5), Vec2(6,7)]), descriptions=['table', 'table surface']),
                 None,
                 ['table', 'table surface'])

    print table.representation.landmarks['r_surf'].get_description(viewpoint)
