import os
import bpy
from bpy.types import NodeTree, Node, NodeSocket, NodeSocketFloat, Operator
from bpy.props import *
import inspect
import json
import mathutils
import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem
from .pixel_collection import PIXEL_COLLECTION
from .pixel_stored_functions import functions_dict

PIX_PREFIX = "pix_"
PIX_ID = "pix_id"
PIX_ID_DUPS = "pix_id_dups"
PIX_PROPERTIES = "pix_properties"


# Define Custom Node Tree
class PixelNodeTree(NodeTree):
    bl_idname = 'PixelTreeType'
    bl_label = 'Pixel Symphony Nodes'
    bl_icon = 'NODETREE'

    def execute(self, context):
        for node in self.nodes:
            node.execute(context)

# Base Node Class
class PixelBaseNode:
    @classmethod
    def poll(cls, ntree):
        print(ntree.bl_idname)
        return ntree.bl_idname == 'PixelTreeType'

    def execute(self, context):
        pass

# Custom node type to get object location
class PixelSymphonyLocationNode(Node):
    bl_idname = 'PixelSymphonyLocationNode'
    bl_label = 'Object Location Node'
    bl_icon = 'SOUND'

    def init(self, context):
        self.inputs.new('NodeSocketString', "Object ID")
        self.outputs.new('NodeSocketVector', "Location")

    def update(self):
        if self.inputs['Object ID'].is_linked:
            object_id = self.inputs['Object ID'].default_value
            print(f"Received object ID: {object_id}")
            if object_id:
                obj = bpy.data.objects.get(object_id)
                if obj:
                    location = obj.location
                    self.outputs['Location'].default_value = location
                    print(f"Object location: {location}")
                    for link in self.outputs['Location'].links:
                        to_socket = link.to_socket
                        to_socket.default_value = location
                        print(f"Updated linked node location: {location}")

# Custom node type for Pixel Symphony
class PixelSymphonyNode(Node):
    bl_idname = 'PixelSymphonyNode'
    bl_label = 'Pixel Symphony Node'
    bl_icon = 'SOUND'

    def init(self, context):
        self.outputs.new('NodeSocketString', "Object ID")
        self.selected_object = None

    def draw_buttons(self, context, layout):
        layout.prop(self, 'selected_object', text='Object')

    def update(self):
        if self.outputs['Object ID'].is_linked:
            if self.selected_object:
                self.object_id = self.selected_object.name
            else:
                self.object_id = ""

            for link in self.outputs['Object ID'].links:
                to_socket = link.to_socket
                to_socket.default_value = self.object_id
                print(f"Updated linked node input with object ID: {self.object_id}")

    selected_object: bpy.props.PointerProperty(
        name="Object",
        type=bpy.types.Object,
        update=lambda self, context: self.update()
    )
    object_id: bpy.props.StringProperty()


# Function to update the list of objects
def update_object_items(self, context):
    items = [(obj.name, obj.name, "") for obj in bpy.context.scene.objects]
    if not items:
        items.append(('None', 'None', ''))
    return items


