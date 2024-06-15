
import bpy
import uuid
import json
import mathutils
import bmesh
import random
from mathutils import Vector
from bpy.props import CollectionProperty, StringProperty
from .pixel_symphony import read_file_as_text


class ReadPixelTetrisFileOperator(bpy.types.Operator):
    """Operator to read a JSON file and store its content in a custom property"""
    bl_idname = "object.read_pixel_tetris_file"
    bl_label = "Read Pixel Tetris File"
    bl_options = {'REGISTER', 'UNDO'}

    # Define properties for the operator
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    property_name: bpy.props.StringProperty(default="json_data")
    enable_floor: bpy.props.BoolProperty(name="Enable Floor", default=True)  # New property for enabling/disabling the floor

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
                solutions = json.load(file)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to read or parse the file: {e}")
            return {'CANCELLED'}

        self.report({'INFO'}, f"JSON data set to property '{self.property_name}'")
        # Select all objects in the scene
        delete_meshes_with_custom_property("MORT_OBJECT")
        # Process 'space' key
        # if 'space' in data:
        #     space_data = data['space']
        #     points = space_data['points']
        #     translation = space_data['translation']

        #     for point in points:
        #         create_cube_at_point(point, translation)

        # Process 'shapes' key
        y_offset = 0
        x_offset = 0
        x_buffer = 2
        lib_added = False
        for data in solutions:
            if 'library' in data and not lib_added:
                lib_added = True
                num = 0
                lib_meshes = []
                for shape in data['library']:
                    shape_type = shape['shape_type']
                    criteria = shape['criteria']
                    if not shape_type in material_dic:
                        material_dic[shape_type] = create_material(f"shape-{shape_type}", random_color())
                    meshes = create_meshes_from_json(shape)
                    depths = []
                    for mesh in meshes:
                        height, width, depth = get_mesh_dimensions(mesh)
                        x_offset = max([width, x_offset])
                        mesh.location.y = y_offset
                        mesh.location.x = -12
                        mesh.location.z = 4
                        lib_meshes.append(mesh)
                        depths.append(depth)
                        assign_material_to_object(mesh.name, material_dic[shape_type])
                    y_offset = max(depths) + y_offset
                    num = num + 1
                for mesh in lib_meshes:
                    mesh.location.x = -(x_offset + x_buffer)
            
            if context.scene.enable_floor:
                if 'space' in data:
                    num = 0
                    shape = data['space']
                    shape_type = -1
                    criteria = (0,0,0)
                    if not shape_type in material_dic:
                        material_dic[shape_type] = create_material(f"shape-{shape_type}", criteria)
                    meshes = create_meshes_from_json(shape)
                    for mesh in meshes:
                        mesh.location.z = -.1
                        assign_material_to_object(mesh.name, material_dic[shape_type])
                    num = num + 1

            if 'shapes' in data:
                num = 0
                for shape in data['shapes']:
                    shape_type = shape['shape_type']
                    criteria = shape['criteria']
                    if not shape_type in material_dic:
                        material_dic[shape_type] = create_material(f"shape-{shape_type}", random_color())
                    meshes = create_meshes_from_json(shape)
                    for mesh in meshes:
                        assign_material_to_object(mesh.name, material_dic[shape_type])
                    num = num + 1

        return {'FINISHED'}

class ReadPixelPolygons(bpy.types.Operator):
    """Operator to read a JSON file and store its content in a custom property"""
    bl_idname = "object.read_pixel_polygons"
    bl_label = "Read Pixel Tetris File"
    bl_options = {'REGISTER', 'UNDO'}

    # Define properties for the operator
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    property_name: bpy.props.StringProperty(default="json_data")
    enable_floor: bpy.props.BoolProperty(name="Enable Floor", default=True)  # New property for enabling/disabling the floor

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
                data = json.load(file)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to read or parse the file: {e}")
            return {'CANCELLED'}

        self.report({'INFO'}, f"JSON data set to property '{self.property_name}'")
        # Select all objects in the scene
        for shape in data:
            shape_type = shape['shape_type']
            if not shape_type in material_dic:
                material_dic[shape_type] = create_material(f"shape-{shape_type}", random_color())
            meshes = create_meshes_from_json(shape)
            for mesh in meshes:
                assign_material_to_object(mesh.name, material_dic[shape_type])

        return {'FINISHED'}

class ClearPixelTetrisOperator(bpy.types.Operator):
    """Operator to read a JSON file and store its content in a custom property"""
    bl_idname = "object.clear_pixel_tetris_pieces"
    bl_label = "Clear Pixel Tetris"
    bl_options = {'REGISTER', 'UNDO'}

    # Define properties for the operator
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    property_name: bpy.props.StringProperty(default="json_data")
    enable_floor: bpy.props.BoolProperty(name="Enable Floor", default=True)  # New property for enabling/disabling the floor

    def execute(self, context):
        delete_meshes_with_custom_property("MORT_OBJECT")
        
        return {'FINISHED'}


