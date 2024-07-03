#version 330 core

out float gl_FragDepth;

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
    } else {
        // Scale alpha to the range [0.0, 1.0] and write it to the depth buffer
        gl_FragDepth = fragTexCoords.x; //tmpColour.r; //Invert to map 1.0 (opaque) to 0.0 (close)
    }
}
