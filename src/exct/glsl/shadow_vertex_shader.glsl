#version 330 core

layout(location = 0) in vec3 position;
layout(location = 1) in vec2 texCoords;
layout(location = 2) in vec3 normalDir;
layout(location = 3) in float texIndex;

out vec2 fragTexCoords;
out vec3 fragNormal;
out vec3 fragPos;
flat out float fragTexIndex;

uniform mat4 depthMVP;

void main()
{
    fragTexCoords = texCoords;
    fragTexIndex = texIndex;
    vec4 position3D = depthMVP * vec4(position, 1.0);
    fragPos = position3D.xyz;
    gl_Position = position3D;
}