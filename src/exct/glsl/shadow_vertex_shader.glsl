#version 330 core

layout(location = 0) in vec3 position;
layout(location = 1) in vec2 texCoords;

out vec2 fragTexCoords;
out vec4 fragPosition;

uniform mat4 depthMVP;

void main()
{
    fragTexCoords = texCoords;
    vec4 position3D = depthMVP * vec4(position, 1.0);
    fragPosition = position3D;
    gl_Position = position3D;
}
