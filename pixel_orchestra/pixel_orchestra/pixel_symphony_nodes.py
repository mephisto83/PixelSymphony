


import bpy
from bpy.types import NodeTree, Node, NodeSocket, NodeSocketFloat
from bpy.props import *
import inspect
import json
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
        NodeItem('PixelFunction'),
        NodeItem('PixelNodeMath')
    ]),
]

# Register and Unregister Functions
classes = (PixelNodeTree, PixelNodeText, PixelNodeFloat, PixelNodePrint, PixelNodeJSONData, PixelFunction, PixelNodeMath)

def register():
    bpy.utils.register_class(PixelCustomSocket)
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    nodeitems_utils.register_node_categories('PIXEL_NODES', node_categories)


def unregister():
    bpy.utils.unregister_class(PixelCustomSocket)
    nodeitems_utils.unregister_node_categories('PIXEL_NODES')
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)


# Register when script is run
# if __name__ == "__main__":
#     register()

