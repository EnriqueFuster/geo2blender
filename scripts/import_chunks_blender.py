import bpy
import os
from mathutils import Vector

# Folder where the PNGs are located
chunk_folder = bpy.path.abspath("//processing/chunks")

# Base scale (you can adjust it so that one pixel = X Blender units)
base_scale = 1.0

# List files and filter PNGs
all_files = os.listdir(chunk_folder)
dsm_files = [f for f in all_files if f.startswith("dsm") and f.lower().endswith(".png")]
satellite_files = [f for f in all_files if f.startswith("satellite") and f.lower().endswith(".png")]

# Create dictionaries for quick access
satellite_dict = {}
dsm_dict = {}

for f in satellite_files:
    key = f.split("_")[1] + "_" + f.split("_")[2].split(".")[0]
    satellite_dict[key] = os.path.join(chunk_folder, f)

for f in dsm_files:
    key = f.split("_")[1] + "_" + f.split("_")[2].split(".")[0]
    dsm_dict[key] = os.path.join(chunk_folder, f)

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create central controller object
controller = bpy.data.objects.new("Chunk_Controller", None)
bpy.context.collection.objects.link(controller)
controller["disp_strength"] = 0.1  # add initial displacement value
controller["_RNA_UI"] = {"disp_strength": {"min": 0, "max": 10, "description": "Displace Strength"}}
controller["subdiv_view"] = 3  # add initial Subdivision Viewport value
controller["_RNA_UI"]["subdiv_view"] = {"min": 0, "max": 6, "description": "Subdivision Viewport"}
controller["subdiv_render"] = 3  # add initial Subdivision Render value
controller["_RNA_UI"]["subdiv_render"] = {"min": 0, "max": 6, "description": "Subdivision Render"}

# Add initial displacement value
controller["global_hue"] = 0.5
controller["_RNA_UI"]["global_hue"] = {"min": 0.0, "max": 1.0, "description": "Global Hue Control"}
controller["global_saturation"] = 1.0
controller["_RNA_UI"]["global_saturation"] = {"min": 0.0, "max": 2.0, "description": "Global Saturation Control"}
controller["global_value"] = 1.0
controller["_RNA_UI"]["global_value"] = {"min": 0.0, "max": 2.0, "description": "Global Value Control"}

# Load only some chunks (adjust the number)
keys_to_load = list(satellite_dict.keys())

x_offset = 0
y_offset = 0
row_heights = {}

