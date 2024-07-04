#version 330 core

in vec4 fragPosition;
in vec2 fragTexCoords;

uniform sampler2D screenTexture;

void main()
{
    vec4 tmpColour = texture(screenTexture, fragTexCoords);
    float alpha = tmpColour.a;

    // Debug: Encode alpha into the depth buffer
    if (alpha < 0.5) {
        discard;
    }
}
