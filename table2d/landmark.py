#!/usr/bin/env python

import sys
from planar import Vec2
from planar import BoundingBox
from planar import Polygon
from planar.line import LineSegment
from planar.line import Line
from random import choice
from uuid import uuid4
from math import sqrt
import numpy as np
import matplotlib.pyplot as plt

# Let's pretend we're importing this from planar
class Circle(object):
    def __init__(self, center, radius):
        self.center = center
        self.radius = radius
        rad_point = Vec2(radius,radius)
        self.bounding_box = BoundingBox([self.center - rad_point, self.center + rad_point])

    def distance_to_edge(self, point):
        return self.center.distance_to(point) - self.radius

    def distance_to(self, point):
        distance = self.distance_to_edge(point)
        return distance if distance >= 0 else 0

    def contains_point(self, point):
        return True if self.distance_to_edge(point) < 0 else False


def ccw(A,B,C):
    ccw = (C.y-A.y)*(B.x-A.x) > (B.y-A.y)*(C.x-A.x)
    return 1 if ccw > 0.0 else -1 if ccw < 0.0 else 0

def intersect(seg1,seg2):
    A,B = seg1.points
    C,D = seg2.points
    return ccw(A,C,D) != ccw(B,C,D) and ccw(A,B,C) != ccw(A,B,D)

def pairwise(l):
    pairs = []
    for i in range(1, len(l)):
        pairs.append( (l[i-1], l[i]) )
    return pairs

def seg_to_seg_distance(seg1, seg2):
    if intersect(seg1,seg2):
        return 0
    else:
        dists = []
        dists.append( seg1.distance_to(
            +seg2.start) )
        dists.append( seg1.distance_to(seg2.end) )
        dists.append( seg2.distance_to(seg1.start) )
        dists.append( seg2.distance_to(seg1.end) )
        return min(dists)

def bb_to_bb_manhattan_distance(bb1, bb2):
    N = 2 # cardinality of points

    result = 0
    for i in range(N):
        delta = 0
        # print bb1.min_point[i], bb2.max_point[i], bb1.min_point[i] > bb2.max_point[i]
        # print bb2.min_point[i], bb1.max_point[i], bb2.min_point[i] > bb1.max_point[i]
        if bb1.min_point[i] > bb2.max_point[i]:
            delta = bb2.max_point[i] - bb1.min_point[i]
        elif bb2.min_point[i] > bb1.max_point[i]:
            delta = bb1.max_point[i] - bb2.min_point[i]

        result += delta * delta

    return result

def poly_to_edges(poly):
    edges = []
    for i in range(1, len(poly)):
        edges.append( LineSegment.from_points( [poly[i-1],poly[i]]) )
    return edges

def poly_to_vec_distance(poly, vec):
    if poly.contains_point( vec ):
        return 0

    dists = []
    for edge in poly_to_edges(poly):
        dists.append( edge.distance_to(vec) )

    return min(dists)

def poly_to_seg_distance(poly, seg):
    dists = []

    for edge in poly_to_edges(poly):
        dists.append(  seg_to_seg_distance( edge, seg )  )

    return min(dists)

def bb_to_bb_distance(bb1, bb2):
    return sqrt(bb_to_bb_manhattan_distance(bb1,bb2))

def poly_to_poly_distance(poly1, poly2):
    dists = []
    for e1 in poly_to_edges(poly1):
        dists.append(poly_to_seg_distance(poly2, e1))
    return min(dists)


class Color(object):
    RED = 'RED'
    GREEN = 'GREEN'
    PURPLE = 'PURPLE'
    BLUE = 'BLUE'
    PINK = 'PINK'
    ORANGE = 'ORANGE'
    YELLOW = 'YELLOW'
    BLACK = 'BLACK'
    WHITE = 'WHITE'


