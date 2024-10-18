#version 460 core

in vec2 fragTexCoords;
out vec4 fragColour;

uniform sampler2D TEXTURE;
uniform vec4 VIGNETTE_COLOUR;
uniform bool USE_VIGNETTE;

void main()
{
	fragColour = texture(TEXTURE, fragTexCoords);
}