# Function to project a 3D point to the image plane
def project_3d_point_to_image(camera, point):
    # Get the camera's intrinsic matrix
    scene = bpy.context.scene
    render = scene.render
    camera_data = camera.data

    # Intrinsic parameters
    f_in_mm = camera_data.lens
    sensor_width_in_mm = camera_data.sensor_width
    sensor_height_in_mm = camera_data.sensor_height

    resolution_x_in_px = render.resolution_x
    resolution_y_in_px = render.resolution_y
    scale = render.resolution_percentage / 100
    resolution_x_in_px = scale * resolution_x_in_px
    resolution_y_in_px = scale * resolution_y_in_px

    pixel_aspect_ratio = render.pixel_aspect_x / render.pixel_aspect_y

    # Focal length in pixels
    f_x = (f_in_mm / sensor_width_in_mm) * resolution_x_in_px
    f_y = (f_in_mm / sensor_height_in_mm) * resolution_y_in_px / pixel_aspect_ratio

    # Principal point in pixels
    c_x = resolution_x_in_px / 2
    c_y = resolution_y_in_px / 2

    # Camera intrinsic matrix
    K = mathutils.Matrix(((f_x, 0, c_x, 0),
                          (0, f_y, c_y, 0),
                          (0, 0, 1, 0),
                          (0, 0, 0, 1)))

    # Convert the point from world coordinates to camera coordinates
    point_world = mathutils.Vector(point)
    point_camera = camera.matrix_world.inverted() @ point_world

    # Homogeneous coordinates
    point_camera_homogeneous = mathutils.Vector((point_camera.x, point_camera.y, point_camera.z, 1))

    # Project the point onto the image plane using the intrinsic matrix
    point_image_homogeneous = K @ point_camera_homogeneous

    # Normalize homogeneous coordinates
    point_image = mathutils.Vector((point_image_homogeneous.x / point_image_homogeneous.z,
                                    point_image_homogeneous.y / point_image_homogeneous.z, 0))

    return point_image

class PixelSymphonyCharacterNode(Node, PixelBaseNode):
    bl_idname = 'PixelSymphonyCharacterNode'
    bl_label = 'Collect information for character'
    bl_icon = 'SOUND'
    def init(self, context):
        self.inputs.new('NodeSocketString', "Camera ID")
        self.inputs.new('NodeSocketString', "Object ID")
        self.inputs.new('NodeSocketString', "Height Object ID")
        self.outputs.new('CharacterSocketType', "Character")

    def update(self):
        if self.inputs['Camera ID'].is_linked and self.inputs['Object ID'].is_linked and self.inputs['Height Object ID'].is_linked:
            camera_id = self.inputs['Camera ID'].default_value
            object_id = self.inputs['Object ID'].default_value
            height_object_id = self.inputs['Height Object ID'].default_value

            print(f"Received camera ID: {camera_id}")
            print(f"Received object ID: {object_id}")
            print(f"Received object ID: {height_object_id}")

            camera = bpy.data.objects.get(camera_id)
            obj = bpy.data.objects.get(object_id)
            height_object = bpy.data.objects.get(height_object_id)

            if camera and obj and height_object:
                location = obj.location
                projected_point = project_3d_point_to_image(camera, obj.location)
                height_projected_point = project_3d_point_to_image(camera, height_object.location)
                distance = (camera.location - location).length

                character = bpy.context.scene.character_property_groups.add()
                character.x = location.x
                character.y = location.y
                character.z = location.z
                character.distance = distance

                self.outputs['Character'].default_value.x = character.x
                self.outputs['Character'].default_value.y = character.y
                self.outputs['Character'].default_value.z = character.z
                self.outputs['Character'].default_value.distance = character.distance
                self.outputs['Character'].default_value.object_id = object_id
                self.outputs['Character'].default_value.camera_id = camera_id
                self.outputs['Character'].default_value.project_x = projected_point[0]
                self.outputs['Character'].default_value.project_y = projected_point[1]
                self.outputs['Character'].default_value.top_x = height_projected_point[0]
                self.outputs['Character'].default_value.top_y = height_projected_point[1]

                print(f"Character info: {character.to_dict()}")

