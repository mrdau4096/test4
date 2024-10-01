#version 330 core

in vec2 fragTexCoords;
in vec3 fragNormal;
in vec3 fragPos;

out vec4 fragColour;

uniform sampler2D TEXTURE;
uniform vec3 LIGHT_POSITION;
uniform float MAX_DIST;

void main()
{
	//Discard fragments with alpha < 0.5 in shadow mapping.
	if (texture(TEXTURE, fragTexCoords).a < 0.5) {
		discard;
	}

	//Calculate the depth from the light's position to the fragment position
	//Where 0.0 is the light's position (0 units to the light)
	//And 1.0 is the light's maximum distance (at the very edge of its influence)
	float ACTUAL_DEPTH = length(LIGHT_POSITION - fragPos);
	float DEPTH = clamp(ACTUAL_DEPTH, MAX_DIST/100, MAX_DIST)/MAX_DIST;

	fragColour = vec4(vec3(DEPTH), 1.0);
}
