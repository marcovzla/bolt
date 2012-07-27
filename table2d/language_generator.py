from relation import *
from random import choice
from planar.line import Line
from landmark import Landmark



class_to_words = {
    Landmark.TABLE:    ['table', 'table surface'],
    Landmark.CHAIR:    ['chair'],
    Landmark.CUP:      ['cup'],
    Landmark.BOTTLE:   ['bottle'],
    Landmark.EDGE:     ['edge'],
    Landmark.CORNER:   ['corner'],
    Landmark.MIDDLE:   ['middle'],
    Landmark.HALF:     ['half'],
    Landmark.END:      ['end'],
    Landmark.SIDE:     ['side'],
    FromRelation:      ['from'],
    ToRelation:        ['to'],
    NextToRelation:    ['next to'],
    AtRelation:        ['at'],
    ByRelation:        ['by'],
    OnRelation:        ['on'],
    InRelation:        ['in'],
    InFrontRelation:   ['in front of'],
    BehindRelation:    ['behind'],
    LeftRelation:      ['to the left of'],
    RightRelation:     ['to the right of'],
    Degree.NONE:       [''],
    Degree.NOT_VERY:   ['not very'],
    Degree.SOMEWHAT:   ['somewhat'],
    Degree.VERY:       ['very'],
    Measurement.CLOSE: ['close'],
    Measurement.FAR:   ['far'],
    Measurement.NEAR:  ['near'],
}

def get_landmark_description(perspective, landmark):
    top = landmark.get_top_parent()
    midpoint = top.middle
    lr_line = Line.from_points([perspective, midpoint])
    nf_line = lr_line.perpendicular(midpoint)

    adj = ''
    if landmark.parent:
        parent_left = True
        parent_right = True
        parent_near = True
        parent_far = True

        for point in landmark.parent.get_points():
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

        landmark_left, landmark_right, landmark_near, landmark_far = True, True, True, True
        for point in landmark.representation.get_points():
            if not (lr_line.point_left(point) or lr_line.contains_point(point)):
                landmark_left = False
            if not (lr_line.point_right(point) or lr_line.contains_point(point)):
                landmark_right = False
            if not (nf_line.point_left(point) or nf_line.contains_point(point)):
                landmark_near = False
            if not (nf_line.point_right(point) or nf_line.contains_point(point)):
                landmark_far = False

        if not parent_nf:
            if landmark_near and not landmark_far:
                adj += 'near '
            if landmark_far and not landmark_near:
                adj += 'far '
        if not parent_lr:
            if landmark_left and not landmark_right:
                adj += 'left '
            if landmark_right and not landmark_left:
                adj += 'right '

    noun = choice(class_to_words[landmark.object_class])
    desc = 'the ' + adj + noun

    if landmark.parent and landmark.parent.parent_landmark:
        p_desc = get_landmark_description(perspective, landmark.parent.parent_landmark)
        if p_desc:
            desc += ' of ' + p_desc

    return desc

def get_relation_description(relation):
    desc = ''
    if hasattr(relation, 'measurement') and not isinstance(relation,VeryCloseDistanceRelation): #TODO create another class called AdjacentRelation
        m = relation.measurement
        degree = choice(class_to_words[m.best_degree_class])
        desc += degree + (' ' if degree else '') + choice(class_to_words[m.best_distance_class]) + ' '
    return desc + choice(class_to_words[type(relation)])

def describe(perspective, landmark, relation):
    return get_relation_description(relation) + ' ' + get_landmark_description(perspective, landmark)