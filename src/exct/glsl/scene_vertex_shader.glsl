#version 330 core

layout(location = 0) in vec3 aPos;
layout(location = 1) in vec2 aTexCoords;
layout(location = 2) in vec3 aNormal;

out vec2 fragTexCoords;
out vec3 fragNormal;
out vec3 fragPos;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main()
{
    fragTexCoords = aTexCoords;
    fragNormal = mat3(transpose(inverse(model))) * aNormal; // Transform normal to world space
    fragPos = vec3(model * vec4(aPos, 1.0)); // Transform position to world space

    gl_Position = projection * view * vec4(fragPos, 1.0);
}