# Custom node type to project a 3D point to the image plane
class PixelSymphonyProjectionNode(Node, PixelBaseNode):
    bl_idname = 'PixelSymphonyProjectionNode'
    bl_label = '3D to 2D Projection Node'
    bl_icon = 'SOUND'

    def init(self, context):
        self.inputs.new('NodeSocketString', "Camera ID")
        self.inputs.new('NodeSocketVector', "Location")
        self.outputs.new('NodeSocketVector', "2D Coordinates")

    def update(self):
        if self.inputs['Camera ID'].is_linked and self.inputs['Location'].is_linked:
            camera_id = None
            location = None

            camera_id = self.inputs['Camera ID'].default_value
            print(f"Updated camera_id: {camera_id}")
            for link in self.inputs['Location'].links:
                location = link.from_socket.default_value
                print(f"Updated location: {location}")

            if camera_id and location:
                camera = bpy.data.objects.get(camera_id)
                if camera and camera.type == 'CAMERA':
                    projected_point = project_3d_point_to_image(camera, location)
                    print(f"projected_point: {projected_point}" )
                    self.outputs['2D Coordinates'].default_value = projected_point
                    for link in self.outputs['2D Coordinates'].links:
                        to_socket = link.to_socket
                        to_socket.default_value = projected_point
                        print(f"Updated  projected_point: {projected_point}")

    camera_id: bpy.props.StringProperty(
        name="Camera",
        description="Type the name of the camera",
        update=lambda self, context: self.update_camera_id(context)
    )
    location: bpy.props.FloatVectorProperty(
        name="Location",
        description="3D location to project",
        size=2,
        update=lambda self, context: self.update_location(context)
    )

    def update_camera_id(self, context):
        self.update()

    def update_location(self, context):
        self.update()


# Function to write location to a file as JSON
def write_location_to_file(file_path, location):
    data = {
        "location": {
            "x": location[0],
            "y": location[1]
        }
    }
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

# Custom property group to represent a location with multiple properties
class CharacterPropertyGroup(bpy.types.PropertyGroup):
    x: bpy.props.FloatProperty(name="X")
    y: bpy.props.FloatProperty(name="Y")
    z: bpy.props.FloatProperty(name="Z")
    object_id: bpy.props.StringProperty(name="Object Id")
    camera_id: bpy.props.StringProperty(name="Camera Id")
    project_x: bpy.props.FloatProperty(name="Project X")
    project_y: bpy.props.FloatProperty(name="Project Y")
    top_x: bpy.props.FloatProperty(name="Top X")
    top_y: bpy.props.FloatProperty(name="Top Y")
    distance: bpy.props.FloatProperty(name="Distance")

    def to_dict(self):
        return {
            "x": self.x, 
            "y": self.y, 
            "z": self.z, 
            "distance": self.distance, 
            "project_x": self.project_x, 
            "project_y": self.project_y, 
            "top_x": self.top_x, 
            "top_y": self.top_y, 
            "object_id": self.object_id, 
            "camera_id": self.camera_id
        }

# Custom socket type for CharacterPropertyGroup
class CharacterSocket(NodeSocket):
    bl_idname = 'CharacterSocketType'
    bl_label = 'Character Socket'

    # Property to hold the CharacterPropertyGroup
    default_value: bpy.props.PointerProperty(type=CharacterPropertyGroup)

    def draw(self, context, layout, node, text):
        layout.label(text=self.name)

    def draw_color(self, context, node):
        return (1.0, 0.4, 0.216, 0.5)

    def get_value(self):
        return self.default_value

    def set_value(self, value):
        self.default_value = value
# Define a global variable to store the frames with keyframes
keyframed_frames = []

def get_keyframed_frames():
    keyframes = set()
    
    # Iterate through all objects in the scene
    for obj in bpy.context.scene.objects:
        # Check if the object has animation data
        if obj.animation_data:
            # Get the action (which contains the keyframes)
            action = obj.animation_data.action
            if action:
                # Iterate through all FCurves in the action
                for fcurve in action.fcurves:
                    # Iterate through all keyframe points in the FCurve
                    for keyframe in fcurve.keyframe_points:
                        keyframes.add(int(keyframe.co.x))
    
    # Sort the frames
    sorted_keyframes = sorted(keyframes)
    
    global keyframed_frames
    keyframed_frames = sorted_keyframes

# Register the frame change handler
def frame_change_handler(scene):
    get_keyframed_frames()
    update_character_nodes(scene)
