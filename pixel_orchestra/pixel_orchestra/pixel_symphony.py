
import bpy
import uuid
import json
import mathutils
import bmesh
import random
from mathutils import Vector
from .pixel_rendering import frames_to_generate
from .pixel_utils import distribute_collection_to_face, get_mesh_data, get_meshes_in_collection
from .pixel_stored_functions import functions_dict
from bpy.props import CollectionProperty, StringProperty

PIX_PREFIX = "pix_"
PIX_ID = "pix_id"
PIX_ID_DUPS = "pix_id_dups"
PIX_PROPERTIES = "pix_properties"


def create_driver(material, node, object, expression, variables_data):
    # Create a driver for the node's value
    driver = node.outputs[0].driver_add("default_value").driver
    driver.type = 'SCRIPTED'
    driver.expression = expression

    # Add variables to the driver
    for var_index, (var_name, data_path) in enumerate(variables_data):
        var = driver.variables.new()
        var.name = f"{var_name}"
        var.type = 'SINGLE_PROP'
        target = var.targets[0]
        target.id_type = 'OBJECT'
        target.id = object # The object containing the property
        target.data_path = data_path  # The data path to the property

    print(f"Driver created on node '{node.name}' in material '{material.name}'.")
    return driver

def create_object_driver(mesh, object, property_name, axis, expression, variables_data):
    """
    Creates a driver for a specified property on a mesh object.

    :param mesh: The mesh object on which the driver is to be created.
    :param object: The Blender object to which the driver refers.
    :param property_name: The name of the property to drive.
    :param expression: The driver expression.
    :param variables_data: A list of tuples containing variable names and data paths.
    :return: The created driver.
    """
    if axis == "y":
        axis = 1
    elif axis == "z":
        axis = 2
    elif axis == "x":
        axis = 0

    # Access the property to drive and create a driver for it
    fcurve = mesh.driver_add(property_name, axis)
    driver = fcurve.driver
    driver.type = 'SCRIPTED'
    driver.expression = expression

    # Add variables to the driver
    for var_index, (var_name, data_path) in enumerate(variables_data):
        var = driver.variables.new()
        var.name = var_name
        var.type = 'SINGLE_PROP'
        target = var.targets[0]
        target.id_type = 'OBJECT'
        target.id = object  # The object containing the property
        target.data_path = data_path  # The data path to the property

    print(f"Driver created on property '{property_name}' in mesh '{mesh.name}'.")
    return driver



def read_prefixed_properties(node, prefix):
    properties = {}
    # Check each property of the node
    for prop_name in node.keys():
        if prop_name.startswith(prefix):
            # Store the property and its value
            properties[prop_name] = node[prop_name]

    return properties
def split_string_by_comma(input_string):
    # Split the string by comma
    return input_string.split(',')
def remove_prefix(string, prefix):
    if string.startswith(prefix):
        return string[len(prefix):]
    return string
def generate_unique_id():
    # Generate a UUID (UUID4)
    unique_id = uuid.uuid4()
    return str(unique_id)
def convert_string(input_string):
    try:
        # Try converting to an FLOAT
        return float(input_string)
    except ValueError:
        try:
            # Try converting to a INTEGER if it's not an integer
            return int(input_string)
        except ValueError:
            # Return as string if it's neither an integer nor a float
            return input_string
def set_custom_property_if_not_exists(mesh, property_name, property_value):
    # Check if the property already exists
    if property_name not in mesh:
        # Set the property
        mesh[property_name] = convert_string(property_value)
        print(f"Property '{property_name}' set to '{property_value}'.")
    else:
        print(f"Property '{property_name}' already exists. No action taken.")

def convert_property_name(prop_name):
    """
    Converts a property name into a formatted string with the property and axis.

    :param prop_name: The original property name (e.g., 'scale_x', 'location_y', 'rotation_z').
    :return: Formatted string in the format '["property"].axis'.
    """
    # Split the property name by '_'
    parts = prop_name.split('_')

    # Mapping of property names to their Blender equivalents
    property_mapping = {
        "scale": "scale",
        "location": "location",
        "rotation": "rotation_euler"
    }
    # Check if the property name is valid and in the mapping
    if parts[0] in property_mapping and len(parts) == 2:
        blender_property = property_mapping[parts[0]]
        axis = parts[1]
        return { 
            "path" : f'["{blender_property}"].{axis}',
            "property" : blender_property,
            "axis" : axis
        }
    else:
        raise ValueError("Invalid property name")

def realize_objects(obj):
    print(f"object {obj.name} found")
    pix_properties = read_prefixed_properties(obj, PIX_PREFIX)
    if PIX_PROPERTIES in pix_properties:
        prop_keys = pix_properties[PIX_PROPERTIES]
        props = split_string_by_comma(prop_keys)
        for i in range(len(props)):
            prop = f"{PIX_PREFIX}{props[i]}"
            print(f"objects {prop} found")
            # set the objects custom property
            if prop + "_expression" in pix_properties:
                expression = pix_properties[prop + "_expression"]
            else:
                print(f"no expression for  {prop} found")
                expression = False
            if prop in pix_properties:
                set_custom_property_if_not_exists(obj, remove_prefix(prop, PIX_PREFIX), pix_properties[prop])
            variables_data = []
            if prop + "_properties" in pix_properties:
                _properties = split_string_by_comma(pix_properties[prop + "_properties"])
                _property_paths = split_string_by_comma(pix_properties[prop + "_property_paths"])
                _property_paths = [f'["{i}"]' for i in _property_paths]
                variables_data = zip(_properties, _property_paths)
            if expression:
                temp = convert_property_name(remove_prefix(prop, PIX_PREFIX))
                create_object_driver(
                    mesh=obj, 
                    object=obj,
                    property_name=temp["property"],
                    axis=temp["axis"],
                    expression=expression,
                    variables_data=variables_data
                )

def realize_nodes(node, material, obj):
    pix_properties = read_prefixed_properties(node, PIX_PREFIX)
    if PIX_PROPERTIES in pix_properties:
        prop_keys = pix_properties[PIX_PROPERTIES]
        props = split_string_by_comma(prop_keys)
        for i in range(len(props)):
            prop = f"{PIX_PREFIX}{props[i]}"
            print(f"nodes {prop} found")
            # set the objects custom property
            if prop + "_expression" in pix_properties:
                expression = pix_properties[prop + "_expression"]
            else:
                print(f"no expression for  {prop} found")
                expression = False
            if prop in pix_properties:
                set_custom_property_if_not_exists(obj, remove_prefix(prop, PIX_PREFIX), pix_properties[prop])
            variables_data = []
            if prop + "_properties" in pix_properties:
                _properties = split_string_by_comma(pix_properties[prop + "_properties"])
                _property_paths = split_string_by_comma(pix_properties[prop + "_property_paths"])
                _property_paths = [f'{i}' for i in _property_paths]
                variables_data = zip(_properties, _property_paths)
            print("variables_data")
            print(variables_data)
            if expression:
                create_driver(
                    material, 
                    node, 
                    object=obj,
                    expression=expression,
                    variables_data=variables_data
                )

