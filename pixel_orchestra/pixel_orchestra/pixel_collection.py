
import bpy

PIXEL_COLLECTION = "PIXEL_COLLECTION"

class COLLECTION_OT_add_pixel_collection_property(bpy.types.Operator):
    """Add PIXEL_COLLECTION Property to Active Collection"""
    bl_idname = "collection.add_pixel_collection_property"
    bl_label = "Add PIXEL_COLLECTION"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        active_collection = context.collection

        if active_collection is None:
            self.report({'ERROR'}, "No active collection selected.")
            return {'CANCELLED'}

        active_collection["PIXEL_COLLECTION"] = True
        self.report({'INFO'}, f"PIXEL_COLLECTION property added to collection: {active_collection.name}")
        return {'FINISHED'}

class COLLECTION_PT_custom_panel(bpy.types.Panel):
    """Creates a Panel in the Collection properties window"""
    bl_label = "PIXEL Collection Panel"
    bl_idname = "COLLECTION_PT_custom_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "collection"  # This places the panel in the Collection properties tab

    def draw(self, context):
        layout = self.layout

        layout.label(text="Custom Collection Properties")

        # The operator button
        layout.operator(COLLECTION_OT_add_pixel_collection_property.bl_idname)

def register():
    bpy.utils.register_class(COLLECTION_OT_add_pixel_collection_property)
    bpy.utils.register_class(COLLECTION_PT_custom_panel)

def unregister():
    bpy.utils.unregister_class(COLLECTION_OT_add_pixel_collection_property)
    bpy.utils.unregister_class(COLLECTION_PT_custom_panel)
