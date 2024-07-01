#version 330 core

in vec2 fragTexCoords;
out vec4 fragColor;

uniform sampler2D screenTexture;
uniform vec2 resolution;
uniform float pixelSize;

void main()
{
	vec2 uv = fragTexCoords * resolution;
	vec2 pix = vec2(pixelSize, pixelSize);
	vec2 coord = (floor(uv / pix) * pix) / resolution;
	fragColor = texture(screenTexture, coord);
}