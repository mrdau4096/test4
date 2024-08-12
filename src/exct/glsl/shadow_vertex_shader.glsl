#version 330 core

layout(location = 0) in vec3 Position;
layout(location = 1) in vec2 TexCoords;
layout(location = 2) in vec3 Normal;

out vec2 fragTexCoords;
out vec3 fragNormal;
out vec3 fragPos;

uniform mat4 MODEL;
uniform mat4 VIEW;
uniform mat4 PROJECTION;

void main()
{
    fragTexCoords = TexCoords;
    fragNormal = mat3(transpose(inverse(MODEL))) * Normal;
    fragPos = vec3(MODEL * vec4(Position, 1.0)); // Transform position to world space

    gl_Position = PROJECTION * VIEW * vec4(fragPos, 1.0);
}