bpy.app.handlers.frame_change_pre.append(frame_change_handler)

def update_character_nodes(scene):
    for node_tree in bpy.data.node_groups:
        for node in node_tree.nodes:
            if isinstance(node, PixelSymphonyCharacterNode):
                node.update()

# Custom node type to write location to a file as JSON
class PixelSymphonyWriteToFileNode(Node, PixelBaseNode):
    bl_idname = 'PixelSymphonyWriteToFileNode'
    bl_label = 'Write Character Data to File Node'
    bl_icon = 'SOUND'

    def init(self, context):
        self.inputs.new('NodeSocketString', "File Path")
        character_data = self.inputs.new('CharacterSocketType', "Character Data")
        character_data.link_limit = 10
        character_data.display_shape = 'SQUARE_DOT'

    def draw_buttons(self, context, layout):
        layout.operator("node.write_location_to_file", text="Write Character Data to File")

    def update(self):
        pass

    file_path: bpy.props.StringProperty(
        name="File Path",
        description="Path to the output file",
        update=lambda self, context: self.update()
    )
    characters: bpy.props.PointerProperty(type=CharacterPropertyGroup)

    def update_location(self, context):
        self.update()

    def get_linked_character_data(self):
        locations = []
        if self.inputs['Character Data'].is_linked:
            for link in self.inputs['Character Data'].links:
                from_socket = link.from_socket
                loc_vector = from_socket.get_value()
                locations.append(loc_vector)
        return locations

# Function to serialize characters to file
def serialize_characters_to_file(file_path, characters):
    current_frame = bpy.context.scene.frame_current
    data = {}
    
    # Check if file exists
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
    
    # Ensure 'frames' key exists
    if 'frames' not in data:
        data['frames'] = {}
    
    # Add or update the current frame's data
    data['frames'][str(current_frame)] = {"characters": [char.to_dict() for char in characters]}

    # Write the updated data back to the file
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

# Handler to write character data on render complete
def write_character_data_on_render(scene):
    for node_tree in bpy.data.node_groups:
        for node in node_tree.nodes:
            if isinstance(node, PixelSymphonyWriteToFileNode):
                file_path = node.file_path
                characters = node.get_linked_character_data()
                if file_path and characters:
                    current_frame = bpy.context.scene.frame_current
                    if current_frame in keyframed_frames:
                        print(keyframed_frames)
                        serialize_characters_to_file(file_path, characters)
                        print(f"Character data written to {file_path} on render")

# Operator to write location to file
class WRITE_OT_location_to_file(Operator):
    bl_idname = "node.write_location_to_file"
    bl_label = "Write Character Data to File"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        node = context.node
        file_path = node.inputs['File Path'].default_value
        locations = node.get_linked_character_data()
        if file_path and locations:
            current_frame = bpy.context.scene.frame_current
            if current_frame in keyframed_frames:
                print(keyframed_frames)
                self.write_location_to_file(file_path, locations)
                self.report({'INFO'}, f"Locations written to {file_path}")
        else:
            self.report({'WARNING'}, "Invalid file path or locations")
        return {'FINISHED'}
    def write_location_to_file(self, file_path, locations):
        serialize_characters_to_file(file_path, locations)

class WRITE_OT_location_to_file(Operator):
    bl_idname = "node.write_location_to_file"
    bl_label = "Write Character Data to File"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        node = context.node
        file_path = node.inputs['File Path'].default_value
        if file_path:
            current_frame = bpy.context.scene.frame_current
            scene = bpy.context.scene
            start_frame = scene.frame_start
            end_frame = scene.frame_end

            for frame in range(start_frame, end_frame + 1):
                if current_frame in keyframed_frames:
                    scene.frame_set(frame)
                    locations = node.get_linked_character_data()
                    if locations:
                        serialize_characters_to_file(file_path, locations)
            
            # Return to the original frame
            scene.frame_set(current_frame)
            self.report({'INFO'}, f"Locations written to {file_path}")
        else:
            self.report({'WARNING'}, "Invalid file path or locations")
        return {'FINISHED'}