for key in keys_to_load:
    row, col = key.split("_")
    row = int(row[1:])
    col = int(col[1:])

    # Determine size from the satellite image
    img = bpy.data.images.load(satellite_dict[key])
    width, height = img.size
    aspect_ratio_x = width / max(width, height)
    aspect_ratio_y = height / max(width, height)

    # Create plane
    bpy.ops.mesh.primitive_plane_add(size=1)
    plane = bpy.context.object
    plane.name = f"chunk_{key}"

    # Scale plane according to aspect ratio and base scale
    plane.scale = (aspect_ratio_x * base_scale, aspect_ratio_y * base_scale, 1)

    # Position plane next to the previous one
    if col == 0:
        x_offset = 0
        y_offset = sum(row_heights.get(r, 0) for r in range(row))
        row_heights[row] = aspect_ratio_y * base_scale
    plane.location = Vector((x_offset + aspect_ratio_x * base_scale / 2,
                             y_offset + aspect_ratio_y * base_scale / 2, 0))
    x_offset += aspect_ratio_x * base_scale

    # Create satellite material
    mat = bpy.data.materials.new(name=f"mat_{key}")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for n in nodes:
        nodes.remove(n)
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled_node.inputs['Roughness'].default_value = 1.0
    tex_image_node = nodes.new(type='ShaderNodeTexImage')
    tex_image_node.image = img
    tex_image_node.extension = 'EXTEND'

    # Hue/Saturation/Value node with global drivers
    hsv_node = nodes.new(type="ShaderNodeHueSaturation")
    hsv_node.inputs['Hue'].default_value = 0.5
    hsv_node.inputs['Saturation'].default_value = 1.0
    hsv_node.inputs['Value'].default_value = 1.0

    links.new(tex_image_node.outputs['Color'], hsv_node.inputs['Color'])
    links.new(hsv_node.outputs['Color'], principled_node.inputs['Base Color'])

    # Drivers
    hue_driver = hsv_node.inputs['Hue'].driver_add("default_value").driver
    hue_driver.type = 'AVERAGE'
    var_h = hue_driver.variables.new()
    var_h.name = "ghue"
    var_h.targets[0].id = controller
    var_h.targets[0].data_path = '["global_hue"]'

    sat_driver = hsv_node.inputs['Saturation'].driver_add("default_value").driver
    sat_driver.type = 'AVERAGE'
    var_s = sat_driver.variables.new()
    var_s.name = "gsat"
    var_s.targets[0].id = controller
    var_s.targets[0].data_path = '["global_saturation"]'

    val_driver = hsv_node.inputs['Value'].driver_add("default_value").driver
    val_driver.type = 'AVERAGE'
    var_v = val_driver.variables.new()
    var_v.name = "gval"
    var_v.targets[0].id = controller
    var_v.targets[0].data_path = '["global_value"]'

    # Normal base color + material output
    links.new(principled_node.outputs['BSDF'], output_node.inputs['Surface'])
    plane.data.materials.append(mat)

    # Extra math nodes from your script (kept intact)
    greater_node = nodes.new(type="ShaderNodeMath")
    greater_node.operation = 'GREATER_THAN'
    greater_node.inputs[1].default_value = 0.3

    invert_node = nodes.new(type="ShaderNodeInvert")

    log_node = nodes.new(type="ShaderNodeMath")
    log_node.operation = 'LOGARITHM'
    log_node.inputs[1].default_value = 0.5

    multiply_node = nodes.new(type="ShaderNodeMath")
    multiply_node.operation = 'MULTIPLY'
    multiply_node.inputs[1].default_value = 1.0

    map_range_node = nodes.new(type="ShaderNodeMapRange")
    map_range_node.inputs["From Min"].default_value = 0.0
    map_range_node.inputs["From Max"].default_value = 1.0
    map_range_node.inputs["To Min"].default_value = 0.0
    map_range_node.inputs["To Max"].default_value = 0.3
    map_range_node.clamp = True

    links.new(tex_image_node.outputs['Color'], greater_node.inputs[0])
    links.new(greater_node.outputs[0], invert_node.inputs['Color'])
    links.new(tex_image_node.outputs['Color'], log_node.inputs[0])
    links.new(invert_node.outputs['Color'], multiply_node.inputs[0])
    links.new(log_node.outputs[0], multiply_node.inputs[1])
    links.new(multiply_node.outputs[0], map_range_node.inputs['Value'])
    links.new(map_range_node.outputs['Result'], principled_node.inputs['Diffuse Roughness'])

    # Automatic UV map
    if not plane.data.uv_layers:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.uv.smart_project()
        bpy.ops.object.mode_set(mode='OBJECT')

    # Subdivision Surface modifier (Simple)
    subd = plane.modifiers.new(name="Subsurf", type='SUBSURF')
    subd.subdivision_type = 'SIMPLE'
    subd.levels = controller["subdiv_view"]
    subd.render_levels = controller["subdiv_render"]

    # Drivers to centralize Subdivision
    driver_view = subd.driver_add("levels").driver
    driver_view.type = 'AVERAGE'
    var = driver_view.variables.new()
    var.name = "subdiv_view"
    var.targets[0].id = controller
    var.targets[0].data_path = '["subdiv_view"]'

    driver_render = subd.driver_add("render_levels").driver
    driver_render.type = 'AVERAGE'
    var2 = driver_render.variables.new()
    var2.name = "subdiv_render"
    var2.targets[0].id = controller
    var2.targets[0].data_path = '["subdiv_render"]'

    # Displace modifier with DSM
    disp = plane.modifiers.new(name="Displace", type='DISPLACE')
    tex = bpy.data.textures.new(name=f"disp_tex_{key}", type='IMAGE')
    tex.image = bpy.data.images.load(dsm_dict[key])
    tex.extension = 'EXTEND'
    disp.texture = tex
    disp.texture_coords = 'UV'
    disp.uv_layer = plane.data.uv_layers.active.name

    # Driver for Displace strength
    driver = disp.driver_add("strength").driver
    driver.type = 'AVERAGE'
    var = driver.variables.new()
    var.name = "ds"
    var.targets[0].id = controller
    var.targets[0].data_path = '["disp_strength"]'

print("✅ Scene assembled with chunks, materials, global HSV control, and displacement configured.")
