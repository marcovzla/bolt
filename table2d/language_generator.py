from relation import *
from random import choice
from planar.line import Line
from landmark import Landmark



class_to_words = {
    Landmark.TABLE:    {'N' : ['table', 'table surface']},
    Landmark.CHAIR:    {'N' : ['chair']},
    Landmark.CUP:      {'N' : ['cup']},
    Landmark.BOTTLE:   {'N' : ['bottle']},
    Landmark.EDGE:     {'N' : ['edge']},
    Landmark.CORNER:   {'N' : ['corner']},
    Landmark.MIDDLE:   {'N' : ['middle']},
    Landmark.HALF:     {'N' : ['half']},
    Landmark.END:      {'N' : ['end']},
    Landmark.SIDE:     {'N' : ['side']},
    Landmark.LINE:     {'N' : ['line']},
    FromRelation:      {'P' : ['from']},
    ToRelation:        {'P' : ['to']},
    NextToRelation:    {'P' : ['next to']},
    AtRelation:        {'P' : ['at']},
    ByRelation:        {'P' : ['by']},
    OnRelation:        {'P' : ['on']},
    InRelation:        {'P' : ['in']},
    InFrontRelation:   {'P' : ['in front of'], 'A' : ['front', 'near']},
    BehindRelation:    {'P' : ['behind'], 'A' : ['back', 'far']},
    LeftRelation:      {'P' : ['to the left of'], 'A' : ['left']},
    RightRelation:     {'P' : ['to the right of'], 'A' : ['right']},
    Degree.NONE:       {'R' : ['']},
    # Degree.NOT_VERY:   {'R' : ['not very']},
    Degree.SOMEWHAT:   {'R' : ['somewhat']},
    Degree.VERY:       {'R' : ['very']},
    Measurement.NONE:  {'A' : ['']},
    Measurement.CLOSE: {'A' : ['close']},
    Measurement.FAR:   {'A' : ['far']},
    Measurement.NEAR:  {'A' : ['near']},
}

def get_landmark_description(perspective, landmark):
    noun = choice(class_to_words[landmark.object_class]['N'])
    desc = 'the '

    if landmark.parent and landmark.parent.parent_landmark:
        '''
        options = set(OrientationRelationSet.relations)
        for point in [landmark.representation.middle]:
            middle_lmk = Landmark('', PointRepresentation(landmark.parent.middle), None, None)
            new_opts = OrientationRelationSet.get_applicable_relations(perspective, middle_lmk, point, use_distance=False)
            options = set(map(type, new_opts)).intersection(options)
        '''
        middle_lmk = Landmark('', PointRepresentation(landmark.parent.middle), landmark.parent, None)
        options = OrientationRelationSet.get_applicable_relations(perspective, middle_lmk, landmark.representation.middle, use_distance=False)
        for option in options:
            desc += choice( class_to_words[type(option)]['A'] ) + ' '
        desc += noun

        p_desc = get_landmark_description(perspective, landmark.parent.parent_landmark)
        if p_desc:
            desc += ' of ' + p_desc
    else:
        desc += noun

    return desc

def get_relation_description(relation):
    desc = ''
    if hasattr(relation, 'measurement') and not isinstance(relation,VeryCloseDistanceRelation): #TODO create another class called AdjacentRelation
        m = relation.measurement
        degree = choice(class_to_words[m.best_degree_class]['R'])
        distance = choice(class_to_words[m.best_distance_class]['A'])
        desc += degree + (' ' if degree else '') + distance + (' ' if distance else '')
    return desc + choice(class_to_words[type(relation)]['P'])

def describe(perspective, landmark, relation):
    return get_relation_description(relation) + ' ' + get_landmark_description(perspective, landmark)