class ObjectClass(object):
    TABLE = 'TABLE'
    CHAIR = 'CHAIR'
    CUP = 'CUP'
    BOTTLE = 'BOTTLE'
    PRISM= 'PRISM'


class Landmark(object):
    EDGE = 'EDGE'
    CORNER = 'CORNER'
    MIDDLE = 'MIDDLE'
    HALF = 'HALF'
    END = 'END'
    SIDE = 'SIDE'
    LINE = 'LINE'
    POINT = 'POINT'

    def __init__(self, name, representation, parent, object_class=None, color=None):
        self.name = name
        self.representation = representation
        self.parent = parent
        self.object_class = object_class
        self.color = color
        self.uuid = uuid4()

        self.representation.parent_landmark = self

        for alt_repr in representation.get_alt_representations():
            alt_repr.parent_landmark = self

    def __repr__(self):
        return self.name

    def get_primary_axes(self, perspective=None):
        return self.get_top_parent().get_primary_axes()

    def distance_to(self, rep):
        #tpd = self.get_top_parent().distance_to(point)
        #if self.parent: point = self.parent.project_point(point)
        return self.representation.distance_to(rep)# + tpd

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
    def __init__(self, alt_of=None):
        self.alt_representations = []
        self.parent_landmark = None
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

    def distance_to(self, rep):
        ''' Takes Representation, returns float '''
        raise NotImplementedError

    def get_landmarks(self, max_level=-1):
        if max_level == 0: return []
        result = self.landmarks.values()

        for landmark in self.landmarks.values():
            result.extend( landmark.representation.get_landmarks(max_level-1) )

        return result

    def contains(self, other):
        ''' Takes Representation, returns boolean '''
        raise NotImplementedError


class PointRepresentation(AbstractRepresentation):
    def __init__(self, point, alt_of=None):
        super(PointRepresentation, self).__init__(alt_of)
        self.location = point
        self.alt_representations = []
        self.landmarks = {}
        self.num_dim = 0
        self.middle = point

    def my_project_point(self, point):
        return Vec2(self.location.x, self.location.y)

    def distance_to(self, rep):
        geo = rep.get_geometry()
        if isinstance(geo, BoundingBox):
            return poly_to_vec_distance(geo.to_polygon(), self.location)
        elif isinstance(geo, Polygon):
            return poly_to_vec_distance(geo, self.location)
        else:
            return geo.distance_to(self.location)

    def contains(self, other):
        ''' If PointRepresentation return True if approx. equal.
            Return False if any other representation. '''
        if other.num_dim > self.num_dim: return False
        return self.location.almost_equals(other.location)

    def get_points(self):
        return [self.location]

    def get_geometry(self):
        return self.location

    def get_primary_axes(self):
        return [Line(self.location, Vec2(1,0)), Line(self.location, Vec2(0,1))]


class LineRepresentation(AbstractRepresentation):
    def __init__(self, orientation='height', line=LineSegment.from_points([Vec2(0, 0), Vec2(1, 0)]), alt_of=None):
        super(LineRepresentation, self).__init__(alt_of)
        self.line = line
        # extend the LineSegment to include a bounding_box field, planar doesn't have that originally
        self.line.bounding_box = BoundingBox.from_points(self.line.points)
        self.num_dim = 1
        self.middle = line.mid
        self.alt_representations = [PointRepresentation(self.line.mid, self)]

        classes = [Landmark.END, Landmark.MIDDLE, Landmark.END] if orientation == 'height' \
             else [Landmark.SIDE, Landmark.MIDDLE, Landmark.SIDE]

        self.landmarks = {
            'start':  Landmark('start',  PointRepresentation(self.line.start), self, classes[0]),
            'end':    Landmark('end',    PointRepresentation(self.line.end),   self, classes[2]),
            'middle': Landmark('middle', PointRepresentation(self.line.mid),   self, classes[1]),
        }

    def my_project_point(self, point):
        return self.line.line.project(point)

    def distance_to(self, rep):
        geo = rep.get_geometry()
        if isinstance(geo,Vec2):
            return self.line.distance_to(geo)
        elif isinstance(geo,LineSegment):
            return seg_to_seg_distance(self.line, geo)
        elif isinstance(geo,BoundingBox):
            return poly_to_seg_distance(geo.to_polygon(), self.line)
        elif isinstance(geo,Polygon):
            return poly_to_seg_distance(geo, self.line)

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

