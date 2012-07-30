from planar import Vec2

def adapt(scene):
    print "***"
    for l in scene.landmarks:
        print scene.landmarks[l].representation.middle, scene.landmarks[l].representation.rect