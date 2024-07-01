#version 330 core

in vec4 fragPosition;
in vec2 fragTexCoords;

uniform sampler2D screenTexture;

//void main()
//{
//    vec4 tmpColour = texture(screenTexture, fragTexCoords);
//
//    if (tmpColour.a < 0.5) {
//        discard;
//    }
//}

void main()
{
    vec4 tmpColour = texture(screenTexture, fragTexCoords);
    //if (tmpColour.a < 0.5) {
    //    discard;
    //}
    // For debugging: visualize the alpha channel
    gl_FragColor = vec4(vec3(tmpColour.a), 1.0);
}