# Custom socket type
class PixelCustomSocket(NodeSocketFloat):
    # Description string
    bl_idname = 'PixelCustomSocket'
    bl_label = "Pixel Custom Node Socket"

    # Property to store JSON data as string
    json_data: bpy.props.StringProperty()
    json_path_data: bpy.props.StringProperty()
    json_float_data: bpy.props.FloatProperty(default=0.0)

    # Override init function to add update callback
    def init(self, context):
        self.update = self.update_socket
    # Optional function for drawing the socket input value
    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text=f"{text}")
        else:
            # Use the socket's name as the display text
            display_text = text
            # Optionally, display a shortened version of the JSON data if it's set
            if self.json_data:
                display_text = (self.json_data[:50] + '...') if len(self.json_data) > 50 else self.json_data
            layout.label(text=f"{display_text}")

            # Add a UI field to edit the float value
            layout.prop(self, "json_float_data", text="Float Value")

    def update_socket(self, context):
        """
        Update function for this socket, triggered on link connection changes.
        """
        if self.is_linked:
            # When socket is connected, set json_path_data from the connected socket's node
            connected_socket = self.links[0].from_socket
            self.json_path_data = getattr(connected_socket.node, 'json_path_data', '')
        else:
            # Reset json_path_data when socket is disconnected
            self.json_path_data = ''
        # This function is called whenever the socket is updated
        self.node.update()  # Calls the update method of the node this socket belongs to


    # Socket color
    def draw_color(self, context, node):
        return (1.0, 0.4, 0.216, 0.5)


# Custom Nodes
class PixelNodeText(Node, PixelBaseNode):
    bl_label = 'Pixel Text'
    bl_idname = 'PixelNodeText'

    def init(self, context):
        self.outputs.new('PixelCustomSocket', 'Text')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'text')

    def execute(self, context):
        self.outputs['Text'].default_value = self.text

    text: bpy.props.StringProperty(name='', update=execute)

def find_unique_pix_properties():
    unique_properties = set()
    try:
        # Go through all collections
        for collection in bpy.data.collections:
            # Check if the collection has the custom PIX_ID
            if PIXEL_COLLECTION in collection.keys():
                # Go through each object in the collection
                for obj in collection.objects:
                    # Check if the object has the pix_properties custom property
                    if "pix_properties" in obj.keys():
                        properties = obj["pix_properties"].split(',')
                        unique_properties.update(properties)

                    # Go through each material of the object
                    try:
                        for mat in obj.data.materials:
                            if mat is not None and mat.node_tree is not None:
                                # Go through each node in the material
                                for node in mat.node_tree.nodes:
                                    # Check if the node has the pix_properties custom property
                                    if "pix_properties" in node.keys():
                                        properties = node["pix_properties"].split(',')
                                        unique_properties.update(properties)
                    except Exception as e:
                        pass
    except Exception as e:
        print("Exception occurred:", e)
        return None

    # Return a set of unique pix_properties
    return unique_properties

def get_pix_properties_items(self, context):
    pix_props = find_unique_pix_properties()
    if pix_props == None:
        print("no pix props found")
        return [("Nothing", 'Nothing', 'Nothing')]
    return [(i, i, i) for i in pix_props]

