import bpy


class RENDER_OT_SpecificFramesModal(bpy.types.Operator):
    """Render Specific Frames in Modal Operator"""
    bl_idname = "render.specific_frames_modal"
    bl_label = "Render Specific Frames (Modal)"
    bl_options = {'REGISTER'}

    _timer = None
    frames_to_render = [10, 20, 30]  # Replace with your frames list
    frame_index = 0

    def modal(self, context, event):
        if event.type == 'TIMER':
            if self.frame_index < len(self.frames_to_render):
                frame = self.frames_to_render[self.frame_index]
                context.scene.frame_set(frame)
                bpy.ops.render.render(write_still=True)  # Render the frame
                self.frame_index += 1
            else:
                self.finish(context)
                return {'FINISHED'}
        return {'PASS_THROUGH'}

    def execute(self, context):
        self.frame_index = 0

        # Store original frame settings
        self.original_frame_start = context.scene.frame_start
        self.original_frame_end = context.scene.frame_end

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def finish(self, context):
        # Restore original frame settings
        context.scene.frame_start = self.original_frame_start
        context.scene.frame_end = self.original_frame_end
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

def draw_menu(self, context):
    self.layout.operator(RENDER_OT_SpecificFramesModal.bl_idname)

def register():
    bpy.utils.register_class(RENDER_OT_SpecificFramesModal)
    bpy.types.TOPBAR_MT_render.append(draw_menu)

def unregister():
    bpy.utils.unregister_class(RENDER_OT_SpecificFramesModal)
    bpy.types.TOPBAR_MT_render.remove(draw_menu)


# if __name__ == "__main__":
#     register()

def get_material_state(material):
    """ Helper function to get the state of material nodes. """
    state = {}
    if material.use_nodes and material.node_tree:
        for node in material.node_tree.nodes:
            node_state = {}
            for prop_name, prop_value in node.items():
                # Record relevant properties (like values, colors, factors)
                if isinstance(prop_value, (float, int, str)):
                    node_state[prop_name] = prop_value
                elif isinstance(prop_value, bpy.types.FloatVectorProperty):
                    # Assuming it's a color. Note: This may need refinement based on specific use cases.
                    node_state[prop_name] = tuple(prop_value)
            state[node.name] = node_state
    return state

def frames_to_generate():
    """
    Detects changes in transformation properties and material node values of objects in the scene across all frames,
    comparing against the last change, and returns a list of frames where changes were detected.

    Returns:
    list: A list of frame numbers where changes were detected.
    """

    # Store the initial state
    states = {}
    for obj in bpy.context.scene.objects:
        obj_state = {
            'location': tuple(obj.location),
            'rotation_euler': tuple(obj.rotation_euler),
            'scale': tuple(obj.scale),
            'materials': {}
        }
        # Record initial material states
        for mat_slot in obj.material_slots:
            if mat_slot.material:
                obj_state['materials'][mat_slot.name] = get_material_state(mat_slot.material)

        states[obj.name] = obj_state

    # List to hold frames that need generation
    frames_needed = []

    # Iterate over all frames
    for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end + 1):
        bpy.context.scene.frame_set(frame)
        change_detected = False

        # Check each object for changes
        for obj in bpy.context.scene.objects:
            current_obj_state = states[obj.name]

            # Check for transformation changes
            if (tuple(obj.location) != current_obj_state['location'] or
                tuple(obj.rotation_euler) != current_obj_state['rotation_euler'] or
                tuple(obj.scale) != current_obj_state['scale']):
                change_detected = True

            # Check for material changes
            for mat_slot in obj.material_slots:
                if mat_slot.material:
                    current_state = get_material_state(mat_slot.material)
                    if current_state != current_obj_state['materials'].get(mat_slot.name, {}):
                        change_detected = True
                        break

            if change_detected:
                # Update the stored state
                states[obj.name] = {
                    'location': tuple(obj.location),
                    'rotation_euler': tuple(obj.rotation_euler),
                    'scale': tuple(obj.scale),
                    'materials': {mat_slot.name: get_material_state(mat_slot.material)
                                  for mat_slot in obj.material_slots if mat_slot.material}
                }
                break

        if change_detected:
            frames_needed.append(frame)
    print(f"frame require {len(frames_needed)}")
    return frames_needed

# Example usage
# frames_to_render = frames_to_generate()
# print("Frames to generate:", frames_to_render)
