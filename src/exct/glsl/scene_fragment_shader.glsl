#version 330 core

in vec2 fragTexCoords;
in vec3 fragNormal;
in vec3 fragPos;

out vec4 fragColour;

uniform sampler2D TRI_TEXTURE;
uniform vec3 CAMERA_POSITION;
uniform vec4 VOID_COLOUR;
uniform float VIEW_MAX_DIST;
uniform bool NORMAL_DEBUG;

//Mirrors the python equivalent class, bar a few unneccessary attributes.
struct LIGHT {
	vec3 POSITION;
	vec3 LOOK_AT;
	vec3 COLOUR;
	float INTENSITY;
	float FOV;
	float MAX_DIST;
	mat4 LIGHT_SPACE_MATRIX;
	sampler2D SHADOW_MAP;
};

//Maximum of 64 lights in a scene.
uniform int LIGHT_COUNT;
uniform LIGHT LIGHTS[64];


float FIND_SHADOW(LIGHT LIGHT, vec3 LIGHT_DIRECTION, vec3 NORMAL, vec4 FRAGMENT_POSITION_LIGHT_SPACE, vec3 fragPos) {
	//Finds whether or not a fragPos should be in shadow or not, utilising the shadow map, and PCF.

	vec3 PROJECTED_COORDINATES = FRAGMENT_POSITION_LIGHT_SPACE.xyz / FRAGMENT_POSITION_LIGHT_SPACE.w;
	PROJECTED_COORDINATES = (PROJECTED_COORDINATES * 0.5) + 0.5; //Convert projected coordinates to [0.0 - 1.0] range to use as UV

	//Initialise values such as the mapping bias and whatnot.
	float SHADOW = 0.0;
	vec2 TEXEL_SIZE = 1.5 / textureSize(LIGHT.SHADOW_MAP, 0);
	float ACTUAL_DEPTH = length(LIGHT.POSITION - fragPos);
	if (ACTUAL_DEPTH > LIGHT.MAX_DIST) {
		return 1.0;
	}
	float CURRENT_DEPTH = clamp(ACTUAL_DEPTH, LIGHT.MAX_DIST/100, LIGHT.MAX_DIST)/LIGHT.MAX_DIST; //0.0 is the light's position, 1.0 at the light's maximum distance. Linear.
	float MAPPING_BIAS = (-1.25e-2 * max(1.0 - dot(NORMAL, LIGHT_DIRECTION), 0.01)) - (2.5e-3 * dot(NORMAL, LIGHT_DIRECTION));



	int KERNEL_SIZE = 5; //5 appears to be a good value for this, not too extreme but also not too low.
	//Iterate over a square with KERNEL_SIZE "radius" to calculate PCF values.
	for (int X = -KERNEL_SIZE; X <= KERNEL_SIZE; ++X) {
		for (int Y = -KERNEL_SIZE; Y <= KERNEL_SIZE; ++Y) {
			float SHADOW_MAP_DEPTH = texture(LIGHT.SHADOW_MAP, PROJECTED_COORDINATES.xy + vec2(X, Y) * TEXEL_SIZE).r;
			SHADOW += ((CURRENT_DEPTH + MAPPING_BIAS) > SHADOW_MAP_DEPTH) ? 1.0 : 0.0;
		}
	}

	//Divide by the KERNEL_SIZE's created sample area, so that the value returned is in the [0.0 - 1.0] range again.
	SHADOW /= float((KERNEL_SIZE * 2 + 1) * (KERNEL_SIZE * 2 + 1));
	return SHADOW;
}


void main() {
	//Actual fragment depth.
	float FRAG_DEPTH = length(CAMERA_POSITION - fragPos);
	if (FRAG_DEPTH >= VIEW_MAX_DIST) {
		fragColour = VOID_COLOUR;
		return;
	}

	//Initialise colours (texture and default final)
	vec4 TEXTURE_COLOUR = texture(TRI_TEXTURE, fragTexCoords);
	vec3 FINAL_COLOUR = vec3(0.05);
	
	if (TEXTURE_COLOUR.a <= 0.25) {
		//If the texture colour's alpha is under 0.25, discard this fragment; these are not rendered.
		discard;
	}

	//Assorted other fragment data.
	vec3 NORMAL = (gl_FrontFacing) ? normalize(fragNormal) : normalize(fragNormal) * -1;
	float DISTANCE_FADE = 1.0 - (FRAG_DEPTH / VIEW_MAX_DIST);


	//Iterate through each light and check if the fragment is within the light's FOV, then calculate brightness and colour impact of said light.
	for (int I = 0; I < LIGHT_COUNT; I++) {
		float FRAG_LIGHT_DISTANCE = length(LIGHTS[I].POSITION - fragPos);
		vec3 LIGHT_DIRECTION = normalize(LIGHTS[I].LOOK_AT - fragPos); // Direction to the light
		vec3 LIGHT_FORWARD = normalize(LIGHTS[I].POSITION - LIGHTS[I].LOOK_AT); // Light's forward direction

		//Calculate the angle between the light direction and the light's forward direction
		float FOV_COS = dot(LIGHT_DIRECTION, LIGHT_FORWARD); //Dot product of normalized vectors
		if (degrees(acos(FOV_COS)) > (LIGHTS[I].FOV * 0.5)) {
			//If it's out of the light's FOV - do not account for this light's influence.
			continue;
		}

		//Calculate the angle between the light's directional vector and the view's surface normal
		float NORMAL_LIGHT_ANGLE = clamp(dot(NORMAL, LIGHT_DIRECTION), 0.0, 1.0);
		//Prevent excessive FOV values from messing with the rest of the light calculations (negative values, 0 values)
		if (NORMAL_LIGHT_ANGLE <= 0.01) {
			continue;
		}

		//Calculate the fragPos in the light's space
		vec4 FRAGMENT_POSITION_LIGHT_SPACE = LIGHTS[I].LIGHT_SPACE_MATRIX * vec4(fragPos, 1.0);

		//Brightness component calculations.
		float ATTENUATION = max(0.0, 1.0 - (FRAG_LIGHT_DISTANCE / LIGHTS[I].MAX_DIST)); //"Distance fade from light".
		float DIFFUSE =  2.0 * FOV_COS * FOV_COS - 1.0; //Dimmer as you go further from the "centre" of the light's direction.
		float SHADOW = FIND_SHADOW(LIGHTS[I], LIGHT_DIRECTION, NORMAL, FRAGMENT_POSITION_LIGHT_SPACE, fragPos); //Fragment shadow or not.
		float BRIGHTNESS = clamp(ATTENUATION * LIGHTS[I].INTENSITY * DIFFUSE * (1.0 - SHADOW), 0.05, 1.0) * abs(NORMAL_LIGHT_ANGLE); //Combine all the rest into one.

		//Add this light's influence to the final colour.
		FINAL_COLOUR += vec3(TEXTURE_COLOUR.rgb * BRIGHTNESS);
	}

	if (!NORMAL_DEBUG) {
		//Display final colour
		fragColour = vec4(FINAL_COLOUR * DISTANCE_FADE, TEXTURE_COLOUR.a);
	} else {
		//Display the surface normals as RGB, where (0, 0, 0) would be (0.5, 0.5, 0.5).
		fragColour = vec4((NORMAL.xyz * 0.5) + vec3(0.5), 1.0);
	}
}




