from Tkinter import *
from collections import namedtuple
import chainfinder
import numpy as np
import pickle
import tkFileDialog

CParams = namedtuple("ChainParams",['distance_limit', 'angle_limit', 'min_line_length',
               'anglevar_weight', 'distvar_weight','dist_weight',
               'allow_intersection'])


class PlaygroundWindow:
    def __init__(self,master):
        
        self.dragOrigin = []
        frame = Frame(master)
        frame.pack()
        
        self.pathfinding_active = 1
        self.allow_intersection = IntVar()
        self.allow_intersection.set(0)
        #algorithm parameters

        
        #variables
        varFrame = Frame(frame,relief=SUNKEN,borderwidth=2,width=2,)
        self.distance_limit=StringVar()
        self.distance_limit.set("1")
        self.angle_limit=StringVar()
        self.angle_limit.set(".9")
        self.min_line_length=StringVar()
        self.min_line_length.set("3")
        self.anglevar_weight=StringVar()
        self.anglevar_weight.set(".1")
        self.distvar_weight=StringVar()
        self.distvar_weight.set(".1")
        self.dist_weight=StringVar()
        self.dist_weight.set("depricated")

        
        sceneFrame = Frame(frame,relief=SUNKEN,borderwidth=2,width=2,)
        self.intersect_checkbox = Checkbutton(sceneFrame,text="Allow Intersecting Lines",variable = self.allow_intersection).pack()
        
        
        
        distvar_limit_label = Label(varFrame, text="Distance Limit:", anchor=W).pack()
        self.distvar_limit_field = Entry(varFrame, width=5,textvariable=self.distance_limit).pack()
        
        angle_limit_label = Label(varFrame, text="Angle Limit:", anchor=W).pack()
        self.angle_limit_field = Entry(varFrame, width=5,textvariable=self.angle_limit).pack()
        
        length_limit_label = Label(varFrame, text="Min Length:", anchor=W).pack()
        self.length_limit_field = Entry(varFrame, width=5,textvariable=self.min_line_length).pack()
    
        
        distvar_weight_label = Label(varFrame, text="Distance Var Weight:", anchor=W).pack()
        self.distvar_weight_field = Entry(varFrame, width=5,textvariable=self.distvar_weight).pack()
        
        angle_weight_label = Label(varFrame, text="Angle Weight:", anchor=W).pack()
        self.length_weight_field = Entry(varFrame, width=5,textvariable=self.anglevar_weight).pack()
        
        search = Button(varFrame,text="Find Lines!",command=self.research)
        search.pack()
        
        open_button = Button(varFrame,text="Load Scene",command=self.openScene)
        open_button.pack()
        
        save_button = Button(varFrame,text="Save Scene",command=self.saveScene)
        save_button.pack()
        #viewport
        viewport = Frame(frame,relief=SUNKEN,borderwidth=2,width=500,height=500)
        self.c = Canvas(viewport,width=500,height=500,confine=True)
        self.c.pack()

        varFrame.pack(side=LEFT,padx=2, pady=2)
        sceneFrame.pack(side=BOTTOM,padx=2, pady=2)
        self.c.bind("<Button-1>", self.mousedown)
        self.c.bind("<B1-Motion>", self.mousedrag)
#        self.c.bind("<ButtonRelease-1>", self.mouseup)
        self.c.bind("<ButtonRelease-2>", self.leftclick)
        self.c.bind("<Double-Button-1>", self.doubleclick)
        viewport.pack(padx=2, pady=2)
        
    def mousedown(self,event):
        self.c.delete("line")
        self.dragOrigin=[event.x,event.y]
        
        
    def mousedrag(self,event):
        self.c.move("current",event.x-self.dragOrigin[0],event.y-self.dragOrigin[1])
        self.dragOrigin = [event.x,event.y]

