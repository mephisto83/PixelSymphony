bl_info = {
    "name": "Pixel Orchestra",
    "description": "Pixel Orchestra",
    "author": "Andrew Porter",
    "version": (0, 0, 1),
    "blender": (3, 6, 0),
    "location": "Global/Text Editor",
    "warning": "",
    "wiki_url": "",
    "category": "Development",
}


import sys
import importlib

modules = [
    'pixel_symphony', 
    'pixel_custom_properties', 
    'pixel_custom_object_properties', 
    'pixel_symphony_nodes', 
    'pixel_rendering', 
    'pixel_utils', 
    'pixel_collection',
    'pixel_tetris'
]

for mod in modules:
    if f"{__package__}.{mod}" in sys.modules:
        importlib.reload(sys.modules[f"{__package__}.{mod}"])
    else:
        globals()[mod] = importlib.import_module(f"{__package__}.{mod}")

def register():
    for mod in modules:
        if mod in globals():
            if hasattr(globals()[mod], 'register'):
                globals()[mod].register()

def unregister():
    for mod in modules:
        if mod in globals():
            if hasattr(globals()[mod], 'unregister'):
                globals()[mod].unregister()

if __name__ == "__main__":
    register()