def iterate_collection(collection, object_func=None, material_func=None, node_func=None):
    # Find the collection
    if not collection:
        print(f"Collection '{collection.name}' not found.")
        return

    # Iterate through each object in the collection
    for obj in collection.objects:
        # Execute the object function
        if object_func:
            object_func(obj)

        # Check if the object has material slots
        if hasattr(obj.data, 'materials'):
            for material in obj.data.materials:
                if material is not None:
                    # Execute the material function
                    if material_func:
                        material_func(material, obj)

                    # Iterate through each node in the material's node tree
                    if material.node_tree is not None:
                        for node in material.node_tree.nodes:
                            # Execute the node function
                            if node_func:
                                node_func(node, material, obj)
def has_customization(material):
    print("check for customizations")
    if material.node_tree is not None:
        print(f"material.node_tree.nodes => {len(material.node_tree.nodes)}")
        for node in material.node_tree.nodes:
            print("checking nodes")
            print(f"node: {node.name}")
            # Execute the node function
            pix_properties = read_prefixed_properties(node, PIX_PREFIX)
            print(pix_properties)
            print(len(pix_properties.keys()))
            if len(pix_properties.keys()) > 0:
                return True
    return False

def delete_collection_and_hierarchy(collection_name):
    # Find the collection
    collection = bpy.data.collections.get(collection_name)
    if not collection:
        print(f"Collection '{collection_name}' not found.")
        return

    # Function to recursively delete objects in collections
    def delete_objects_in_collection(coll):
        # Delete all objects in the current collection
        for obj in coll.objects:
            bpy.data.objects.remove(obj, do_unlink=True)
        
        # Recursively delete objects in child collections
        for child_coll in coll.children:
            delete_objects_in_collection(child_coll)

    # Start the recursive deletion
    delete_objects_in_collection(collection)

    # Once all objects are deleted, delete the collection itself
    bpy.data.collections.remove(collection)

def find_collections_with_property(property_name, property_value):
    matching_collections = []

    # Iterate through all collections
    for collection in bpy.data.collections:
        # Check if the collection has the specified property
        if property_name in collection:
            # Check if the property value matches
            if collection[property_name] == property_value:
                matching_collections.append(collection)

    return matching_collections

def duplicate_customized_materials_in_collection(collection_name):
    # Find the collection
    collection = bpy.data.collections.get(collection_name)
    if not collection:
        print(f"Collection '{collection_name}' not found.")
        return

    # Iterate through each object in the collection
    for obj in collection.objects:
        # Check if the object has material slots
        if hasattr(obj.data, 'materials'):
            for i in range(len(obj.data.materials)):
                original_material = obj.data.materials[i]
                print(f"checking material =>  {original_material.name}")
                # Check if there is a material in the slot
                if original_material is not None and has_customization(original_material):
                    # Duplicate the material
                    duplicate_material = original_material.copy()
                    duplicate_material.name = f"{original_material.name}_duplicate"
                    
                    # Replace the original material with the duplicate
                    obj.data.materials[i] = duplicate_material

def delete_collection_instance(collection_instance_name):
    # Get the collection instance object
    collection_instance = bpy.data.objects.get(collection_instance_name)
    if not collection_instance:
        print(f"Collection instance '{collection_instance_name}' not found.")
        return

    # Delete the object
    bpy.data.objects.remove(collection_instance, do_unlink=True)

def link_obj_to_collection(obj, collection_name):
    """
    Links an existing obj to a specified collection.

    Parameters:
    - obj: The object to link.
    - collection_name: The name of the collection to link the armature to.
    """

    # Check if the specified collection exists
    collection = bpy.data.collections.get(collection_name)
    if not collection:
        # Create a new collection if it doesn't exist
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)
        print(f"Created new collection '{collection_name}'.")

    # Link the armature to the collection if it's not already linked
    if obj.name not in collection.objects:
        collection.objects.link(obj)
        print(f"Linked armature '{obj.name}' to collection '{collection_name}'.")
    else:
        print(f"Armature '{obj.name}' is already in the collection '{collection_name}'.")
def move_top_objects_in_collection(collection_name, move_vector):
    # Check if the collection exists
    collection = bpy.data.collections.get(collection_name)
    if not collection:
        print(f"Collection '{collection_name}' not found.")
        return

    # Convert the move_vector to a mathutils Vector if it's not already
    if not isinstance(move_vector, Vector):
        move_vector = Vector(move_vector)

    # Move each object in the collection
    # for obj in collection.objects:
    #     if obj.parent == None:
    #         obj.location += move_vector
    #         print(f"Moved {obj.name} by {move_vector}")

def create_collection(collection_name, parent_collection_name=None):
    # Create a new collection
    new_collection = bpy.data.collections.new(collection_name)

    # If a parent collection name is given, link the new collection to the parent
    if parent_collection_name:
        parent_collection = bpy.data.collections.get(parent_collection_name)
        if parent_collection:
            parent_collection.children.link(new_collection)
            print(f"Collection '{collection_name}' created under parent '{parent_collection_name}'.")
        else:
            print(f"Parent collection '{parent_collection_name}' not found. Collection created but not linked.")
    else:
        # No parent collection given, link the new collection to the master collection
        bpy.context.scene.collection.children.link(new_collection)
        print(f"Collection '{collection_name}' created at the top level.")

    return new_collection