class MESH_OT_WriteBoundaryVerticesToClipboard(bpy.types.Operator):
    """Write Boundary Vertices to Clipboard"""
    bl_idname = "mesh.write_boundary_vertices_to_clipboard"
    bl_label = "Write Boundary Vertices to Clipboard"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH'

    def execute(self, context):
        try:
            meshes = get_selected_objects()
            objects = []
            for mesh in meshes:
                json_data = write_boundary_vertices_to_json(mesh)
                objects.append(json_data)
            context.window_manager.clipboard = json.dumps(objects)
            self.report({'INFO'}, "Boundary vertices written to clipboard")
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        return {'FINISHED'}
    

def delete_meshes_with_custom_property(property_name):
    """
    Deletes all mesh objects in the current scene that have a specified custom property.

    Args:
    property_name (str): The name of the custom property to check for.
    """
    # Create a list to hold objects to be removed
    objects_to_remove = []

    # Iterate over all objects in the scene
    for obj in bpy.context.scene.objects:
        # Check if the object is a mesh and has the custom property
        if obj.type == 'MESH' and property_name in obj:
            objects_to_remove.append(obj)

    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

    # Select and delete the objects
    for obj in objects_to_remove:
        obj.select_set(True)
        bpy.ops.object.delete()

def random_color():
    """
    Generates a random color vector.

    Returns:
        tuple: A tuple of three floats representing the RGB components of the color.
    """
    return (random.random(), random.random(), random.random())

def write_boundary_vertices_to_json(mesh_object):
    """
    Writes the boundary vertices of a mesh object to a JSON object in CCW order,
    including their global position.

    Args:
    mesh_object (bpy.types.Object): The mesh object.

    Returns:
    str: A JSON string containing the boundary vertices with their global position.
    """

    if mesh_object.type != 'MESH':
        raise ValueError("Provided object is not a mesh")

    # Create a bmesh from the object mesh
    bm = bmesh.new()
    bm.from_mesh(mesh_object.data)
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()

    # Find boundary edges
    boundary_edges = [edge for edge in bm.edges if edge.is_boundary]

    # Start with an arbitrary boundary edge and sort in CCW order
    boundary_loop = []
    edge = boundary_edges.pop(0)
    while boundary_edges:
        boundary_loop.append(edge)
        # Get the next edge sharing the last vertex
        next_vertex = edge.verts[1]
        next_edge = next(e for e in boundary_edges if next_vertex in e.verts)
        boundary_edges.remove(next_edge)
        edge = next_edge

    # Add the last edge to the loop
    boundary_loop.append(edge)

    # Extract vertices in CCW order and apply the world matrix to get global coordinates
    world_matrix = mesh_object.matrix_world
    vertices = [world_matrix @ edge.verts[0].co for edge in boundary_loop]

    # Convert to JSON
    json_data = json.dumps({"vertices": [v[:] for v in vertices]}, default=lambda x: list(x))

    # Clean up
    bm.free()

    return json_data

def get_selected_objects():
    """
    Returns a list of all currently selected objects in Blender.

    Returns:
    list: A list of selected bpy.types.Object instances.
    """
    return [obj for obj in bpy.context.selected_objects]

def create_meshes_from_json(data):
    # Parsing JSON data

    # Extracting vertices from polygons
    polygons = data['polygons']
    # Parsing JSON data
    res = []
    for polygon in polygons:
        obj = create_mesh_from_json({'polygons':[polygon],'translation': data['translation']})
        res.append(obj)
    mesh = res[0]
    if len(polygons) > 1:
        for i in range(1, len(polygons)):
            if res[i]:
                join_meshes(mesh, res[i])
    return [mesh]

def create_mesh_from_json(data):
    # Parsing JSON data

    # Extracting vertices from polygons
    polygons = data['polygons']
    all_vertices = [tuple(v + [0]) for poly in polygons for v in poly]  # Z-coordinate is assumed to be 0
    edges = []  # Assuming no explicit edges are defined

    # Create a new mesh
    mesh = bpy.data.meshes.new('MeshObject')

    # Create a new object with the mesh
    obj = bpy.data.objects.new('MeshObject', mesh)

    # Link the object to the current scene
    bpy.context.collection.objects.link(obj)

    # Set the location to the scene's origin
    obj.location = bpy.context.scene.cursor.location

    # Create a bmesh to edit the mesh
    bm = bmesh.new()

    # Add vertices to the bmesh
    bm_verts = [bm.verts.new(v) for v in all_vertices]
    bm.verts.ensure_lookup_table()  # Ensure the lookup table is updated

    # Add faces to the bmesh
    for poly in polygons:
        face_verts = [bm_verts[i] for i in range(len(poly))]
        bm.faces.new(face_verts)

    # Update the bmesh to the mesh
    bm.to_mesh(mesh)
    bm.free()

    # Apply translation
    translation = data['translation']
    obj.location.x += translation[0]
    obj.location.y += translation[1]
    obj.location.z += 0  # Assuming Z translation is not required

    # Add custom property 'MORT_OBJECT' set to True
    obj["MORT_OBJECT"] = True

    return obj

