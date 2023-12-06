import bpy
import bmesh  # Importing the bmesh module
import random
from mathutils import Vector, Quaternion
import mathutils

def get_pix_properties_items(self, context):
    pix_props = ["brightness", "color_green", "color_blue", "color_red", "location_x", "location_y", "location_z", "scale_x",
                 "scale_y", "scale_z", "rotation_x", "rotation_y", "rotation_z"]
    return [(i, i, i) for i in pix_props]

def get_meshes_in_collection(collection_name):
    """
    Retrieves all mesh objects in the specified collection.

    Args:
    collection_name (str): The name of the collection to search in.

    Returns:
    list: A list of mesh objects found in the specified collection.
    """
    collection = bpy.data.collections.get(collection_name)
    if not collection:
        raise ValueError(f"Collection '{collection_name}' not found")

    meshes = [obj for obj in collection.objects if obj.type == 'MESH']
    return meshes

def pin_collection_to_face(instance, object_data):
    # Ensure object_data is a mesh object
    if not isinstance(object_data.data, bpy.types.Mesh):
        print("object_data is not a Mesh object.")
        return

    # Ensure object_data's mesh has faces
    if len(object_data.data.polygons) == 0:
        print("No faces in the mesh.")
        return

    # Select a random face
    face = random.choice(object_data.data.polygons)

    # Calculate the normal of the face in local space
    normal_local = face.normal

    # Calculate the face center in local space
    face_center_local = sum((object_data.data.vertices[v].co for v in face.vertices), Vector()) / len(face.vertices)

    # Set the location of the instance to the face center (relative to the parent)
    instance.location = face_center_local

    # Align instance's vertical axis (0,0,1) with the face normal
    z_axis = Vector((0, 0, 1))
    rotation_quaternion = z_axis.rotation_difference(normal_local)
    instance.rotation_mode = 'QUATERNION'
    instance.rotation_quaternion = rotation_quaternion

    # Parent the instance to the object
    instance.parent = object_data

    # Update the scene (if needed)
    bpy.context.view_layer.update()

    print("Instance placed at: ", instance.location)
    print("Instance rotation: ", instance.rotation_quaternion)


def pin_collection_to_face2(instance, mesh_data):
    # Random location within the specified range
    # x = random.uniform(x_min, x_max)
    # y = random.uniform(y_min, y_max)
    # z = 0  # Assuming you want to place them on the plane
    # Check if plane_obj is the correct type
    # if not isinstance(plane_obj, bpy.types.Object):
    #     print(f"Provided plane is not an object: {plane_obj}")
    #     return
    print(instance)
    print(mesh_data)
    # {
    #     'face': None,
    #     'normal': None,
    #     'world_position': None,
    #     'rotation_euler': None
    # }
    # Apply the plane's rotation to the instance
    # instance.rotation_euler = mesh_data["rotation_euler"]

    # Set the instance's location relative to the plane
    # instance.location = mesh_data['world_position'] 

    # Link the instance to the same collection as the plane
    # plane_collection = plane_obj.users_collection[0] if plane_obj.users_collection else bpy.context.collection
    # plane_collection.objects.link(instance)
    instance.location = Vector((0,0,0))
    # Parent the instance to the plane
    instance.parent = mesh_data

def distribute_collection_to_face(instance, mesh_data):
    # Random location within the specified range
    # x = random.uniform(x_min, x_max)
    # y = random.uniform(y_min, y_max)
    # z = 0  # Assuming you want to place them on the plane
    # Check if plane_obj is the correct type
    # if not isinstance(plane_obj, bpy.types.Object):
    #     print(f"Provided plane is not an object: {plane_obj}")
    #     return
    print(instance)
    print(mesh_data)
    # {
    #     'face': None,
    #     'normal': None,
    #     'world_position': None,
    #     'rotation_euler': None
    # }
    # Apply the plane's rotation to the instance
    instance.rotation_euler = mesh_data["rotation_euler"]

    # Set the instance's location relative to the plane
    instance.location = mesh_data['world_position'] 

    # Link the instance to the same collection as the plane
    # plane_collection = plane_obj.users_collection[0] if plane_obj.users_collection else bpy.context.collection
    # plane_collection.objects.link(instance)

    # Parent the instance to the plane
    instance.parent = None

def get_mesh_data(mesh_object):
    """
    Extracts faces, normals, world positions, and rotations (Euler) of each face of the given mesh object.

    Args:
    mesh_object (bpy.types.Object): The mesh object to extract data from.

    Returns:
    list of dicts: Each dict contains data for a face including vertices, normal, world position, and rotation.
    """

    # Ensure the object is a mesh
    if mesh_object.type != 'MESH':
        raise ValueError("Provided object is not a mesh")

    # Create a bmesh from the mesh
    mesh = mesh_object.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    # Calculate normals
    bm.normal_update()
    mesh.calc_normals()

    # Transform to world coordinates
    bm.transform(mesh_object.matrix_world)

    # Extract data
    results = []
    for face in bm.faces:
        info = {}
        # Face vertices
        face_verts = [vert.co.copy() for vert in face.verts]

        # Face normal
        normal = face.normal.copy()

        # Face center in world coordinates
        world_position = mesh_object.matrix_world @ face.calc_center_median()

        # Calculate rotation (Euler) aligned with the face normal
        rotation_matrix = normal.to_track_quat('Z', 'Y').to_euler()
        
        # Append data
        info['face'] = face_verts
        info['normal'] = normal
        info['world_position'] = world_position
        info['rotation_euler'] = rotation_matrix
        results.append(info)

    # Free the bmesh
    bm.free()

    return results