def duplicate_collection_instance(source_instance, parent_collection=None):
    """
    Duplicates a Blender collection instance along with its objects and their hierarchical relationships.

    :param source_instance: The source Blender collection instance to duplicate.
    :return: The new duplicated collection instance object.
    """
    if not isinstance(source_instance, bpy.types.Object) or source_instance.instance_type != 'COLLECTION':
        raise TypeError("The provided input is not a Blender collection instance.")

    source_collection = source_instance.instance_collection

    if source_collection is None:
        raise ValueError("The provided instance does not have a linked collection.")

    # Create a new collection
    new_collection = bpy.data.collections.new(name=f"{source_collection.name}_Duplicate")
    if parent_collection != None:
        parent_collection.children.link(new_collection)
    else:
        bpy.context.scene.collection.children.link(new_collection)
    
    # Function to duplicate object and link to the new collection
    def duplicate_object(obj, parent=None):
        new_obj = obj.copy()
        new_obj.data = obj.data.copy()
        new_obj.animation_data_clear()
        new_collection.objects.link(new_obj)

        if parent:
            new_obj.parent = parent

        return new_obj

    # Dictionary to keep track of old-to-new object mapping
    old_to_new_objs = {}

    # Recursively duplicate objects and maintain parent-child relationships
    def duplicate_recursive(obj, new_parent=None):
        new_obj = duplicate_object(obj, parent=new_parent)
        old_to_new_objs[obj] = new_obj

        for child in obj.children:
            duplicate_recursive(child, new_obj)

    # Duplicate the objects in the collection
    for obj in source_collection.all_objects:
        if obj.parent is None:  # Start with root objects
            duplicate_recursive(obj)

    # Restore parent-child relationships for all objects
    for obj, new_obj in old_to_new_objs.items():
        if obj.parent in old_to_new_objs:
            new_obj.parent = old_to_new_objs[obj.parent]

    # Copy location, scale, and rotation from the source instance
    # new_collection.location = source_instance.location
    # new_collection.scale = source_instance.scale
    # new_collection.rotation_euler = source_instance.rotation_euler
    move_top_objects_in_collection(new_collection.name, source_instance.location)
    # Create a new instance for the duplicated collection
    # new_instance = bpy.data.objects.new(name=f"{source_instance.name}_Duplicate", object_data=None)
    # new_instance.instance_type = 'COLLECTION'
    # new_instance.instance_collection = new_collection
    # bpy.context.scene.collection.objects.link(new_instance)

    return new_collection
def duplicate_collection_as_individual_objects(collection_instance):
    # Check if the provided object is a collection instance
    if collection_instance.instance_type != 'COLLECTION':
        print(f"{collection_instance.name} is not a collection instance.")
        return

    # Get the collection linked to the instance
    collection = collection_instance.instance_collection
    if not collection:
        print("No collection linked to the instance.")
        return
    new_collection = create_collection(collection_name=f"{collection_instance.name}_realized")
    # Duplicate objects in the collection and link them to the scene
    for obj in collection.objects:
        new_obj = obj.copy()
        if obj.data:
            new_obj.data = obj.data.copy()

        # Position the new object relative to the collection instance
        new_obj.location += collection_instance.location
        link_obj_to_collection(new_obj, new_collection.name)
    return new_collection

def create_collection_instance(collection_name, parent_collection = None):
    # Ensure the collection exists
    collection = bpy.data.collections.get(collection_name)
    if not collection:
        print(f"Collection '{collection_name}' not found.")
        return

    # Create an empty object
    empty_obj = bpy.data.objects.new("Instance_" + collection_name, None)
    if parent_collection == None:
        bpy.context.collection.objects.link(empty_obj)
    else: 
        parent_collection.objects.link(empty_obj)

    # Set the instance type and collection
    empty_obj.instance_type = 'COLLECTION'
    empty_obj.instance_collection = collection
    return empty_obj

def duplicate_collection(collection_name, make_single):
    original_collection = bpy.data.collections.get(collection_name)
    if not original_collection:
        print(f"Collection '{collection_name}' not found")
        return

    new_collection = bpy.data.collections.new(name=f"{collection_name}_Duplicate")
    bpy.context.scene.collection.children.link(new_collection)

    for obj in original_collection.objects:
        new_obj = obj.copy()
        if make_single:
            new_obj.data = obj.data.copy() if obj.data else None
        new_collection.objects.link(new_obj)

def get_collection_names(self, context):
    collection_names = [(col.name, col.name, "") for col in bpy.data.collections]
    return collection_names

def find_collection_instances(collection_name):
    # Find the collection
    target_collection = bpy.data.collections.get(collection_name)
    if not target_collection:
        print(f"Collection '{collection_name}' not found.")
        return []

    instances = []

    # Iterate through all objects in the Blender scene
    for obj in bpy.data.objects:
        # Check if the object is a collection instance and if it's the target collection
        if obj.instance_type == 'COLLECTION' and obj.instance_collection == target_collection:
            instances.append(obj)

    return instances

class DuplicateCollectionOperator(bpy.types.Operator):
    """Operator to duplicate a collection"""
    bl_idname = "object.duplicate_collection"
    bl_label = "Duplicate Collection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        collection_name = context.scene.my_collection_enum
        parent_collection = bpy.data.collections.get(context.scene.target_collection_enum)
        create_collection_instance(collection_name, parent_collection)
        return {'FINISHED'}

def find_pixel_symphony_node_trees(self, context):
    """
    Find all node trees of type 'PixelTreeType'.

    :return: A list of node trees that are of type 'PixelTreeType'.
    """
    pixel_symphony_tree_names = [('','','')]

    # Iterate through all node trees in the current Blender file
    for node_tree in bpy.data.node_groups:
        # Check if the node tree is of type 'PixelTreeType'
        if node_tree.bl_idname == 'PixelTreeType':
            pixel_symphony_tree_names.append((node_tree.name, node_tree.name, ""))

    return pixel_symphony_tree_names

def get_pixel_symphony_node_trees(name):
    # Iterate through all node trees in the current Blender file
    for node_tree in bpy.data.node_groups:
        # Check if the node tree is of type 'PixelTreeType'
        if node_tree.bl_idname == 'PixelTreeType' and name == node_tree.name:
            return node_tree

    return None

def get_pixel_symphony_trees():
    res = []
    # Iterate through all node trees in the current Blender file
    for node_tree in bpy.data.node_groups:
        # Check if the node tree is of type 'PixelTreeType'
        if node_tree.bl_idname == 'PixelTreeType':
            res.append(node_tree)

    return res

def get_pixelnode_math_nodes(node_tree):
    """
    Get all PixelNodeMath nodes from a given node tree.

    :param node_tree: The node tree to search in.
    :return: A list of PixelNodeMath nodes found in the node tree.
    """
    pixelnode_math_nodes = []

    # Check if node_tree is a valid node tree
    if node_tree is None or not hasattr(node_tree, 'nodes'):
        print("Invalid node tree provided.")
        return pixelnode_math_nodes

    # Iterate through all nodes in the node tree
    for node in node_tree.nodes:
        # Check if the node is of type PixelNodeMath
        if node.bl_idname == 'PixelNodeMath':
            pixelnode_math_nodes.append(node)

    return pixelnode_math_nodes

