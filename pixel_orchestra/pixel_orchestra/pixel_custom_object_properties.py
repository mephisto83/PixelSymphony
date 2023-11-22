

import bpy

class PIX_CUSTOM_OBJECT_PROPS_OT_add_edit(bpy.types.Operator):
    """Add or Edit a Pix Custom Object Property"""
    bl_idname = "object.pix_add_edit_custom_object_prop"
    bl_label = "Add/Edit Pix Custom Object Property"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        wm = context.window_manager
        obj = context.active_object
        full_prop_name = "pix_" + wm.pix_new_object_prop_name
        obj[full_prop_name] = wm.pix_new_object_prop_value
        return {'FINISHED'}

def add_unique_prop(new_value, existing_string):
    """
    Adds a new value to a comma-delimited string, ensuring it doesn't appear twice.

    :param new_value: The new value to be added.
    :param existing_string: The existing comma-delimited string.
    :return: Updated comma-delimited string with the new value added if not already present.
    """
    # Split the existing string into a list
    existing_values = existing_string.split(',') if existing_string else []

    # Add the new value only if it's not already in the list
    if new_value not in existing_values:
        existing_values.append(new_value)

    # Return the updated string
    return ','.join(existing_values)

class PIX_CUSTOM_OBJECT_PROPS_OT_batch_add_edit(bpy.types.Operator):
    """Set Auto Property"""
    bl_idname = "object.pix_batch_add_edit_custom_object_prop"
    bl_label = "Add/Edit Pix Auto Custom Object Property"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        wm = context.window_manager
        obj = context.active_object
        full_prop_name = "pix_" + wm.pix_new_object_prop_name
        obj[full_prop_name] = wm.pix_new_object_prop_value or 0.0
        full_prop_name = "pix_properties"
        props = f"{wm.pix_new_object_prop_name}"
        temp = ""
        if full_prop_name in obj:
            temp = obj[full_prop_name]
        obj[full_prop_name] = add_unique_prop(props, temp) 

        # full_prop_name = "pix_properties_types"
        # props = f"Float"
        # obj[full_prop_name] = props

        
        full_prop_name = "pix_" + wm.pix_new_object_prop_name + "_properties"
        obj[full_prop_name] = "var1"
        
        full_prop_name = "pix_" + wm.pix_new_object_prop_name + "_property_paths"
        obj[full_prop_name] = wm.pix_new_object_prop_name

        
        full_prop_name = "pix_" + wm.pix_new_object_prop_name + "_expression"
        obj[full_prop_name] = "var1"

        return {'FINISHED'}

class PIX_CUSTOM_PROPS_OT_delete(bpy.types.Operator):
    """Delete a Pix Custom Object Property"""
    bl_idname = "object.pix_delete_custom_object_prop"
    bl_label = "Delete Pix Custom Property"

    prop_name: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        obj = context.active_object
        if self.prop_name in obj:
            del obj[self.prop_name]
        return {'FINISHED'}

class PIX_CUSTOM_PROPS_OT_select(bpy.types.Operator):
    """Select a Pix Custom Property"""
    bl_idname = "object.pix_select_custom_object_prop"
    bl_label = "Select Pix Custom Property"

    prop_name: bpy.props.StringProperty()
    prop_value: bpy.props.StringProperty()

    def execute(self, context):
        wm = context.window_manager
        wm.pix_new_object_prop_name = self.prop_name[4:]  # Remove 'pix_' prefix
        wm.pix_new_object_prop_value = self.prop_value
        return {'FINISHED'}

def draw_pix_custom_props_panel(self, context):
    layout = self.layout
    wm = context.window_manager
    obj = context.active_object

    if obj and obj.type == 'MESH':
        for prop in obj.keys():
            if prop.startswith("pix_"):
                row = layout.row()
                prop_select_op = row.operator("object.pix_select_custom_object_prop", text="", icon="DOT")
                prop_select_op.prop_name = prop
                prop_select_op.prop_value = str(obj[prop])
                row.label(text=f"{prop}: {obj[prop]}")
                prop_delete_op = row.operator("object.pix_delete_custom_object_prop", text="", icon="X")
                prop_delete_op.prop_name = prop

        layout.separator()
        layout.label(text="Add/Edit Property:")
        layout.prop(wm, "pix_new_object_prop_name")
        layout.prop(wm, "pix_new_object_prop_value")
        layout.operator("object.pix_add_edit_custom_object_prop", text="Add/Edit")
        layout.operator("object.pix_batch_add_edit_custom_object_prop", text=f"Auto {wm.pix_new_object_prop_name}")

def register():
    bpy.utils.register_class(PIX_CUSTOM_OBJECT_PROPS_OT_add_edit)
    bpy.utils.register_class(PIX_CUSTOM_OBJECT_PROPS_OT_batch_add_edit)
    bpy.utils.register_class(PIX_CUSTOM_PROPS_OT_delete)
    bpy.utils.register_class(PIX_CUSTOM_PROPS_OT_select)
    bpy.types.OBJECT_PT_custom_props.append(draw_pix_custom_props_panel)
    bpy.types.WindowManager.pix_new_object_prop_name = bpy.props.StringProperty(name="Pix Prop Name")
    bpy.types.WindowManager.pix_new_object_prop_value = bpy.props.StringProperty(name="Pix Prop Value")

def unregister():
    bpy.utils.unregister_class(PIX_CUSTOM_OBJECT_PROPS_OT_add_edit)
    bpy.utils.unregister_class(PIX_CUSTOM_OBJECT_PROPS_OT_batch_add_edit)
    bpy.utils.unregister_class(PIX_CUSTOM_PROPS_OT_delete)
    bpy.utils.unregister_class(PIX_CUSTOM_PROPS_OT_select)
    bpy.types.OBJECT_PT_custom_props.remove(draw_pix_custom_props_panel)
    del bpy.types.WindowManager.pix_new_object_prop_name
    del bpy.types.WindowManager.pix_new_object_prop_value

# if __name__ == "__main__":
#     register()