class CircleRepresentation(AbstractRepresentation):
    def __init__(self, circ, alt_of=None):
        self.circ = circ
        self.num_dim = 2
        self.middle = circ.center
        self.alt_representations = [PointRepresentation(self.middle, self)]

        self.landmarks = {
            'middle': Landmark('middle', PointRepresentation(self.middle), self, Landmark.MIDDLE)
        }

    def my_project_point(self, point):
        return point

    def distance_to(self, rep):
        geo = rep.get_geometry()
        if isinstance(geo,Vec2):
            return self.circ.distance_to(geo)
        elif isinstance(geo,LineSegment):
            distance = geo.distance_to(self.circ.center) - self.circ.radius
        elif isinstance(geo,BoundingBox):
            distance = poly_to_vec_distance(geo.to_polygon(), self.circ.center) - self.circ.radius
        elif isinstance(geo,Polygon):
            distance = poly_to_vec_distance(geo, self.circ.center) - self.circ.radius
        elif isinstance(geo,Circle):
            self.circ.distance_to(geo.center) - geo.radius
        return distance if distance > 0 else 0

    def contains(self, other):
        if other.num_dim > self.num_dim: return False
        if other.num_dim == 0:
            return self.circ.contains_point(other.location)
        if other.num_dim == 1:
            return self.circ.contains_point(other.line.start) and self.circ.contains_point(other.line.end)
        if other.num_dim == 2:
            if isinstance(other,Circle):
                return True if self.circ.center.distance_to(other.circ.center) + other.circ.radius < self.circ.radius else False
            for p in other.get_points():
                if not self.circ.contains_point(p): return False
            return True

    def get_geometry(self):
        return self.circ