#    def mouseup(self,event):
#        self.research()

        
    def leftclick(self,event):
        self.c.delete("line")
        self.c.delete("current")


    def doubleclick(self,event):
        self.c.create_oval(event.x-10,event.y-10,event.x+10,event.y+10,fill="red")


    def research(self):
        params = CParams(eval(self.distance_limit.get()),
                         eval(self.angle_limit.get()),
                         eval(self.min_line_length.get()),
                         eval(self.anglevar_weight.get()),
                         eval(self.distvar_weight.get()),
                         1,
                         self.allow_intersection.get()
                         )
        self.c.delete("line")
        searchMe = []
        for o in self.c.find_all():
            searchMe.append(PhysicalObject(o,np.array(self.c.coords(o)),0,0))
        results = chainfinder.findChains(searchMe,params.distance_limit,params.angle_limit,params.min_line_length,
                                         params.anglevar_weight,params.distvar_weight,params.dist_weight,params.allow_intersection)
        if len(results)>0:
            self.chainViz(results)
            
        
            
    def chainViz(self,chains):

        self.c.delete("line")
        color = "green"
        weight = 4
        print "chains",chains
        
    def saveScene(self):
        params = tuple([eval(self.distance_limit.get()),
                         eval(self.angle_limit.get()),
                         eval(self.min_line_length.get()),
                         eval(self.anglevar_weight.get()),
                         eval(self.distvar_weight.get()),
                         1,
                         self.allow_intersection.get()
                         ])
        self.c.delete("line")
        filename = tkFileDialog.asksaveasfilename()
        f=open(filename,'w')
        dots = map(self.c.coords,self.c.find_all())
        output = (params,dots)
        print output
        pickledCanvas = pickle.dump(output, f)
        f.close()
        
    def openScene(self):
        all = self.c.find_all()
        self.c.delete('all')
        filename = tkFileDialog.askopenfilename()
        f=open(filename,'r')
        unpickled=pickle.load(f)
        
        self.distance_limit.set(str(unpickled[0][0]))
        self.angle_limit.set(str(unpickled[0][1]))
        self.min_line_length.set(str(unpickled[0][2]))
        self.anglevar_weight.set(str(unpickled[0][3]))
        self.distvar_weight.set(str(unpickled[0][4]))
        self.allow_intersection.set(unpickled[0][6])
        
        for o in unpickled[1]:
            self.c.create_oval(o[0],o[1],o[2],o[3],fill="red")
        f.close()
        
        
        
    def chainViz(self,chains):
        self.c.delete("line")
        color1 = "#00FF00"
        color2 = "#00bb00"
        color = color1
        weight = 4
        for c in chains[:-1]:
            for o in range(len(c)-1):
                if color == color1: color=color2
                else: color = color1
                linePts = self.c.coords(c[o])[0:2]+self.c.coords(c[o+1])[0:2]
                linePts = map(int,linePts)
                linePts = map(lambda x: x+10,linePts)
                self.c.create_line(linePts,fill=color,tags="line",width=weight) 
            
            
#    def chainViz(self,chains):
#        rank = 0
#        self.c.delete("line")
#        
#        for c in chains:
#
#            if rank ==0: 
#                color = "green"
#                weight = 4
#
#            elif rank == 1: 
#                color = "orange"
#                weight = 2
#            elif rank == 2: 
#                color = "red"
#                weight = 1
#            if rank < 3:
#                for o in range(len(c[1])-1):
#                    linePts = self.c.coords(c[1][o])[0:2]+self.c.coords(c[1][o+1])[0:2]
#                    linePts = map(int,linePts)
#                    linePts = map(lambda x: x+10,linePts)
#                    self.c.create_line(linePts,fill=color,tags="line",width=weight) 
#            rank += 1
            
        
        
    
root = Tk(className=" Chainfinder Playground ")

PhysicalObject = namedtuple('physicalObject', ['id', 'position', 'bbmin', 'bbmax'])






app = PlaygroundWindow(root)

root.mainloop()
