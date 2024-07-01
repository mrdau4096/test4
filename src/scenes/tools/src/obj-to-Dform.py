def obj_to_custom(obj_data, texture_pos, collidable_formatted, centre):
    vertices = []
    triangles = []
    converted_line = 0

    lines = obj_data.strip().split("\n")

    for line in lines:
        if line.startswith('v '):
            parts = line.split()
            vertex = (float(parts[1]), float(parts[2]), float(parts[3]))
            vertices.append(vertex)
            #print(f"Vertex: {vertex}")
        elif line.startswith('f '):
            parts = line.split()
            indices = [int(part.split('/')[0]) - 1 for part in parts[1:]]
            if len(indices) == 3:
                triangles.append(indices)
            elif len(indices) > 3:
                # Convert polygons to triangles using fan triangulation
                for i in range(1, len(indices) - 1):
                    triangles.append([indices[0], indices[i], indices[i + 1]])
            #print(f"Face: {indices}")
        elif line.startswith('vt ') or line.startswith('vn ') or line.startswith('mtllib ') or line.startswith('o ') or line.startswith('# '):
            continue

    custom_content = ""
    for triangle in triangles:
        v1 = vertices[triangle[0]]
        v2 = vertices[triangle[1]]
        v3 = vertices[triangle[2]]
        custom_content += f"4 | {v1[0] + centre[0]}, {v1[1] + centre[1]}, {v1[2] + centre[2]} | {v2[0] + centre[0]}, {v2[1] + centre[1]}, {v2[2] + centre[2]} | {v3[0] + centre[0]}, {v3[1] + centre[1]}, {v3[2] + centre[2]} | {collidable_formatted} | {texture_pos}\n"

    return custom_content.strip()

file_to_read = input("What is the name of the file to convert?\n[___.obj] (without filetype)\n> ")
centre_X = int(input("What X coordinate should the centre of the object have?\n[INT]\n> "))
centre_Y = int(input("What Y coordiante should the centre of the object have?\n[INT]\n> "))
centre_Z = int(input("What Z coordinate should the centre of the object have?\n[INT]\n> "))
centre = [centre_X, centre_Y, centre_Z]
texture_pos = input("What texture position on the spritesheet should be used?\n[___]\n> ")
collidable_unformatted = input("Should the model be collide-able?\n[T/F]\n> ")
front_padding_file = input("Which file should the program use as 'padding' at the start of the file?\n[___.___] (with filetype)\n> ")

if collidable_unformatted.lower() in ["true", "t", "yes", "y"]:
    collidable_formatted = "T"
elif collidable_unformatted.lower() in ["false", "f", "no", "n"]:
    collidable_formatted = "F"
else:
    input(f"Collide-able must be True or False, and no other value.\nYou may press enter, or close this window now.")


with open(f"{file_to_read}.obj", "r") as i:
    obj_data = i.read()

custom_data = obj_to_custom(obj_data, texture_pos, collidable_formatted, centre)

try:
    with open(f"{front_padding_file}", "r") as p:
        padding_str = p.read() + "\n"
        final_data = padding_str + custom_data
except FileNotFoundError:
    final_data = custom_data

id_to_save_as = input("What ID should it be saved as?\n[scene-m___.dat]\n> ")
print(f"File will be saved as scene-m{id_to_save_as}.dat")

with open(f"scene-m{id_to_save_as}.dat", "w") as o:
    o.write(final_data)

input(f"Conversion complete: {file_to_read}.obj -> scene-m{id_to_save_as}.dat\nYou may press enter, or close this window now.")