class RectangleRepresentation(AbstractRepresentation):
    def __init__(self, rect=BoundingBox([Vec2(0, 0), Vec2(1, 2)]),
                 landmarks_to_get=['ll_corner','ur_corner','lr_corner','ul_corner','middle','l_edge','r_edge','n_edge','f_edge','l_surf','r_surf','n_surf','f_surf','m_surf'],
                 alt_of=None):
        super(RectangleRepresentation, self).__init__(alt_of)
        self.rect = rect
        self.num_dim = 2
        self.middle = rect.center
        self.alt_representations = [LineRepresentation('width',
                                                        LineSegment.from_points([Vec2(self.rect.min_point.x, self.rect.center.y),
                                                                                 Vec2(self.rect.max_point.x, self.rect.center.y)],),
                                                        self),
                                    LineRepresentation('height',
                                                        LineSegment.from_points([Vec2(self.rect.center.x, self.rect.min_point.y),
                                                                                 Vec2(self.rect.center.x, self.rect.max_point.y)]),
                                                        self)]

        lrc = Vec2(self.rect.min_point.x + self.rect.width, self.rect.min_point.y)
        ulc = Vec2(self.rect.max_point.x - self.rect.width, self.rect.max_point.y)

        landmark_constructors = {
                'll_corner': '''Landmark('ll_corner', PointRepresentation(self.rect.min_point), self, Landmark.CORNER)''',
                'ur_corner': '''Landmark('ur_corner', PointRepresentation(self.rect.max_point), self, Landmark.CORNER)''',
                'lr_corner': '''Landmark('lr_corner', PointRepresentation(lrc), self, Landmark.CORNER)''',
                'ul_corner': '''Landmark('ul_corner', PointRepresentation(ulc), self, Landmark.CORNER)''',
                'middle':    '''Landmark('middle',    PointRepresentation(self.rect.center), self, Landmark.MIDDLE)''',
                'l_edge':    '''Landmark('l_edge',    LineRepresentation('height', LineSegment.from_points([self.rect.min_point, ulc])), self, Landmark.EDGE)''',
                'r_edge':    '''Landmark('r_edge',    LineRepresentation('height', LineSegment.from_points([lrc, self.rect.max_point])), self, Landmark.EDGE)''',
                'n_edge':    '''Landmark('n_edge',    LineRepresentation('width', LineSegment.from_points([self.rect.min_point, lrc])), self, Landmark.EDGE)''',
                'f_edge':    '''Landmark('f_edge',    LineRepresentation('width', LineSegment.from_points([ulc, self.rect.max_point])), self, Landmark.EDGE)''',

                'l_surf':    '''Landmark('l_surf',    SurfaceRepresentation( BoundingBox([rect.min_point,
                                                                                       Vec2(rect.min_point.x+rect.width/2.0,
                                                                                            rect.max_point.y)]),
                                                                          landmarks_to_get=['ll_corner','ul_corner','l_edge']),
                                      self, Landmark.HALF)''',
                'r_surf':    '''Landmark('r_surf',    SurfaceRepresentation( BoundingBox([Vec2(rect.min_point.x+rect.width/2.0,
                                                                                            rect.min_point.y),
                                                                                       rect.max_point]),
                                                                          landmarks_to_get=['lr_corner','ur_corner','r_edge']),
                                      self, Landmark.HALF)''',
                'n_surf':    '''Landmark('n_surf',    SurfaceRepresentation( BoundingBox([rect.min_point,
                                                                                       Vec2(rect.max_point.x,
                                                                                            rect.min_point.y+rect.height/2.0)]),
                                                                          landmarks_to_get=['ll_corner','lr_corner','n_edge']),
                                      self, Landmark.HALF)''',
                'f_surf':    '''Landmark('f_surf',    SurfaceRepresentation( BoundingBox([Vec2(rect.min_point.x,
                                                                                            rect.min_point.y+rect.height/2.0),
                                                                                       rect.max_point]),
                                                                          landmarks_to_get=['ul_corner','ur_corner','f_edge']),
                                      self, Landmark.HALF)''',

                'm_surf':    '''Landmark('m_surf',    SurfaceRepresentation( BoundingBox([Vec2(rect.min_point.x+rect.width/4.0,
                                                                                            rect.min_point.y+rect.height/4.0),
                                                                                       Vec2(rect.max_point.x-rect.width/4.0,
                                                                                            rect.max_point.y-rect.height/4.0)])), self, Landmark.MIDDLE)''',
        }

        self.landmarks = {}
        for lmk_name in landmarks_to_get:
            if lmk_name in landmark_constructors:
                self.landmarks[lmk_name] = eval(landmark_constructors[lmk_name])

    def my_project_point(self, point):
        return point

    def distance_to(self, rep):
        geo = rep.get_geometry()
        if isinstance(geo,Vec2):
            return poly_to_vec_distance(self.rect.to_polygon(), geo)
        elif isinstance(geo,LineSegment):
            return poly_to_seg_distance(self.rect.to_polygon(), geo)
        elif isinstance(geo,BoundingBox):
            return bb_to_bb_distance(self.rect, geo)
        elif isinstance(geo,Polygon):
            return poly_to_poly_distance(self.rect.to_polygon(), geo)

    def contains(self, other):
        if other.num_dim > self.num_dim: return False
        if other.num_dim == 0:
            return self.rect.contains_point(other.location)
        if other.num_dim == 1:
            return self.rect.contains_point(other.line.start) and self.rect.contains_point(other.line.end)
        if other.num_dim == 2:
            for p in other.get_points():
                if not self.rect.contains_point(p): return False
            return True

    def get_geometry(self):
        return self.rect

    def get_points(self):
        return list(self.rect.to_polygon())

    def get_primary_axes(self):
        return [Line.from_points([Vec2(self.rect.min_point.x, self.rect.center.y),
                                  Vec2(self.rect.max_point.x, self.rect.center.y)]),
                Line.from_points([Vec2(self.rect.center.x, self.rect.min_point.y),
                                  Vec2(self.rect.center.x, self.rect.max_point.y)])]


