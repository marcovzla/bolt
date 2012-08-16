from relation import *
from random import choice
from landmark import Landmark, ObjectClass, Color


# point_words = ['bottle', 'cup', 'computer', 'laptop', 'keyboard', 'book', 'box', 'monitor',
#                'disc', 'CD', 'camera', 'lens', 'motor', 'screwdriver', 'pen', 'pencil']

class_to_words = {
    ObjectClass.TABLE:    {'N' : ['table']},
    ObjectClass.CHAIR:    {'N' : ['chair']},
    ObjectClass.CUP:      {'N' : ['cup']},
    ObjectClass.BOTTLE:   {'N' : ['bottle']},
    ObjectClass.PRISM:    {'N' : ['prism', 'triangle']},
    Color.RED:            {'A' : ['red']},
    Color.GREEN:          {'A' : ['green']},
    Color.PURPLE:         {'A' : ['purple']},
    Color.BLUE:           {'A' : ['blue']},
    Color.PINK:           {'A' : ['pink']},
    Color.ORANGE:         {'A' : ['orange']},
    Color.YELLOW:         {'A' : ['yellow']},
    Color.BLACK:          {'A' : ['black']},
    Color.WHITE:          {'A' : ['white']},
    Landmark.EDGE:     {'N' : ['edge']},
    Landmark.CORNER:   {'N' : ['corner']},
    Landmark.MIDDLE:   {'N' : ['middle']},
    Landmark.HALF:     {'N' : ['half']},
    Landmark.END:      {'N' : ['end']},
    Landmark.SIDE:     {'N' : ['side']},
    Landmark.LINE:     {'N' : ['line']},
    Landmark.POINT:    {'N' : ['point']},
    FromRelation:      {'P' : ['from']},
    ToRelation:        {'P' : ['to']},
    NextToRelation:    {'P' : ['next to', 'at', 'by']},
    OnRelation:        {'P' : ['on']},
    InFrontRelation:   {'P' : ['in front of'], 'A' : ['front', 'near']},
    BehindRelation:    {'P' : ['behind'], 'A' : ['back', 'far']},
    LeftRelation:      {'P' : ['to the left of'], 'A' : ['left']},
    RightRelation:     {'P' : ['to the right of'], 'A' : ['right']},
    Degree.NONE:       {'R' : ['']},
    Degree.SOMEWHAT:   {'R' : ['somewhat']},
    Degree.VERY:       {'R' : ['very']},
    Measurement.NONE:  {'A' : ['']},
    Measurement.FAR:   {'A' : ['far']},
    Measurement.NEAR:  {'A' : ['near', 'close']},
}

phrase_to_class = {
    'table':    ObjectClass.TABLE,
    'table surface':    ObjectClass.TABLE,
    'chair':    ObjectClass.CHAIR,
    'cup':  ObjectClass.CUP,
    'bottle':   ObjectClass.BOTTLE,
    'edge': Landmark.EDGE,
    'corner':   Landmark.CORNER,
    'middle':   Landmark.MIDDLE,
    'half': Landmark.HALF,
    'end':  Landmark.END,
    'side': Landmark.SIDE,
    'line': Landmark.LINE,
    'from': FromRelation,
    'to':   ToRelation,
    'next to':  NextToRelation,
    'at':  NextToRelation,
    'by':  NextToRelation,
    'on':   OnRelation,
    'in front of':  InFrontRelation,
    'front':    InFrontRelation,
    'near': InFrontRelation,
    'behind':   BehindRelation,
    'back': BehindRelation,
    'far':  BehindRelation,
    'to the left of':   LeftRelation,
    'left': LeftRelation,
    'to the right of':  RightRelation,
    'right':    RightRelation,
    'somewhat': Degree.SOMEWHAT,
    'very': Degree.VERY,
    'close':    Measurement.NEAR,
    'of':   'OF',
    'the':  'DT',

}

def get_landmark_description(perspective, landmark, delimit_chunks=False):
    noun = choice(class_to_words[landmark.object_class]['N']) + (' * ' if delimit_chunks else ' ')
    desc = 'the' + (' * ' if delimit_chunks else ' ')

    for option in landmark.ori_relations:
        desc += choice( class_to_words[type(option)]['A'] ) + (' * ' if delimit_chunks else ' ')

    desc += (choice(class_to_words[landmark.color]['A']) + ' ' if landmark.color else '') + noun

    if landmark.parent and landmark.parent.parent_landmark:
        p_desc = get_landmark_description(perspective, landmark.parent.parent_landmark)
        if p_desc:
            desc += 'of' + (' * ' if delimit_chunks else ' ') + p_desc

    return desc

def get_relation_description(relation, delimit_chunks=False):
    desc = ''
    if hasattr(relation, 'measurement') and not isinstance(relation,VeryCloseDistanceRelation): #TODO create another class called AdjacentRelation
        m = relation.measurement
        degree = choice(class_to_words[m.best_degree_class]['R'])
        distance = choice(class_to_words[m.best_distance_class]['A'])
        desc += degree   + ( (' * ' if delimit_chunks else ' ') if degree else '') + \
                distance + ( (' * ' if delimit_chunks else ' ') if distance else '')
    return desc + choice(class_to_words[type(relation)]['P']) + (' * ' if delimit_chunks else ' ')

def describe(perspective, trajector, landmark, relation, delimit_chunks=False):
    return 'The ' + \
           (choice(class_to_words[trajector.color]['A']) + ' ' if trajector.color else '') + \
           choice(class_to_words[trajector.object_class]['N']) + ' is' + \
           (' * ' if delimit_chunks else ' ') + \
           get_relation_description(relation, delimit_chunks) + \
           get_landmark_description(perspective, landmark, delimit_chunks)

def phrases_to_meaning(phrases):
    m = []

    for p in phrases:
        p = p.strip()
        if p in phrase_to_class:
            m.append(phrase_to_class[p])

    print m

if __name__ == '__main__':
    f = open('/home/anton/github/bolt/voting-experts/input/word/bolt_all_3k.txt')
    for l in f:
        phrases = l.split('*')
        print phrases
        phrases_to_meaning(phrases)