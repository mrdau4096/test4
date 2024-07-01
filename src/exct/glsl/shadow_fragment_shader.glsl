#version 330 core

out vec4 fragColor;

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
    if (tmpColour.a < 0.5) {
        //discard;
        fragColor = vec4(1.0, 1.0, 1.0, 1.0);
    }
    //For debugging: visualize the alpha channel
    fragColor = vec4(1.0, 0.0, 1.0, 1.0);
}
