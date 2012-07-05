from landmark import *
from matplotlib import pyplot as plt
from relations import relations
from numpy import array,random,arange


class Scene(object):
	def __init__(self):
		self.landmarks = {}
		self.landmarks['table'] = Landmark('table', RectangleRepresentation(  BoundingBox( [Vec2(5,5),Vec2(6,7)] ),['table']  ),None,['table'])
		self.landmarks['obj1']  = Landmark('blue cup', RectangleRepresentation(  BoundingBox( [Vec2(5,5),Vec2(5.1,5.1)] )  ),None,['blue cup'])
		self.landmarks['obj2']  = Landmark('bottle', RectangleRepresentation(  BoundingBox( [Vec2(5.5,6),Vec2(5.6,6.1)] )  ),None,['bottle'])




def visualize(scene):

	plt.figure( figsize=(10,5) )
	plt.subplot(1,2,1)
	plt.axis([4.3,6.7,4.5,7.5])

	for lmk in scene.landmarks.values():

		if isinstance(lmk.representation, RectangleRepresentation):
			rect = lmk.representation.rect
			xs = [rect.min_point.x,rect.min_point.x,rect.max_point.x,rect.max_point.x]
			ys = [rect.min_point.y,rect.max_point.y,rect.max_point.y,rect.min_point.y]
			plt.fill(xs,ys,facecolor='none',linewidth=2)



	location = Vec2(random.random()+5,random.random()*2+5)

	plt.plot(location.x,location.y,'rx',markeredgewidth=2)

	table = scene.landmarks['table'].representation

	representations = [table]
	representations.extend(table.get_alt_representations())

	epsilon = 0.000001
	landmarks_distances = []
	for representation in representations:
	    for lmk in representation.get_landmarks():
	        landmarks_distances.append([lmk, lmk.distance_to(location)])

	for lmk in scene.landmarks.values():
		landmarks_distances.append( [lmk, lmk.distance_to(location)] )

	landmarks, distances = zip( *landmarks_distances )
	scores = 1.0/(array(distances)**1.5 + epsilon)
	lm_probabilities = scores/sum(scores)
	index = lm_probabilities.cumsum().searchsorted( random.sample(1) )[0]
	sampled_landmark = landmarks[index]
	distance = distances[index]

	print sampled_landmark

	if isinstance(sampled_landmark.representation, PointRepresentation):
		plt.plot(sampled_landmark.representation.location.x,
				 sampled_landmark.representation.location.y,
				 'r.',markeredgewidth=2)
	elif isinstance(sampled_landmark.representation, LineRepresentation):
		xs = [sampled_landmark.representation.line.start.x,sampled_landmark.representation.line.end.x]
		ys = [sampled_landmark.representation.line.start.y,sampled_landmark.representation.line.end.y]
		plt.fill(xs,ys,facecolor='none',edgecolor='red',linewidth=2)
	elif isinstance(sampled_landmark.representation, RectangleRepresentation):
		rect = sampled_landmark	.representation.rect
		xs = [rect.min_point.x,rect.min_point.x,rect.max_point.x,rect.max_point.x]
		ys = [rect.min_point.y,rect.max_point.y,rect.max_point.y,rect.min_point.y]
		plt.fill(xs,ys,facecolor='none',edgecolor='red',linewidth=2)


	rel_scores = []
	for relation in relations:
	    rel_scores.append( relation.probability(location, sampled_landmark) )
	rel_scores = array(rel_scores)
	rel_probabilities = rel_scores/sum(rel_scores)
	index = rel_probabilities.cumsum().searchsorted( random.sample(1) )[0]
	sampled_relation = relations[index]

	toprint = str(location)+' ; '+sampled_relation.get_description() + " " + sampled_landmark.get_description()
	print toprint
	plt.suptitle(toprint)


	plt.subplot(2,2,2)
	plt.axis([0,1.5,-0.1,1.1])

	xs = arange(0,3,0.01)
	ys = {}
	for relation in relations:
		name = relation.__class__.__name__
		plt.plot( xs, relation.distance_probability(xs) )
	plt.axvline(x=distance,linewidth=2)
	print distance


	plt.show()


if __name__ == '__main__':
	scene = Scene()
	visualize(scene)