from planar import Vec2, BoundingBox
from collections import namedtuple
import numpy as np
import chainfinder



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
    results = chainfinder.findChains(objects)[0:-1]#trim the score from the end of the list
    for r in range(len(results)):
        for s in range(len(results[r])):
            results[r][s] = scene.fetch_landmark(results[r][s])
    return results
