# Primary Object class.
# Each object in blender will be passed into this class. Any children are added as child objects.

from xml.etree.ElementTree import SubElement, Element, ElementTree
from .TkSceneNodeData import TkSceneNodeData
from .TkSceneNodeAttributeData import TkSceneNodeAttributeData
from .TkTransformData import TkTransformData
from .TkMaterialData import TkMaterialData
from .List import List
from .Errors import *
from numbers import Number

TYPES = ['MESH', 'LOCATOR', 'COLLISION', 'MODEL', 'REFERENCE']

class Object():
    """ Structure:
    TkSceneNodeData:
        Name
        Type
        Transform (TkTransformData)
        Attributes (List of TkSceneNodeAttributeData). The specific values in this will depend on the Type.
        Children (List of TkSceneNodeData)
    end
    """
    
    def __init__(self, **kwargs):
        self.Transform = kwargs.get('Transform', TkTransformData())     # This will be given as a TkTransformData object.
                                                                        # If this isn't specified the default value will be used.

        self.Attributes = None      # default to None so that it is handled properly if there are none.

        self.Children = []          # just a normal list so it is easier to iterate over
        self.Parent = None          # set to None by default. Every child will have this set to something when it is added as a child.

        self.IsMesh = False         # whether or not something is a mesh. This will be modified when the object is created if required.

        self.NodeData = None

        self.ID = None              # this is a unique number that is used to effectively flatten the mesh data so that it
                                    # can be related to the index in the main function.

        self.provided_streams = set()  # list of provided data streams (only applicable to Mesh type Objects)
        
    def give_parent(self, parent):
        self.Parent = parent

    def populate_meshlist(self, obj):
        # take the obj and pass it all the way up to the Model object and add the object to it's list of meshes
        if self.Parent is not None:
            # in this case we are a child of something, so pass the object up an order...
            self.Parent.populate_meshlist(obj)
        else:
            #... until we hit the Model object who is the only object that has no parent.
            self.ListOfMeshes.append(obj)
            
    def add_child(self, child):
        self.Children.append(child)
        child.give_parent(self)     # give the child it's parent
        if child.IsMesh:
            # if the child has mesh data, we want to pass the reference of the object up to the Model object
            self.populate_meshlist(child)

    def determine_included_streams(self):
        # this will search through the different possible streams and determine which have been provided
        for name in ['Vertices', 'Indexes', 'UVs', 'Normals', 'Tangents']:
            if self.__dict__.get(name, None) is not None:
                self.provided_streams = self.provided_streams.union(set([name]))

    def get_data(self):
        # returns the NodeData attribute
        return self.NodeData

    def construct_data(self):
        # iterate through all the children and create a TkSceneNode for every child with the appropriate properties.
        
        # call each child's process function
        if len(self.Children) != 0:
            self.Child_Nodes = List()
            for child in self.Children:
                child.construct_data()
                self.Child_Nodes.append(child.get_data())      # this will return the self.NodeData object in the child Object
        else:
            self.Child_Nodes = None

        self.NodeData = TkSceneNodeData(Name = self.Name,
                            Type = self._Type,
                            Transform = self.Transform,
                            Attributes = self.Attributes,
                            Children = self.Child_Nodes)
            

        # next, create a TkSceneNodeData object and fill it with data
        # this won't get call until all the child nodes have already had their TkSceneNodeData objects created


class Locator(Object):
    def __init__(self, Name, **kwargs):
        super(Locator, self).__init__(**kwargs)
        self.Name = Name
        self._Type = "LOCATOR"
        self.hasAttachment = kwargs.get('ATTACHMENT', False)

    def create_attributes(self, data):
        if data is not None:
            self.Attributes = List(TkSceneNodeAttributeData(Name = 'ATTACHMENT',
                                                            Value = data['ATTACHMENT']))

class Joint(Object):
    def __init__(self, Name, **kwargs):
        super(Locator, self).__init__(**kwargs)
        self.Name = Name
        self._Type = "JOINT"

    def create_attributes(self, data):
        if data is not None:
            self.Attributes = List(TkSceneNodeAttributeData(Name = 'JOINTINDEX',
                                                            Value = data['JOINTINDEX']))

class Emitter(Object):
    def __init__(self, Name, **kwargs):
        super(Locator, self).__init__(**kwargs)
        self.Name = Name
        self._Type = "EMITTER"

    def create_attributes(self, data):
        if data is not None:
            self.Attributes = List(TkSceneNodeAttributeData(Name = 'MATERIAL',
                                                            Value = data['MATERIAL']),
                                   TkSceneNodeAttributeData(Name = 'DATA',
                                                            Value = data['DATA']))