class PixelNodeMath(Node, PixelBaseNode):
    bl_idname = 'PixelNodeMath'
    bl_label = 'Pixel Math Node'
    # Custom float property with min and max
    start: bpy.props.FloatProperty(
        name="Star",
        description="A float property with min and max",
        min=0.0,
        max=1.0,
        default=0.0,
    )
    # Custom float property with min and max
    end: bpy.props.FloatProperty(
        name="Star",
        description="A float property with min and max",
        min=0.0,
        max=1.0,
        default=1.0,
    )

    pixproperty: bpy.props.EnumProperty(
        name="Pix Properties",
        description="Choose pix properties",
        items=get_pix_properties_items,
        default=0
    )

    def init(self, context):
        self.inputs.new('PixelCustomSocket', 'Track')
        self.inputs.new('PixelCustomSocket', 'Note')
        self.inputs.new('PixelCustomSocket', 'Midi')
        self.inputs.new('PixelCustomSocket', 'Value')
        self.inputs.new('PixelCustomSocket', 'Duration')
        self.inputs.new('PixelCustomSocket', 'Time')

    def draw_buttons(self, context, layout):
        layout.prop(self, "pixproperty", text="")
        layout.prop(self, "start", text="Start")
        layout.prop(self, "end", text="End")

    def update(self):
        try:
            pass
        except Exception as e:
            self.label = str(e)

class PixelFunction(Node):
    bl_idname = 'PixelFunction'
    bl_label = 'Pixel Function'

    
    def update_sockets(self, context):
        selected_func = functions_dict.get(self.selected_function)

        # Clear existing input sockets
        for socket in self.inputs:
            self.inputs.remove(socket)

        # Create new sockets based on the function's parameters
        if selected_func:
            params = inspect.signature(selected_func).parameters
            for param_name in params.keys():
                new_socket = self.inputs.new('PixelCustomSocket', param_name)
                new_socket.update = new_socket.update_socket  # Set update function

    selected_function: bpy.props.EnumProperty(
        name="Function",
        description="Choose a function",
        items=[(name, name, "") for name in functions_dict.keys()],
        update=update_sockets
    )
    def init(self, context):
        self.outputs.new('PixelCustomSocket', "Output")  # Example output socket

    def draw_buttons(self, context, layout):
        layout.prop(self, "selected_function")



class PixelNodeJSONData(bpy.types.Node, PixelBaseNode):
    bl_label = 'JSON Data'
    bl_idname = 'PixelNodeJSONData'
    path_data: bpy.props.StringProperty(name='')
    stored_data: bpy.props.StringProperty(name='')

    def init(self, context):
        self.inputs.new('PixelCustomSocket', 'Data')

    def draw_buttons(self, context, layout):
        layout.label(text="Input JSON or use scene's data")

    def update_sockets_from_json(self, json_data, json_path_data):
        existing_sockets = {sock.name: sock for sock in self.outputs}

        try:
            print("update_sockets_from_json")

            self.path_data = json_path_data
            if not json_data:
                json_data = self.stored_data
            if isinstance(json_data, str):
                print("deserialize json")
                data = json.loads(json_data)
                self.stored_data = json_data
            else:
                print("already json")
                self.stored_data = json.dump(json_data)
                data = json_data
            
            print("required_sockets")
            required_sockets = set()
            if isinstance(data, dict):
                print("is dict")
                for key, value in data.items():
                    print(f"key {key}")
                    required_sockets.add(key)
                    if key not in existing_sockets:
                        self.create_socket(key, value, f"{self.path_data}.{key}")
                    else:
                        # Update existing socket value
                        self.update_socket_value(existing_sockets[key], value, f"{self.path_data}.{key}")
            elif isinstance(data, list) and data:
                print("is array")
                required_sockets.add("Array")
                if "Array" not in existing_sockets:
                    self.create_socket("Array", data[0], f"{self.path_data}.[]")
                else:
                    # Update existing socket value
                    self.update_socket_value(existing_sockets["Array"], data[0], f"{self.path_data}.[]")
            else:
                print("not expected type")
            # Remove sockets that are no longer needed
            for socket_name in existing_sockets.keys() - required_sockets:
                self.outputs.remove(existing_sockets[socket_name])

        except json.JSONDecodeError:
            print('failed to parse json')
            print(json_data)
            pass  # Handle JSON parsing error if needed

    def create_socket(self, name, value, json_path_data):
        # Determine the type of the value and create an appropriate socket
        socket = self.outputs.new('PixelCustomSocket', name)
        socket.json_path_data = json_path_data
        socket.json_data = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
        return socket

    def update_socket_value(self, socket, value, json_path_data):
        # Update the value of the socket based on the data type
        if isinstance(value, str):
            socket.json_data = value
        elif isinstance(value, (int, float)):
            socket.json_float_data = float(value)
        else:
            socket.json_data = json.dumps(value)
        socket.json_path_data = json_path_data
        return socket
    def process_json_data(self, context):
        input_socket = self.inputs['Data']
        json_data = "{}"
        if input_socket.is_linked and input_socket.links:
            print("using linked data")
            linked_socket = input_socket.links[0].from_socket
            json_data = linked_socket.json_data 
            json_path_data = linked_socket.json_path_data
        else:
            json_data = context.scene.get('raw_json_data', "{}")
            json_path_data = "$"
        self.update_sockets_from_json(json_data, json_path_data)

    def update(self):
        self.process_json_data(bpy.context)