def get_connected_socket(node, socket_name):
    """
    Get the socket that is connected to the given socket of a node.

    :param node: The node containing the socket.
    :param socket_name: The name of the socket in the node.
    :return: The socket connected to the given node's socket, or None if not connected.
    """
    # Check if the socket exists in the node
    if socket_name not in node.inputs and socket_name not in node.outputs:
        print(f"Socket named '{socket_name}' not found in node.")
        return None

    # Determine if the socket is an input or an output
    socket = node.inputs.get(socket_name) or node.outputs.get(socket_name)

    # Check if the socket is connected
    if socket.is_linked:
        # Get the first link (assuming one connection for simplicity)
        link = socket.links[0]

        # Return the corresponding connected socket
        if socket == link.from_socket:
            return link.to_socket
        else:
            return link.from_socket

    return None

def get_connected_node(node, socket_name):
    """
    Get the node that is connected to the given socket of a node.

    :param node: The node containing the socket.
    :param socket_name: The name of the socket in the node.
    :return: The node connected to the given node's socket, or None if not connected.
    """
    # Check if the socket exists in the node
    if socket_name not in node.inputs and socket_name not in node.outputs:
        print(f"Socket named '{socket_name}' not found in node.")
        return None

    # Determine if the socket is an input or an output
    socket = node.inputs.get(socket_name) or node.outputs.get(socket_name)

    # Check if the socket is connected
    if socket.is_linked:
        # Get the first link (assuming one connection for simplicity)
        link = socket.links[0]

        # Return the node at the other end of the link
        connected_socket = link.from_socket if socket == link.to_socket else link.to_socket
        return connected_socket.node

    return None

def extract_data_from_pixel_function(node):
    """
    Extracts the selected function and input socket values from a PixelFunction node.
    Includes json_path_data from connected nodes.

    :param node: An instance of PixelFunction.
    :return: A dictionary containing the selected function and input socket values.
    """
    if node.bl_idname != 'PixelFunction':
        raise ValueError("The provided node is not a PixelFunction.")

    # Extract the selected function
    function_name = node.selected_function

    # Extract input socket values
    socket_values = {}
    for socket in node.inputs:
        # Check if the socket is connected
        if socket.is_linked:
            # Get the connected socket
            connected_socket = socket.links[0].from_socket
            # Use json_path_data from the connected node, if available
            json_path_data = getattr(connected_socket, 'json_path_data', None)
            socket_values[socket.name] = {
                'json_data': socket.json_data,
                'json_path_data': json_path_data,
                'json_float_data': socket.json_float_data
            }
        else:
            # Handle custom socket data extraction
            socket_values[socket.name] = {
                'json_data': socket.json_data,
                'json_path_data': socket.json_path_data,
                'json_float_data': socket.json_float_data
            }

    # Compile the node data
    node_data = {
        'selected_function': function_name,
        'input_sockets': socket_values
    }

    return node_data

def extract_data_old(json_data, path):
    """
    Extracts data based on a custom path format.

    :param json_data: The JSON object.
    :param path: The custom path string.
    :return: Extracted data based on the path.
    """
    parts = path.split('.')
    current_data = json_data
    results = []

    for part in parts[1:]:  # Skip the root symbol '$'
        if part == "[]":
            # Collect data from each element in the current list
            new_results = []
            for i, item in enumerate(current_data):
                for sub_item in item:
                    new_results.append(sub_item)
            current_data = new_results
        else:
            # Collect data based on the key
            current_data = [item.get(part) for item in current_data if isinstance(item, dict)]
    
    return current_data

def extract_data(json_data, path):
    """
    Extracts data based on a custom path format.

    :param json_data: The JSON object.
    :param path: The custom path string.
    :return: Extracted data based on the path.
    """
    parts = path.split('.')
    current_data = json_data
    results = []

    for part in parts[1:]:  # Skip the root symbol '$'
        if part == "[]":
            # Collect data from each element in the current list
            new_results = []
            for i, item in enumerate(current_data):
                new_results.append(item)
            current_data = new_results
        else:
            # Collect data based on the key
            if isinstance(current_data, dict):
                current_data = current_data.get(part)
            else:
                print(current_data)
                print(f"part => {part}")
                print(f"path => {path}")
                raise BaseException(f"that shouldnt happen i think, {part}")
    
    return current_data