class Mesh(Object):
    def __init__(self, Name, **kwargs):
        super(Mesh, self).__init__(**kwargs)
        self.Name = Name
        self._Type = "MESH"
        self.Vertices = kwargs.get('Vertices', None)
        self.Indexes = kwargs.get('Indexes', None)
        self.Material = kwargs.get('Material', TkMaterialData(Name="EMPTY"))        # This will be given as a TkMaterialData object
        self.UVs = kwargs.get('UVs', None)
        self.Normals = kwargs.get('Normals', None)
        self.Tangents = kwargs.get('Tangents', None)
        self.IsMesh = True

        self.determine_included_streams()   # find out what streams have been provided

    def create_attributes(self, data):
        # data will be just the information required for the Attributes
        self.Attributes = List(TkSceneNodeAttributeData(Name = 'BATCHSTART',
                                                        Value = data['BATCHSTART']),
                               TkSceneNodeAttributeData(Name = 'BATCHCOUNT',
                                                        Value = data['BATCHCOUNT']),
                               TkSceneNodeAttributeData(Name = 'VERTRSTART',
                                                        Value = data['VERTRSTART']),
                               TkSceneNodeAttributeData(Name = 'VERTREND',
                                                        Value = data['VERTREND']),
                               TkSceneNodeAttributeData(Name = 'FIRSTSKINMAT',
                                                        Value = 0),
                               TkSceneNodeAttributeData(Name = 'LASTSKINMAT',
                                                        Value = 0),
                               TkSceneNodeAttributeData(Name = 'MATERIAL',
                                                        Value = data['MATERIAL']),
                               TkSceneNodeAttributeData(Name = 'MESHLINK',
                                                        Value = self.Name + 'Shape'),
                               TkSceneNodeAttributeData(Name = 'ATTACHMENT',
                                                        Value = data['ATTACHMENT']))
        

class Collision(Object):
    def __init__(self, Name, **kwargs):
        super(Collision, self).__init__(**kwargs)
        self.Name = Name
        self._Type = "COLLISION"
        self.CType = kwargs.get("CollisionType", "Mesh")
        if self.CType == "Mesh":
            # get the relevant bits of data from the kwargs
            self.IsMesh = True
            self.Vertices = kwargs.get('Vertices', None)
            self.Indexes = kwargs.get('Indexes', None)
            self.Material = None
            self.UVs = kwargs.get('UVs', None)
            self.Normals = kwargs.get('Normals', None)
            self.Tangents = kwargs.get('Tangents', None)

            self.determine_included_streams()   # find out what streams have been provided
        else:
            # just give all 4 values. The required ones will be non-zero (deal with later in the main file...)
            self.Width = kwargs.get('Width', 0)
            self.Height = kwargs.get('Height', 0)
            self.Depth = kwargs.get('Depth', 0)
            self.Radius = kwargs.get('Radius', 0)

    def create_attributes(self, data):
        self.Attributes = List(TkSceneNodeAttributeData(Name = "TYPE",
                                                        Value = self.CType))
        if self.CType == 'Mesh':
            self.Attributes.append(TkSceneNodeAttributeData(Name = 'BATCHSTART',
                                                            Value = data['BATCHSTART']))
            self.Attributes.append(TkSceneNodeAttributeData(Name = 'BATCHCOUNT',
                                                            Value = data['BATCHCOUNT']))
            self.Attributes.append(TkSceneNodeAttributeData(Name = 'VERTRSTART',
                                                            Value = data['VERTRSTART']))
            self.Attributes.append(TkSceneNodeAttributeData(Name = 'VERTREND',
                                                            Value = data['VERTREND']))
            self.Attributes.append(TkSceneNodeAttributeData(Name = 'FIRSTSKINMAT',
                                                            Value = 0))
            self.Attributes.append(TkSceneNodeAttributeData(Name = 'LASTSKINMAT',
                                                            Value = 0))
        elif self.CType == 'Box':
            self.Attributes.append(TkSceneNodeAttributeData(Name = "WIDTH",
                                                            Value = data['WIDTH']))
            self.Attributes.append(TkSceneNodeAttributeData(Name = "HEIGHT",
                                                            Value = data['HEIGHT']))
            self.Attributes.append(TkSceneNodeAttributeData(Name = "DEPTH",
                                                            Value = data['DEPTH']))
        elif self.CType == 'Sphere':
            self.Attributes.append(TkSceneNodeAttributeData(Name = "RADIUS",
                                                            Value = data['RADIUS']))
        elif self.CType == 'Capsule' or self.CType == 'Cylinder':
            self.Attributes.append(TkSceneNodeAttributeData(Name = "RADIUS",
                                                            Value = data['RADIUS']))
            self.Attributes.append(TkSceneNodeAttributeData(Name = "HEIGHT",
                                                            Value = data['HEIGHT']))

class Model(Object):
    def __init__(self, Name, **kwargs):
        super(Model, self).__init__(**kwargs)
        self.Name = Name
        self._Type = "MODEL"

        self.ListOfMeshes = []      # this is a list of all the MESH objects or collisions of type MESH so that we can easily access it.
                                    # The list will be automatically populated when a child is added to any children of this object.

    def create_attributes(self, data):
        # data will be just the information required for the Attributes
        self.Attributes = List(TkSceneNodeAttributeData(Name = 'GEOMETRY',
                                                        Value = data['GEOMETRY']))
        

class Reference(Object):
    def __init__(self, Name, **kwargs):
        # this will need to recieve SCENEGRAPH as an argument to be used.
        # Hopefully this casn be given by blender? Maybe have the user enter it in or select the path from a popup??
        super(Reference, self).__init__(**kwargs)
        self.Name = Name
        self._Type = "REFERENCE"

        self.Scenegraph = kwargs.get("Scenegraph", "Enter in the path of the SCENE.MBIN you want to reference here.")


    def create_attributes(self, data):
        self.Attributes = List(TkSceneNodeAttributeData(Name = 'SCENEGRAPH',
                                                        Value = self.Scenegraph))
