#version 330 core

in vec2 fragTexCoords;
out vec4 fragColor;

uniform sampler2D SCREEN_TCB;
uniform vec2 RESOLUTION;
uniform float PIXEL_SIZE;

void main()
{
	//Draws the current pixel to the quad from a texture, with optional PIXEL_SIZE pixellation effect.
	vec2 UV = fragTexCoords * RESOLUTION;
	vec2 PIXEL = vec2(PIXEL_SIZE, PIXEL_SIZE);
	vec2 UV_COORDINATE = (floor(UV / PIXEL) * PIXEL) / RESOLUTION;
	fragColor = texture(SCREEN_TCB, UV_COORDINATE);
}