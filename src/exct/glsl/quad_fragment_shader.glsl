#version 330 core

in vec2 fragTexCoords;
out vec4 fragColor;

uniform sampler2D SCREEN_TCB;
uniform vec2 RESOLUTION;
uniform float PIXEL_SIZE;

void main()
{
	fragColor = texture(SCREEN_TCB, fragTexCoords);
}