class ApplyMusicOperator(bpy.types.Operator):
    """Operator to apply music to collections"""
    bl_idname = "object.apply_music_to_collections"
    bl_label = "Apply Music"
    bl_options = {'REGISTER', 'UNDO'}
    # bpy.data.node_groups["Pixel Symphony Nodes"].nodes["Pixel Connection Node.001"].end
    def execute(self, context):
        json_data = context.scene['json_data']
        raw_json_data = context.scene['raw_json_data']
        raw_json_data = json.loads(raw_json_data)
        scene = context.scene
        track_count , unique_notes_per_track, unique_notes_for_track = analyze_tracks(json_data=json_data)
        self.report({'INFO'}, "Apply Music")
        symphony_trees = get_pixel_symphony_trees()
        for i in range(len(symphony_trees)):
            defauly_symphony_tree = symphony_trees[i]
            pixel_math_nodes = get_pixelnode_math_nodes(defauly_symphony_tree)
            for i in range(len(pixel_math_nodes)):
                pixel_math_node = pixel_math_nodes[i]
                print(pixel_math_node)
                print(f"pixel_math_nodes.start => {pixel_math_node.start}")
                print(f"pixel_math_nodes.end => {pixel_math_node.end}")
                print(f"pixel_math_nodes.pixproperty => {pixel_math_node.pixproperty}")
                track_socket = get_connected_socket(pixel_math_node, 'Track')
                if track_socket != None:
                    print(f"Track {track_socket.json_path_data}")
                    
                    note_socket = get_connected_socket(pixel_math_node, 'Note')
                    if note_socket != None:
                        midi_socket = get_connected_socket(pixel_math_node, 'Midi')
                        if midi_socket != None:
                            duration_socket = get_connected_socket(pixel_math_node, 'Duration')
                            if duration_socket != None:
                                time_socket = get_connected_socket(pixel_math_node, 'Time')
                                if time_socket != None:
                                    selected_function = None
                                    input_sockets = None
                                    value_node = get_connected_node(pixel_math_node, "Value")
                                    if value_node:
                                        value_node_info = extract_data_from_pixel_function(value_node)
                                        selected_function = value_node_info["selected_function"]
                                        input_sockets = value_node_info["input_sockets"]
                                    if selected_function != None and input_sockets != None:
                                        tracks = extract_data(raw_json_data, track_socket.json_path_data)
                                        for i in range(len(tracks)):
                                            track_section = get_track_section(scene, i)
                                            if track_section.enabled:
                                                track = tracks[i]
                                                note_path = f"{remove_prefix(note_socket.json_path_data, track_socket.json_path_data)}"
                                                notes = extract_data(track, note_path)
                                                for j in range(len(notes)):
                                                    data = {
                                                        "Track": i,
                                                        "Note": j,
                                                    }
                                                    note = notes[j]

                                                    duration_path = f"${remove_prefix(duration_socket.json_path_data, note_socket.json_path_data)}"
                                                    data["Duration"] = extract_data(note, duration_path)

                                                    midi_path = f"${remove_prefix(midi_socket.json_path_data, note_socket.json_path_data)}"
                                                    data["Midi"] = extract_data(note, midi_path)
                                                        
                                                    time_path = f"${remove_prefix(time_socket.json_path_data, note_socket.json_path_data)}"
                                                    data["Time"] = extract_data(note, time_path)

                                                    track_note_collection = find_collection_with_properties({"track": i, "note": data["Midi"] })
                                                    if track_note_collection != None:
                                                        print(f"track {i}")
                                                        print(f"note {j}")
                                                        print("track note  collection found")
                                                        print(functions_dict[selected_function])
                                                        print(input_sockets)
                                                        kwargs = {}
                                                        for key in input_sockets:
                                                            value = None
                                                            if input_sockets[key]['json_path_data']:
                                                                input_path = f"${remove_prefix(input_sockets[key]['json_path_data'], note_socket.json_path_data)}"
                                                                value = extract_data(note, input_path)
                                                            elif 'json_float_data' in input_sockets[key]:
                                                                value = input_sockets[key]['json_float_data']
                                                            kwargs[key] = value
                                                            pass
                                                        data["Value"] = functions_dict[selected_function](**kwargs)
                                                        frame_rate = context.scene.render.fps
                                                        start_frame = int(frame_rate * data["Time"])
                                                        end_frame = int(frame_rate *  data["Time"] + frame_rate * data["Duration"])
                                                        if start_frame + 3 < end_frame:
                                                            print(f"pixel_math_node.pixproperty => {pixel_math_node.pixproperty}")
                                                            pix_objects = find_pix_properties(collection=track_note_collection,property_name=pixel_math_node.pixproperty)
                                                            print(f"pix_objects {len(pix_objects)}")
                                                            for po in pix_objects:
                                                                print(po)
                                                                print(po[pixel_math_node.pixproperty])
                                                                print(po[f"pix_{pixel_math_node.pixproperty}"])
                                                                print(f"applying property {pixel_math_node.pixproperty}")
                                                                po_path = pixel_math_node.pixproperty
                                                                frames = end_frame - start_frame
                                                                start_peak = max(start_frame + 1, int(start_frame + frames * pixel_math_node.start))
                                                                end_peak = min(end_frame - 1, int(end_frame - frames * (1 - pixel_math_node.end)))
                                                                print(f"start_frame => {start_frame}, start_peak => {start_peak}, end_peak => {end_peak}, end_frame => {end_frame}")
                                                                add_keyframe(po, po_path, po[f"pix_{pixel_math_node.pixproperty}"], start_frame)
                                                                add_keyframe(po, po_path, po[f"pix_{pixel_math_node.pixproperty}"], end_frame)

                                                                add_keyframe(po, po_path, data["Value"], start_peak)
                                                                add_keyframe(po, po_path, data["Value"], end_peak)




        instances = [obj for obj in bpy.data.objects if obj.instance_type == 'COLLECTION']  # List of collection instances
        for i in range(track_count):
            for j in range(unique_notes_per_track[i]):
                index = i
                track_section = get_track_section(scene, index)
                if track_section.enabled:
                    matching_instance = find_instance_with_properties(instances, {"track": i, "note": unique_notes_for_track[i][j]})
                    if matching_instance != None:
                        pass

        return {'FINISHED'}

def add_keyframe(obj, property_path, value, frame):
    """
    Sets a value to a property of an object and adds a keyframe.

    Args:
    obj (bpy.types.Object): The object to which the keyframe is added.
    property_path (str): The path to the property (e.g., "location", "rotation_euler", or "['custom_prop']").
    value: The value to set on the property.
    frame (int): The frame number at which to insert the keyframe.
    """
    # Check if the property path is for a custom property
    is_custom_property = property_path.startswith("[\"") and property_path.endswith("\"]")

    # Check for custom property
    if is_custom_property:
        prop_name = property_path[2:-2]  # Extract the property name
        if prop_name in obj.keys():
            obj[prop_name] = value
            obj.keyframe_insert(data_path='["' + prop_name + '"]', frame=frame)
        else:
            print("Custom property not found")
    # Check for regular property
    elif hasattr(obj, property_path):
        print(f"property_path: {property_path}, value : {value}, frame: {frame}")
        setattr(obj, property_path, convert_to_float(value))
        obj.keyframe_insert(data_path=property_path, frame=frame)
    else:
        print("Property not found")

def convert_to_float(value):
    """
    Convert a value to a float if it isn't one already.

    Args:
    value (str, int, float): The value to convert.

    Returns:
    float: The converted value.
    """
    # Check if the value is already a float
    if isinstance(value, float):
        return value
    try:
        # Attempt to convert the value to a float
        return float(value)
    except ValueError:
        # Handle the case where conversion is not possible
        raise ValueError(f"Cannot convert {value} to float")
def find_asset_collections():
    """
    Finds all collections marked as assets.

    Returns:
    list: A list of names of collections that are marked as assets.
    """
    asset_collections = []

    # Iterate through all collections in the blend file
    for collection in bpy.data.collections:
        # Check if the collection is marked as an asset
        if collection.asset_data is not None:
            asset_collections.append(collection.name)

    return asset_collections

def find_pix_properties(collection, property_name):
    unique_properties = []
    try:
        # Check if the collection has the custom PIX_ID
        if PIX_ID_DUPS in collection.keys():
            # Go through each object in the collection
            for obj in collection.objects:
                # Check if the object has the pix_properties custom property
                if "pix_properties" in obj.keys():
                    if property_name in obj:
                        unique_properties.append(obj)

                # Go through each material of the object
                if hasattr(obj.data, "materials"):
                    for mat in obj.data.materials:
                        if mat is not None and mat.node_tree is not None:
                            # Go through each node in the material
                            for node in mat.node_tree.nodes:
                                # Check if the node has the pix_properties custom property
                                if "pix_properties" in node.keys():
                                    if node["pix_properties"].find(property_name) != -1:
                                        obj[f"pix_{property_name}"] = node[f"pix_{property_name}"]
                                        unique_properties.append(obj)
    except Exception as e:
        print(e)
    return unique_properties

