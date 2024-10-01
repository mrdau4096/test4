#version 330 core

in vec2 fragTexCoords;
in vec3 fragNormal;
in vec3 fragPos;
flat in float fragTexIndex;

uniform sampler2D sheets[16];

void main()
{
    vec4 tmpColour = texture(sheets[int(fragTexIndex)], fragTexCoords);

    if (tmpColour.a < 0.5) {
        discard;
    }
}