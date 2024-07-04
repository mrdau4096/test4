#version 330 core

layout(location = 0) out vec3 gNormal;

in vec2 fragTexCoords;
in vec4 fragPosition;
in vec3 fragNormal;

uniform sampler2D screenTexture;

void main()
{
    vec4 tmpColour = texture(screenTexture, fragTexCoords);
    float alpha = tmpColour.a;

    // Debug: Encode alpha into the depth buffer
    if (alpha < 0.5) {
        discard;
    } else {
        gNormal = normalize(fragNormal);
    }
}
