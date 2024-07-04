#version 330 core

layout(location = 0) in vec3 position;
layout(location = 1) in vec2 texCoords;
layout(location = 2) in vec3 normal;

out vec2 fragTexCoords;
out vec4 fragPosition;
out vec3 fragNormal;

uniform mat4 depthMVP;
uniform mat4 model;

void main()
{
    fragTexCoords = texCoords;
    vec4 position3D = depthMVP * vec4(position, 1.0);
    fragPosition = position3D;
    fragNormal = mat3(transpose(inverse(model))) * normal;
    gl_Position = position3D;
}
