#version 330 core

layout(location = 0) in vec3 Position;
layout(location = 1) in vec2 TexCoords;
layout(location = 2) in vec3 Normal;

out vec2 fragTexCoords;
out vec3 fragNormal;
out vec3 fragPos;

uniform mat4 MODEL_MATRIX;
uniform mat4 VIEW_MATRIX;
uniform mat4 PROJ_MATRIX;

void main()
{
    fragTexCoords = TexCoords;
    fragNormal = mat3(transpose(inverse(MODEL_MATRIX))) * Normal;
    fragPos = vec3(MODEL_MATRIX * vec4(Position, 1.0)); // Transform position to world space

    gl_Position = PROJ_MATRIX * VIEW_MATRIX * vec4(fragPos, 1.0);
}
