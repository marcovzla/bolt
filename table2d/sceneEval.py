'''
Created on Jul 22, 2012

@author: colinwinslow
'''
import heapq


def bundleSearch(scene, groups, intersection = 0,beamwidth=10):
    global allow_intersection 
    allow_intersection = intersection
    
    print "number of groups:",len(groups)
    expanded = 0
    singletonCost = 1
    for i in scene:
        groups.append((singletonCost,[i[0]]))
        
    node = BNode(frozenset(), -1, [], 0)
    frontier = PriorityQueue()
    frontier.push(node, 0)
    explored = set()
    while frontier.isEmpty() == False:
        node = frontier.pop()
        expanded += 1
        if node.getState() >= frozenset(map(lambda x:x[0],scene)):
            path = node.traceback()
            print "Expanded",expanded
            return path
        explored.add(node.state)
        successors = node.getSuccessors(scene,groups)
        successors.sort(key= lambda s: s.gainratio,reverse=True)
        successors = successors[0:beamwidth]
        for child in successors:
            if child.state not in explored and frontier.contains(child.state)==False:
                frontier.push(child, child.cost)
            elif frontier.contains(child.state) and frontier.pathCost(child.state) > child.cost:
                
                frontier.push(child,child.cost)  
                
class BNode:
    def __init__(self, state, parent, action, cost):
        self.state = state
        self.parent = parent
        self.action = action
        self.cost = cost
        if parent != -1:
            self.cost = parent.cost + cost
        else:
            self.cost=cost
        self.gain = len(self.state)-self.cost

        if len(self.state)>0:
            self.gainratio = self.gain/len(self.state)
        else: self.gainratio = 0

            
    def getState(self):
        return self.state
    
    def getSuccessors(self, points,groups):
        successors = []
        for g in groups:
            if len(self.state.intersection(g[1]))<=allow_intersection:
                asd=BNode(self.state.union(g[1]),self,g,g[0])
                if asd.gain > 0:
                    successors.append(asd)
        return successors
        

    def traceback(self):
        solution = []
        node = self
        while node.parent != -1:
            solution.append(node.action[1])

            node = node.parent
        cardinality = len(solution)-1 #exclude the first node, which has cost 0
        cost = self.cost#/cardinality
        solution.reverse()
        solution.append(cost)

        return solution
    
class PriorityQueue:
    '''stolen from ista 450 hw ;)'''

    def  __init__(self):  
        self.heap = []
        self.dict = dict()
    
    def push(self, item, priority):
        pair = (priority, item)
        heapq.heappush(self.heap, pair)
        self.dict[item.state]=priority
    
    def contains(self,item):
        return self.dict.has_key(item)
    
    def pathCost(self,item):
        return self.dict.get(item)

    def pop(self):
        (priority, item) = heapq.heappop(self.heap)
        return item
        
    def isEmpty(self):
        return len(self.heap) == 0