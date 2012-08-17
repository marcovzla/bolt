from planar import Vec2, BoundingBox
from collections import namedtuple
import numpy as np
import SceneEval



PhysicalObject = namedtuple('physicalObject', ['id', 'position', 'bbmin', 'bbmax'])
objects = []
def adapt(scene):
    '''takes a scene object and returns a list of lists of objects that form groups'''
    for l in scene.landmarks:
        o =PhysicalObject(scene.landmarks[l].uuid,
                       np.array(scene.landmarks[l].representation.middle),
                        np.array(scene.landmarks[l].representation.rect.min_point),
                        np.array(scene.landmarks[l].representation.rect.max_point))
        objects.append(o)
    results = SceneEval.sceneEval(objects)
    return  results