def remove_prefix(string, prefix):
    """
    Removes a prefix from a string if the string starts with that prefix.

    :param string: The string from which to remove the prefix.
    :param prefix: The prefix to remove.
    :return: The string without the prefix.
    """
    if string.startswith(prefix):
        return string[len(prefix):]
    return string

class RealizeCollectionOperator(bpy.types.Operator):
    """Operator to make collection instances real copies"""
    bl_idname = "object.realize_collection"
    bl_label = "Realize Collection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        collection_name = context.scene.my_collection_enum
        track_sections = scene.music_data_props.track_sections
        collection_names = set()
        if collection_name:
            collection_names.add(collection_name)
        for i in range(len(track_sections)):
            track_section = track_sections[i]
            if track_section.track_object_collection:
                collection_names.add(track_section.track_object_collection)
        parent_collection = bpy.data.collections.get(context.scene.target_collection_enum)
        for collection_name in collection_names:
            target_collection = bpy.data.collections.get(collection_name)
            if not PIX_ID in target_collection:
                target_collection[PIX_ID] = generate_unique_id()
            else:
                to_delete = find_collections_with_property(PIX_ID_DUPS, target_collection[PIX_ID])
                for i in range(len(to_delete)):
                    inst = to_delete[i]
                    delete_collection_and_hierarchy(inst.name)
            instances = find_collection_instances(collection_name)
            for i in range(len(instances)):
                insta = instances[i]
                new_collection = duplicate_collection_instance(insta, parent_collection)
                new_collection[PIX_ID_DUPS] = target_collection[PIX_ID]
                new_collection['track'] = insta['track']
                new_collection['note'] = insta['note']
                empty = parent_to_empty(new_collection)
                empty.location = insta.location
                empty.rotation_euler = insta.rotation_euler
                empty.scale = insta.scale
                delete_collection_instance(insta.name)
                duplicate_customized_materials_in_collection(new_collection.name)
                iterate_collection(new_collection,
                                object_func=realize_objects,
                                material_func=lambda mat, obj: print(f"Material: {mat.name}, Object: {obj.name}"),
                                node_func=realize_nodes)
        return {'FINISHED'}
def parent_to_empty(collection):
    if not collection:
        print(f"Collection '{collection}' not found")
        return

    # Create an empty object
    bpy.ops.object.empty_add(type='PLAIN_AXES')
    empty = bpy.context.active_object
    empty.name = f"Empty_{collection}"
    # Set the empty as the parent for top-level objects in the collection
    for obj in collection.objects:
        if not obj.parent:
            obj.parent = empty

    unlink_object_from_scene_collection(empty.name)
    # Add the empty to the collection
    collection.objects.link(empty)
    return empty

def unlink_object_from_scene_collection(object_name):
    # Get the object
    obj = bpy.data.objects.get(object_name)
    
    # Check if the object exists
    if obj:
        # Go through all collections in the scene
        for coll in bpy.context.scene.collection.children:
            # If the object is directly linked to a top-level collection in the scene
            if obj.name in coll.objects:
                # Unlink the object from the collection
                coll.objects.unlink(obj)
                print(f"Object '{object_name}' unlinked from the top-level Scene Collection.")
                break
    else:
        print(f"Object '{object_name}' not found in the top-level Scene Collection.")

class ReadJSONFileOperator(bpy.types.Operator):
    """Operator to read a JSON file and store its content in a custom property"""
    bl_idname = "object.read_json_file"
    bl_label = "Read JSON File"
    bl_options = {'REGISTER', 'UNDO'}

    # Define properties for the operator
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    property_name: bpy.props.StringProperty(default="json_data")
    raw_json_data: bpy.props.StringProperty(default="raw_json_data")

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        # Ensure the filepath is not empty
        if not self.filepath:
            self.report({'ERROR'}, "No file path provided")
            return {'CANCELLED'}

        # Read and parse the JSON file
        try:
            with open(self.filepath, 'r') as file:
                json_data = json.load(file)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to read or parse the file: {e}")
            return {'CANCELLED'}

        # Assign the JSON data to a custom property of the scene
        context.scene[self.property_name] = json_data
        context.scene[self.raw_json_data] = read_file_as_text(self.filepath)
        self.report({'INFO'}, f"JSON data set to property '{self.property_name}'")
        return {'FINISHED'}