material_dic = {}
def assign_material_to_object(obj_name, material):
    """
    Assigns a given material to an object.

    Parameters:
    obj_name (str): The name of the object to which the material will be assigned.
    material (bpy.types.Material): The material to assign to the object.
    """

    # Get the object from the scene
    obj = bpy.data.objects.get(obj_name)
    if obj is None:
        print(f"No object named '{obj_name}' found in the scene.")
        return

    # Assign the material to the object
    if obj.data.materials:
        # Replace the first material slot
        obj.data.materials[0] = material
    else:
        # Add material slot and assign material
        obj.data.materials.append(material)

def create_material(name, color):
    """
    Creates a new material with the specified name and diffuse color.

    Parameters:
    name (str): The name of the material.
    color (tuple): A tuple of three float values representing the RGB color.
    """

    # Create a new material
    material = bpy.data.materials.new(name=name)

    # Enable 'Use Nodes'
    material.use_nodes = True
    nodes = material.node_tree.nodes

    # Get the Principled BSDF node
    principled_bsdf = nodes.get('Principled BSDF')
    if principled_bsdf is not None:
        principled_bsdf.inputs['Base Color'].default_value = (*color, 1)  # RGB + Alpha

    return material

def create_cube_at_point(point, translation):
    # Create a cube at the specified point
    bpy.ops.mesh.primitive_cube_add(size=1, enter_editmode=False, align='WORLD', location=(point[0], point[1], 0))
    print(f"create cube at {point}, {translation}")
    # Get the reference to the newly created cube
    cube = bpy.context.active_object

    # Apply the translation offset
    cube.location.x += translation[0]
    cube.location.y += translation[1]
    return cube


def get_mesh_dimensions(obj):
    """
    Get the dimensions (height, width, depth) of a mesh object in Blender.

    Args:
    obj (bpy.types.Object): The mesh object.

    Returns:
    tuple: A tuple containing the height, width, and depth of the mesh.
    """
    if obj.type != 'MESH':
        raise ValueError("Object is not a mesh")

    # Create a bmesh from the object mesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)

    # Get the bounds
    min_x, max_x = min([v.co.x for v in bm.verts]), max([v.co.x for v in bm.verts])
    min_y, max_y = min([v.co.y for v in bm.verts]), max([v.co.y for v in bm.verts])
    min_z, max_z = min([v.co.z for v in bm.verts]), max([v.co.z for v in bm.verts])

    # Calculate width, depth, and height
    width = max_x - min_x
    depth = max_y - min_y
    height = max_z - min_z

    bm.free()

    return (height, width, depth)


def join_meshes(obj1, obj2):
    """
    Joins two mesh objects into a single object.

    Args:
    obj1 (bpy.types.Object): The first mesh object.
    obj2 (bpy.types.Object): The second mesh object.
    """

    # Ensure both objects are meshes
    if obj1.type != 'MESH' or obj2.type != 'MESH':
        raise ValueError("Both objects must be of type 'MESH'")

    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

    # Select both objects
    obj1.select_set(True)
    obj2.select_set(True)

    # Set the context's active object
    bpy.context.view_layer.objects.active = obj1

    # Join the objects
    bpy.ops.object.join()


class PixelTetrisPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Pixel Tetris Panel"
    bl_idname = "OBJECT_PT_pixeltetrissymphony"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        # Checkbox for enabling/disabling the floor
        # Directly accessing the operator's property
        layout.prop(scene, "enable_floor", text="Enable Floor")
        layout.operator("object.read_pixel_tetris_file")
        layout.operator("object.clear_pixel_tetris_pieces")
        layout.operator("mesh.write_boundary_vertices_to_clipboard")
        layout.operator("object.read_pixel_polygons")


def register():
    bpy.types.Scene.enable_floor = bpy.props.BoolProperty(
        name="Enable Floor",
        description="Enable or disable the floor",
        default=True
    )
    bpy.utils.register_class(ReadPixelTetrisFileOperator)
    bpy.utils.register_class(PixelTetrisPanel)
    bpy.utils.register_class(MESH_OT_WriteBoundaryVerticesToClipboard)
    bpy.utils.register_class(ClearPixelTetrisOperator)
    bpy.utils.register_class(ReadPixelPolygons)

def unregister():
    bpy.utils.unregister_class(ReadPixelTetrisFileOperator)
    bpy.utils.unregister_class(PixelTetrisPanel)
    bpy.utils.unregister_class(MESH_OT_WriteBoundaryVerticesToClipboard)
    bpy.utils.unregister_class(ClearPixelTetrisOperator)
    bpy.utils.unregister_class(ReadPixelPolygons)
    del bpy.types.Scene.enable_floor
# if __name__ == "__main__":
#     register()
