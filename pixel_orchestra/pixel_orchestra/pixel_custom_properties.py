

import bpy

class PIX_CUSTOM_PROPS_OT_add_edit(bpy.types.Operator):
    """Add or Edit a Pix Custom Property"""
    bl_idname = "node.pix_add_edit_custom_prop"
    bl_label = "Add/Edit Pix Custom Property"

    @classmethod
    def poll(cls, context):
        return context.active_node is not None

    def execute(self, context):
        wm = context.window_manager
        node = context.active_node
        full_prop_name = "pix_" + wm.pix_new_prop_name
        node[full_prop_name] = wm.pix_new_prop_value
        return {'FINISHED'}

class PIX_CUSTOM_PROPS_OT_delete(bpy.types.Operator):
    """Delete a Pix Custom Property"""
    bl_idname = "node.pix_delete_custom_prop"
    bl_label = "Delete Pix Custom Property"

    prop_name: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return context.active_node is not None

    def execute(self, context):
        node = context.active_node
        if self.prop_name in node:
            del node[self.prop_name]
        return {'FINISHED'}

class PIX_CUSTOM_PROPS_OT_select(bpy.types.Operator):
    """Select a Pix Custom Property"""
    bl_idname = "node.pix_select_custom_prop"
    bl_label = "Select Pix Custom Property"

    prop_name: bpy.props.StringProperty()
    prop_value: bpy.props.StringProperty()

    def execute(self, context):
        wm = context.window_manager
        wm.pix_new_prop_name = self.prop_name[4:]  # Remove 'pix_' prefix
        wm.pix_new_prop_value = self.prop_value
        return {'FINISHED'}

def draw_pix_custom_props_panel(self, context):
    layout = self.layout
    wm = context.window_manager
    node = context.active_node

    if node:
        for prop in node.keys():
            if prop.startswith("pix_"):
                row = layout.row()
                prop_select_op = row.operator("node.pix_select_custom_prop", text="", icon="DOT")
                prop_select_op.prop_name = prop
                prop_select_op.prop_value = str(node[prop])
                row.label(text=f"{prop}: {node[prop]}")
                prop_delete_op = row.operator("node.pix_delete_custom_prop", text="", icon="X")
                prop_delete_op.prop_name = prop

        layout.separator()
        layout.label(text="Add/Edit Property:")
        layout.prop(wm, "pix_new_prop_name")
        layout.prop(wm, "pix_new_prop_value")
        layout.operator("node.pix_add_edit_custom_prop", text="Add/Edit")
def register_custom_properties():
    bpy.types.Object.brightness = bpy.props.FloatProperty(
        name="Brightness",
        description="Control the brightness",
        default=0.0,
        min=-10000000.0,
        max=10000000.0
    )
    bpy.types.Object.location_x = bpy.props.FloatProperty(
        name="Location X",
        description="Location X",
        default=0.0,
        min=-10000000.0,
        max=10000000.0
    )
    bpy.types.Object.location_y = bpy.props.FloatProperty(
        name="Location Y",
        description="Location Y",
        default=0.0,
        min=-10000000.0,
        max=10000000.0
    )
    bpy.types.Object.location_z = bpy.props.FloatProperty(
        name="Location Z",
        description="Location Z",
        default=0.0,
        min=-10000000.0,
        max=10000000.0
    )
    bpy.types.Object.scale_x = bpy.props.FloatProperty(
        name="Scale X",
        description="Scale X",
        default=0.0,
        min=-10000000.0,
        max=10000000.0
    )
    bpy.types.Object.scale_y = bpy.props.FloatProperty(
        name="Scale Y",
        description="Scale Y",
        default=0.0,
        min=-10000000.0,
        max=10000000.0
    )
    bpy.types.Object.scale_z = bpy.props.FloatProperty(
        name="Scale Z",
        description="Scale Z",
        default=0.0,
        min=-10000000.0,
        max=10000000.0
    )
    bpy.types.Object.rotation_x = bpy.props.FloatProperty(
        name="Rotation X",
        description="Rotation X",
        default=0.0,
        min=-10000000.0,
        max=10000000.0
    )
    bpy.types.Object.rotation_y = bpy.props.FloatProperty(
        name="Rotation Y",
        description="Rotation Y",
        default=0.0,
        min=-10000000.0,
        max=10000000.0
    )
    bpy.types.Object.rotation_z = bpy.props.FloatProperty(
        name="Rotation Z",
        description="Rotation Z",
        default=0.0,
        min=-10000000.0,
        max=10000000.0
    )

def unregister_custom_properties():
    del bpy.types.Object.brightness
    del bpy.types.Object.location_x
    del bpy.types.Object.location_y
    del bpy.types.Object.location_z

    del bpy.types.Object.scale_x
    del bpy.types.Object.scale_y
    del bpy.types.Object.scale_z

    del bpy.types.Object.rotation_x
    del bpy.types.Object.rotation_y
    del bpy.types.Object.rotation_z

def register():
    register_custom_properties()
    bpy.utils.register_class(PIX_CUSTOM_PROPS_OT_add_edit)
    bpy.utils.register_class(PIX_CUSTOM_PROPS_OT_delete)
    bpy.utils.register_class(PIX_CUSTOM_PROPS_OT_select)
    bpy.types.NODE_PT_active_node_properties.append(draw_pix_custom_props_panel)
    bpy.types.WindowManager.pix_new_prop_name = bpy.props.StringProperty(name="Pix Prop Name")
    bpy.types.WindowManager.pix_new_prop_value = bpy.props.StringProperty(name="Pix Prop Value")

def unregister():
    unregister_custom_properties()
    bpy.utils.unregister_class(PIX_CUSTOM_PROPS_OT_add_edit)
    bpy.utils.unregister_class(PIX_CUSTOM_PROPS_OT_delete)
    bpy.utils.unregister_class(PIX_CUSTOM_PROPS_OT_select)
    bpy.types.NODE_PT_active_node_properties.remove(draw_pix_custom_props_panel)
    del bpy.types.WindowManager.pix_new_prop_name
    del bpy.types.WindowManager.pix_new_prop_value

# if __name__ == "__main__":
#     register()
