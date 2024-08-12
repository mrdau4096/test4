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
	// Discard fragments with alpha < 0.5
	if (texture(TEXTURE, fragTexCoords).a < 0.5) {
		discard;
	}

	//Calculate the depth from the light's position to the fragment position
	float ACTUAL_DEPTH = length(LIGHT_POSITION - fragPos);
	float DEPTH = clamp(ACTUAL_DEPTH, MAX_DIST/100, MAX_DIST)/MAX_DIST;

	// Normalize the depth value based on the near and far plane

	fragColour = vec4(vec3(DEPTH), 1.0);
}
