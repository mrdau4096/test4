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

uniform int LIGHT_COUNT;
uniform LIGHT LIGHTS[64];


float FIND_SHADOW(LIGHT LIGHT, vec3 LIGHT_DIRECTION, vec3 NORMAL, vec4 FRAGMENT_POSITION_LIGHT_SPACE, vec3 fragPos) {
	vec3 PROJECTED_COORDINATES = FRAGMENT_POSITION_LIGHT_SPACE.xyz / FRAGMENT_POSITION_LIGHT_SPACE.w;
	PROJECTED_COORDINATES = (PROJECTED_COORDINATES * 0.5) + 0.5; //Transform to [0,1] range

	float SHADOW = 0.0;
	vec2 TEXEL_SIZE = 1.5 / textureSize(LIGHT.SHADOW_MAP, 0);
	float ACTUAL_DEPTH = length(LIGHT.POSITION - fragPos);
	if (ACTUAL_DEPTH > LIGHT.MAX_DIST) {
		return 1.0;
	}
	float CURRENT_DEPTH = clamp(ACTUAL_DEPTH, LIGHT.MAX_DIST/100, LIGHT.MAX_DIST)/LIGHT.MAX_DIST;
	float MAPPING_BIAS = (-1.25e-2 * max(1.0 - dot(NORMAL, LIGHT_DIRECTION), 0.01)) - (2.5e-3 * dot(NORMAL, LIGHT_DIRECTION));



	int KERNEL_SIZE = 5; //5 appears to be a good value for this.
	//Iterate over the kernel
	for (int X = -KERNEL_SIZE; X <= KERNEL_SIZE; ++X) {
		for (int Y = -KERNEL_SIZE; Y <= KERNEL_SIZE; ++Y) {
			float SHADOW_MAP_DEPTH = texture(LIGHT.SHADOW_MAP, PROJECTED_COORDINATES.xy + vec2(X, Y) * TEXEL_SIZE).r;
			SHADOW += ((CURRENT_DEPTH + MAPPING_BIAS) > SHADOW_MAP_DEPTH) ? 1.0 : 0.0;
		}
	}

	SHADOW /= float((KERNEL_SIZE * 2 + 1) * (KERNEL_SIZE * 2 + 1));
	return SHADOW;


	float SHADOW_MAP_DEPTH = texture(LIGHT.SHADOW_MAP, PROJECTED_COORDINATES.xy).r;

	//return ((CURRENT_DEPTH + MAPPING_BIAS) > SHADOW_MAP_DEPTH) ? 1.0 : 0.0;
	//return 50 * (CURRENT_DEPTH - SHADOW_MAP_DEPTH + MAPPING_BIAS); //0.16 for centre, 0.25 for corner.
	//return SHADOW_MAP_DEPTH;
	//return CURRENT_DEPTH;
}


void main() {
	float FRAG_DEPTH = length(CAMERA_POSITION - fragPos);

	if (FRAG_DEPTH >= VIEW_MAX_DIST) {
		fragColour = VOID_COLOUR;
		return;
	}

	vec4 TEXTURE_COLOUR = texture(TRI_TEXTURE, fragTexCoords);
	vec3 FINAL_COLOUR = vec3(0.05);

	vec3 NORMAL = (gl_FrontFacing) ? normalize(fragNormal) : normalize(fragNormal) * -1;
	float DISTANCE_FADE = 1.0 - (FRAG_DEPTH / VIEW_MAX_DIST);

	if (TEXTURE_COLOUR.a <= 0.25) {
		discard;
	}

	//Iterate through each light and check if the fragment is within the light's FOV
	for (int I = 0; I < LIGHT_COUNT; I++) {
		float FRAG_LIGHT_DISTANCE = length(LIGHTS[I].POSITION - fragPos);
		vec3 LIGHT_DIRECTION = normalize(LIGHTS[I].LOOK_AT - fragPos); // Direction to the light
		vec3 LIGHT_FORWARD = normalize(LIGHTS[I].POSITION - LIGHTS[I].LOOK_AT); // Light's forward direction

		// Calculate the angle between the light direction and the light's forward direction
		float FOV_COS = dot(LIGHT_DIRECTION, LIGHT_FORWARD); // Dot product of normalized vectors
		bool IN_FOV = degrees(acos(FOV_COS)) <= (LIGHTS[I].FOV * 0.5); // Angle in degrees

		if (!IN_FOV) {
			continue;
		}

		//Calculate the angle between the light's surface normal and the view's surface normal
		float NORMAL_LIGHT_ANGLE = clamp(dot(NORMAL, LIGHT_DIRECTION), 0.0, 1.0);

		if (NORMAL_LIGHT_ANGLE <= 0.01) {
			continue;
		}

		vec4 FRAGMENT_POSITION_LIGHT_SPACE = LIGHTS[I].LIGHT_SPACE_MATRIX * vec4(fragPos, 1.0);

		float ATTENUATION = max(0.0, 1.0 - (FRAG_LIGHT_DISTANCE / LIGHTS[I].MAX_DIST));
		float DIFFUSE =  2.0 * FOV_COS * FOV_COS - 1.0;
		float SHADOW = FIND_SHADOW(LIGHTS[I], LIGHT_DIRECTION, NORMAL, FRAGMENT_POSITION_LIGHT_SPACE, fragPos);
		float BRIGHTNESS = clamp(ATTENUATION * LIGHTS[I].INTENSITY * DIFFUSE * (1.0 - SHADOW), 0.05, 1.0) * abs(NORMAL_LIGHT_ANGLE);

		//fragColour = vec4(vec3(BRIGHTNESS), 1.0);
		if (false) {
			if (SHADOW > 0.01) {
				fragColour = vec4(SHADOW, 0.0, 0.0, 1.0);
			} else if (SHADOW < 0.0) {
				fragColour = vec4(0.0, 0.0, abs(SHADOW), 1.0);
			} else {
				fragColour = vec4(0.0, 1.0, 0.0, 1.0);
			}
		} else if (false) {
            fragColour = vec4(vec3(SHADOW), 1.0);
        }
		//return;

		FINAL_COLOUR += vec3(TEXTURE_COLOUR.rgb * BRIGHTNESS);

	}

	if (!NORMAL_DEBUG) {
		fragColour = vec4(FINAL_COLOUR * DISTANCE_FADE, TEXTURE_COLOUR.a);
	} else {
		fragColour = vec4((NORMAL.xyz * 0.5) + vec3(0.5), 1.0);
	}
}