class PolygonRepresentation(AbstractRepresentation):
    def __init__(self, poly, alt_of=None):
        super(PolygonRepresentation, self).__init__(alt_of)
        self.poly = poly
        self.num_dim = 2
        self.middle = poly.centroid
        self.landmarks = {
            'middle': Landmark('middle', PointRepresentation(self.middle), self, Landmark.MIDDLE)
        }

    def my_project_point(self, point):
        return point

    def distance_to(self, rep):
        geo = rep.get_geometry()
        if isinstance(geo,Vec2):
            return poly_to_vec_distance(self.poly, geo)
        elif isinstance(geo,LineSegment):
            return poly_to_seg_distance(self.poly, geo)
        elif isinstance(geo,BoundingBox):
            return poly_to_poly_distance(self.poly, geo.to_polygon())
        elif isinstance(geo, Polygon):
            return poly_to_poly_distance(self.poly, geo)

    def contains(self, other):
        if other.num_dim > self.num_dim: return False
        if other.num_dim == 0:
            return self.poly.contains_point(other.location)
        if other.num_dim == 1:
            return self.poly.contains_point(other.line.start) and self.poly.contains_point(other.line.end)
        if other.num_dim == 2:
            for p in other.get_points():
                if not self.poly.contains_point(p): return False
            return True

    def get_geometry(self):
        return self.poly

    def get_points(self):
        return list(self.poly)

    def get_primary_axes(self):
        return []


class SurfaceRepresentation(RectangleRepresentation):
    def __init__(self, rect=BoundingBox([Vec2(0, 0), Vec2(1, 2)]), landmarks_to_get=[]):
        super(SurfaceRepresentation, self).__init__(rect, landmarks_to_get)
        self.alt_representations = []


class GroupLineRepresentation(LineRepresentation):
    def __init__(self, lmk_group, alt_of=None):
        centers = np.array([lmk.representation.middle for lmk in lmk_group])
        x = centers[:,0]
        y = centers[:,1]
        A = np.vstack([x, np.ones(len(x))]).T
        m, c = np.linalg.lstsq(A, y)[0]
        lxy = zip(x, m*x + c)
        points = [Vec2(px,py) for px,py in sorted(lxy)]

        super(GroupLineRepresentation, self).__init__(line=LineSegment.from_points(points),alt_of=alt_of)

        sorted_idx = sorted(range(len(lxy)), key=lxy.__getitem__)
        self.landmark_group = [lmk_group[idx] for idx in sorted_idx]


class GroupRectangleRepresentation(RectangleRepresentation):
    def __init__(self, lmk_group, alt_of=None):
        shapes = [lmk.get_geometry() for lmk in lmk_group]
        super(GroupRectangleRepresentation, self).__init__(rect=BoundingBox.from_shapes(shapes),
                                                           landmarks_to_get=['middle'],
                                                           alt_of=alt_of)
        self.landmark_group = lmk_group


class Scene(object):
    def __init__(self, num_dim):
        self.num_dim = num_dim
        self.landmarks = {}

    def __repr__(self):
        return 'Scene(' + str(self.num_dim) + ', ' + str(self.landmarks) + ')'

    def add_landmark(self, lmk):
        self.landmarks[lmk.name] = lmk

    def get_child_scenes(self, trajector):
        scenes = []

        for lmk1 in self.landmarks.values():
            if lmk1.representation.contains(trajector.representation):
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
