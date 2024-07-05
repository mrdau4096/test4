#version 330 core

in vec2 fragTexCoords;
in vec3 fragNormal;
in vec3 fragPos;

uniform sampler2D screenTexture;

void main()
{
    if (texture(screenTexture, fragTexCoords).a < 0.5) {
        discard;
    }
}