class PixelNodeFloat(Node, PixelBaseNode):
    bl_label = 'Float'
    bl_idname = 'PixelNodeFloat'

    def init(self, context):
        self.outputs.new('NodeSocketFloat', 'Float')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'float')

    def execute(self, context):
        self.outputs['Float'].default_value = self.float

    float: bpy.props.FloatProperty(name='', update=execute)

class PixelNodePrint(Node, PixelBaseNode):
    bl_label = 'Print'
    bl_idname = 'PixelNodePrint'

    def init(self, context):
        self.inputs.new('NodeSocketVirtual', 'Print')

    def draw_buttons(self, context, layout):
        if self.inputs['Print'].is_linked:
            print_value = self.inputs['Print'].links[0].from_socket.default_value
            layout.label(text=f'{print_value}')

# Custom Node Category
class PixelSymphonyNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'PixelTreeType'

# Node Categories
node_categories = [
    PixelSymphonyNodeCategory('UTILITIES', 'Utilities', items=[
        NodeItem('PixelNodeText'),
        NodeItem('PixelNodeFloat'),
        NodeItem('PixelNodePrint'),
        NodeItem('PixelNodeJSONData'),
        NodeItem('PixelSymphonyNode'),
        NodeItem('PixelSymphonyLocationNode'),
        NodeItem('PixelSymphonyProjectionNode'),
        NodeItem('PixelSymphonyWriteToFileNode'),
        NodeItem('PixelFunction'),
        NodeItem('PixelSymphonyCharacterNode'),
        NodeItem('PixelNodeMath')
    ]),
]

# Register and Unregister Functions
classes = (PixelNodeTree, CharacterPropertyGroup, CharacterSocket, 
           PixelNodeText, PixelSymphonyWriteToFileNode, PixelSymphonyProjectionNode, 
           PixelNodeFloat, PixelNodePrint, PixelSymphonyNode, PixelSymphonyLocationNode, 
           PixelNodeJSONData, PixelFunction, PixelNodeMath,
           PixelSymphonyCharacterNode)

def register():
    bpy.utils.register_class(PixelCustomSocket)
    bpy.utils.register_class(WRITE_OT_location_to_file)
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    nodeitems_utils.register_node_categories('PIXEL_NODES', node_categories)
    bpy.types.Scene.character_property_groups = bpy.props.CollectionProperty(type=CharacterPropertyGroup)
    bpy.app.handlers.render_complete.append(write_character_data_on_render)

def unregister():
    bpy.utils.unregister_class(PixelCustomSocket)
    bpy.utils.unregister_class(WRITE_OT_location_to_file)
    nodeitems_utils.unregister_node_categories('PIXEL_NODES')
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.character_property_groups
    bpy.app.handlers.render_complete.remove(write_character_data_on_render)


# Register when script is run
# if __name__ == "__main__":
#     register()