def read_file_as_text(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return None    
def find_instances_with_properties(instances, properties):
    matching_instances = []

    for instance in instances:
        if all(instance.get(prop) == value for prop, value in properties.items()):
            matching_instances.append(instance)

    return matching_instances

def find_collection_with_properties(properties):
    return find_instance_with_properties(bpy.data.collections, properties)

def find_instance_with_properties(instances, properties):
    matching_instances = find_instances_with_properties(instances, properties)
    if len(matching_instances) > 0:
        return matching_instances[0]
    return None

def analyze_tracks(json_data):
    track_count = len(json_data)
    unique_notes_per_track = []
    unique_notes_for_track = []

    for track in json_data:
        notes = track.get("notes", [])
        unique_notes = {note["midi"] for note in notes}  # Using a set for unique values
        unique_notes_per_track.append(len(unique_notes))
        unique_notes_for_track.append(list(unique_notes))

    return track_count, unique_notes_per_track, unique_notes_for_track

def distribute_collection_on_plane(instance, plane_obj, x_min, x_max, y_min, y_max):
    # Random location within the specified range
    x = random.uniform(x_min, x_max)
    y = random.uniform(y_min, y_max)
    z = 0  # Assuming you want to place them on the plane
    # Check if plane_obj is the correct type
    if not isinstance(plane_obj, bpy.types.Object):
        print(f"Provided plane is not an object: {plane_obj}")
        return
    print(instance)
    print(plane_obj)
    # Apply the plane's rotation to the instance
    instance.rotation_euler = plane_obj.rotation_euler

    # Set the instance's location relative to the plane
    instance.location = plane_obj.matrix_world @ mathutils.Vector((x, y, z))

    # Link the instance to the same collection as the plane
    # plane_collection = plane_obj.users_collection[0] if plane_obj.users_collection else bpy.context.collection
    # plane_collection.objects.link(instance)

    # Parent the instance to the plane
    instance.parent = None

class CalculateRequiredFramesOperator(bpy.types.Operator):
    bl_idname = "scene.calculate_required_frames"
    bl_label = "Calculate Require Frames"

    @classmethod
    def poll(cls, context):
        return 'json_data' in context.scene

    def execute(self, context):
        print("calculating")
        frames_needed = frames_to_generate()
        self.report({'INFO'}, f"Required frames to print {len(frames_needed)}")
        return {'FINISHED'}

class DistributeInstancesOperator(bpy.types.Operator):
    bl_idname = "scene.distribut_instances"
    bl_label = "Distribute instances"

    @classmethod
    def poll(cls, context):
        return 'json_data' in context.scene

    def execute(self, context):
        scene = context.scene
        # Check if music data is available
        placement_offsets = {}
        if  'music_data' in scene and 'tracks' in scene['music_data']:
            tracks = list(scene['music_data']['tracks'])
            for index, track in enumerate(tracks):
                prop_name = f"track-section-{index}"
                track_section = get_track_section(scene, index)
                if track_section != None and track_section.enabled:
                    # Dropdown for plane selection
                    if track_section.enabled:
                        mesh_name = track_section.track_plane
                        if mesh_name != None and mesh_name in bpy.data.objects:
                            plan_mesh = bpy.data.objects[mesh_name]
                            # Checkboxes for MIDI notes
                            instances = [obj for obj in bpy.data.objects if obj.instance_type == 'COLLECTION']  # List of collection instances
                            for note in track['notes']:
                                prop_name = f"cb_{note}_{index}"
                                track_note = get_track_note(scene, index, note)
                                if  track_note.enabled or track_note == None:
                                    properties = {"note": note, "track": index}  # Dictionary of properties to match
                                    matching_instance = find_instance_with_properties(instances, properties)
                                    if matching_instance != None:
                                        maxx = track_section.max_x
                                        maxy = track_section.max_y
                                        minx = track_section.min_x
                                        miny = track_section.min_y
                                        distribute_collection_on_plane(matching_instance, plan_mesh, minx, maxx, miny, maxy)
                                else:
                                    print(f"cant find {prop_name}")
                        elif mesh_name != None and mesh_name in bpy.data.collections:
                            collection = bpy.data.collections[mesh_name]
                            print("collection ")
                            print(collection)
                            objs = get_meshes_in_collection(collection.name)
                            all_mesh_data = []
                            for i in range(len(objs)):
                                obj = objs[i]
                                mesh_data = get_mesh_data(obj)
                                all_mesh_data.extend(mesh_data)
                            if  collection.name in placement_offsets:
                                c = placement_offsets[collection.name] 
                            else:
                                placement_offsets[collection.name] = 0
                                c = 0
                            instances = [obj for obj in bpy.data.objects if obj.instance_type == 'COLLECTION']  # List of collection instances
                            for note in track['notes']:
                                prop_name = f"cb_{note}_{index}"
                                track_note = get_track_note(scene, index, note)
                                if  track_note.enabled or track_note == None:
                                    properties = { "note": note, "track": index }  # Dictionary of properties to match
                                    mesh_dat = all_mesh_data[c % len(all_mesh_data)]
                                    matching_instance = find_instance_with_properties(instances, properties)
                                    if matching_instance != None:
                                        distribute_collection_to_face(matching_instance, mesh_dat)
                                        c = c + 1
                                        placement_offsets[collection.name] = c
                                else:
                                    print(f"cant find {prop_name}")
                            
                            
        self.report({'INFO'}, "Distributed instances")
        return {'FINISHED'}

def print_all_keys_of_object(obj):
    if obj is None:
        print("No object provided")
        return

    if hasattr(obj, 'keys'):
        print(f"Keys for object '{obj.name}':")
        for key in obj.keys():
            print(key)
    else:
        print(f"The provided object '{obj.name}' does not support custom properties.")

class ProcessJSONFileOperator(bpy.types.Operator):
    bl_idname = "scene.process_json_file"
    bl_label = "Process JSON File"

    @classmethod
    def poll(cls, context):
        return 'json_data' in context.scene

    def execute(self, context):
        json_data = context.scene['json_data']
        scene = context.scene
        # Process the json_data here
        # ...
        track_count , unique_notes_per_track, unique_notes_for_track = analyze_tracks(json_data=json_data)
        print("Number of tracks:", track_count)
        print("Unique MIDI notes per track:", unique_notes_per_track)
        music_data = {
            'tracks': []
        }

        for i in range(track_count):
            temp = {
                'name': json_data[i].get('name') + f" {i+1}",
                'notes': unique_notes_for_track[i]
            }
            music_data["tracks"].append(temp)
        context.scene["music_data"] = music_data
        collection_name = context.scene.my_collection_enum
        instances = [obj for obj in bpy.data.objects if obj.instance_type == 'COLLECTION']  # List of collection instances
        for i in range(track_count):
            add_dynamic_properties(scene, unique_notes_for_track[i], i)
            for j in range(unique_notes_per_track[i]):
                index = i
                if is_track_section_enabled(scene, index):
                    matching_instance = find_instance_with_properties(instances, {"track": i, "note": unique_notes_for_track[i][j]})
                    if matching_instance == None:
                        parent_collection = bpy.data.collections.get(context.scene.target_collection_enum)
                        track_section = get_track_section(scene, track_index=index)
                        if track_section != None and track_section.track_object_collection:
                            insta = create_collection_instance(track_section.track_object_collection, parent_collection)
                        else:
                            insta = create_collection_instance(collection_name, parent_collection)
                        insta["track"] = i
                        insta["note"] = unique_notes_for_track[i][j]
                    else:
                        print("found instance")
        self.report({'INFO'}, "JSON data processed")
        return {'FINISHED'}

def add_dynamic_properties(scene, midi_notes, track_index):
    max_dim = 2
    add_track_section_to_properties(scene, track_index=track_index, 
                                    min_x=-max_dim,
                                    max_x=max_dim,
                                    min_y=-max_dim,
                                    max_y=max_dim,
                                    show=False,
                                    enabled=True)
    for note in midi_notes:
        add_track_to_properties(scene, track_index, note)
    
class TrackNoteItem(bpy.types.PropertyGroup):
    track_id: bpy.props.IntProperty(name="Track")
    note_id: bpy.props.IntProperty(name="Note")
    enabled: bpy.props.BoolProperty(name="Enabled")

class TrackSectionItem(bpy.types.PropertyGroup):
    track_id: bpy.props.IntProperty()
    track_plane: bpy.props.StringProperty()
    track_object_collection: bpy.props.StringProperty()
    track_symphony_tree: bpy.props.EnumProperty(items=find_pixel_symphony_node_trees)
    min_x: bpy.props.FloatProperty(name=f"Min X")
    min_y: bpy.props.FloatProperty(name="Min y")
    max_x: bpy.props.FloatProperty(name="Max x")
    max_y: bpy.props.FloatProperty(name="Max y")
    show: bpy.props.BoolProperty(name="Show")
    enabled: bpy.props.BoolProperty(name="Enabled")

def show_track_section(scene, track_index):
    track_section = get_track_section(scene, track_index=track_index)
    if track_section != None:
        if track_section.enabled:
            return track_section.show
    return False
def is_track_section_enabled(scene, track_index):
    track_section = get_track_section(scene, track_index=track_index)
    if track_section != None:
        return track_section.enabled
    print("track section is none")
    return False

def has_track_section(scene, track_index):
    track_section = get_track_section(scene, track_index=track_index)
    return track_section != None

def get_track_section(scene, track_index):
    for track_item in scene.music_data_props.track_sections:
        if track_item.track_id == track_index:
            return track_item
    return None

def get_track_note(scene, track_index, note_id):
    for track_item in scene.music_data_props.track_notes:
        if track_item.track_id == track_index and track_item.note_id == note_id:
            return track_item
    return None

def add_track_to_properties(scene, track_index, note_id):
    note = get_track_note(scene, track_index=track_index, note_id=note_id)
    if note == None:
        track_notes = scene.music_data_props.track_notes
        track_item = track_notes.add()
        track_item.name = f"Track {track_index + 1}"
        track_item.track_id = track_index
        track_item.note_id = note_id
        track_item.enabled = True

def add_track_section_to_properties(scene, track_index, min_x, min_y, max_x, max_y, show, enabled):
    if not has_track_section(scene, track_index=track_index):
        print(f"add_track_section_to_properties => {track_index}")
        track_sections = scene.music_data_props.track_sections
        track_section_item = track_sections.add()
        track_section_item.name = f"Track {track_index + 1}"
        track_section_item.track_id = track_index
        track_section_item.min_x = min_x
        track_section_item.min_y = min_y
        track_section_item.max_x = max_x
        track_section_item.max_y = max_y
        track_section_item.show = show
        track_section_item.enabled = enabled
class MusicDataProperties(bpy.types.PropertyGroup):
    # This class will hold all the dynamic properties
    track_notes: bpy.props.CollectionProperty(type=TrackNoteItem)
    track_sections: bpy.props.CollectionProperty(type=TrackSectionItem)

class PixelSymphonyPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Pixel Symphony Panel"
    bl_idname = "OBJECT_PT_pixelsymphony"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return True

    def draw_music_panel(self, context):
        layout = self.layout
        scene = context.scene
        
        # Check if music data is available
        if 'music_data' in scene and 'tracks' in scene['music_data']:
            tracks = list(scene['music_data']['tracks'])
            for index, track in enumerate(tracks):
                track_section = get_track_section(scene, index)
                if track_section != None:
                    box = layout.box()
                    box.prop(track_section, 'enabled', text=track['name'])
                    box.prop(track_section, 'show', text="Show")
                    box.prop_search(track_section, 'track_plane', bpy.data, "collections")
                    box.prop_search(track_section, 'track_object_collection', bpy.data, "collections")
                    box.prop(track_section, "track_symphony_tree")
                    if show_track_section(scene, index):
                        # Dropdown for plane selection
                        for prop_name_boundary in [
                            f"min_x",
                            f"max_x",
                            f"min_y",
                            f"max_y"]:
                            if hasattr(track_section, prop_name_boundary):
                                box.prop(track_section, prop_name_boundary)
                        if track_section.show:
                            for note in track['notes']:
                                track_note = get_track_note(scene, index, note)
                                prop_name = f"cb_{note}_{index}"
                                if track_note != None:
                                    box.prop(track_note, 'enabled', text=str(note))
                                else:
                                    print(f"mising {prop_name}")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(context.scene, "music_data_props")
        layout.prop(context.scene, "my_collection_enum")
        layout.prop(context.scene, "target_collection_enum")
        # layout.operator("object.duplicate_collection")
        layout.operator("object.read_json_file")
        layout.prop(context.scene, "make_single", text="Make single user")
        if 'json_data' in scene:
            layout.operator("scene.process_json_file")
            layout.operator("scene.distribut_instances")
            layout.operator("object.realize_collection")
            layout.prop(context.scene, "symphonytrees")
            layout.operator("object.apply_music_to_collections")
            layout.operator("scene.calculate_required_frames")
        self.draw_music_panel(context)

def register():
    bpy.utils.register_class(DuplicateCollectionOperator)
    bpy.utils.register_class(RealizeCollectionOperator)
    bpy.utils.register_class(ApplyMusicOperator)
    bpy.utils.register_class(ReadJSONFileOperator)
    bpy.utils.register_class(ProcessJSONFileOperator)
    bpy.utils.register_class(DistributeInstancesOperator)
    bpy.utils.register_class(CalculateRequiredFramesOperator)
    bpy.utils.register_class(TrackSectionItem)
    bpy.utils.register_class(TrackNoteItem)
    bpy.utils.register_class(MusicDataProperties)
    bpy.utils.register_class(PixelSymphonyPanel)
    bpy.types.Scene.music_data_props = bpy.props.PointerProperty(type=MusicDataProperties)
    bpy.types.Scene.my_collection_enum = bpy.props.EnumProperty(items=get_collection_names)
    bpy.types.Scene.target_collection_enum = bpy.props.EnumProperty(items=get_collection_names)
    bpy.types.Scene.symphonytrees = bpy.props.EnumProperty(items=find_pixel_symphony_node_trees)
    bpy.types.Scene.make_single = bpy.props.BoolProperty(
        name="Make single user",
        description="Makes each collection a single user.",
        default=False
    )

def unregister():
    bpy.utils.unregister_class(DuplicateCollectionOperator)
    bpy.utils.unregister_class(RealizeCollectionOperator)
    bpy.utils.unregister_class(ApplyMusicOperator)
    bpy.utils.unregister_class(ReadJSONFileOperator)
    bpy.utils.unregister_class(ProcessJSONFileOperator)
    bpy.utils.unregister_class(DistributeInstancesOperator)
    bpy.utils.unregister_class(CalculateRequiredFramesOperator)
    bpy.utils.unregister_class(PixelSymphonyPanel)
    del bpy.types.Scene.music_data_props
    bpy.utils.unregister_class(MusicDataProperties)
    bpy.utils.unregister_class(TrackNoteItem)
    bpy.utils.unregister_class(TrackSectionItem)
    del bpy.types.Scene.make_single
    del bpy.types.Scene.my_collection_enum
    del bpy.types.Scene.target_collection_enum
    del bpy.types.Scene.symphonytrees

# if __name__ == "__main__":
#     register()
