#version 460 core

in vec2 fragTexCoords;
in vec3 fragNormal;
in vec3 fragPos;
flat in float fragSheetID;

out vec4 fragColour;


uniform sampler2DArray SHEETS;
uniform sampler2DArray SHADOW_MAPS;
uniform vec3 CAMERA_POSITION;
uniform vec3 CAMERA_LOOK_AT;
uniform vec4 VOID_COLOUR;
uniform float VIEW_MAX_DIST;
uniform bool HEADLAMP_ENABLED;
uniform bool NORMAL_DEBUG;
uniform bool WIREFRAME_DEBUG;
uniform float MAX_RAY_PERSIST_SECONDS;


//Mirrors the python equivalent class, bar a few unneccessary attributes.
struct LIGHT {
	vec3 POSITION;
	vec3 LOOK_AT;
	vec3 COLOUR;
	float INTENSITY;
	float FOV;
	float MAX_DIST;
	mat4 LIGHT_SPACE_MATRIX;
	bool ENABLED;
};

//Maximum of 64 lights in a scene.
uniform int LIGHT_COUNT;
uniform LIGHT LIGHTS[64];



float FIND_SHADOW(int LIGHT_ID, LIGHT LIGHT, vec3 LIGHT_DIRECTION, vec3 NORMAL, vec4 FRAGMENT_POSITION_LIGHT_SPACE, vec3 fragPos) {
	//Finds whether or not a fragPos should be in shadow or not, utilising the shadow map, and PCF.

	vec3 PROJECTED_COORDINATES = FRAGMENT_POSITION_LIGHT_SPACE.xyz / FRAGMENT_POSITION_LIGHT_SPACE.w;
	PROJECTED_COORDINATES = (PROJECTED_COORDINATES * 0.5) + 0.5; //Convert projected coordinates to [0.0 - 1.0] range to use as UV

	//Initialise values such as the mapping bias and whatnot.
	float SHADOW = 0.0;
	vec2 TEXEL_SIZE = vec2(0.000732421875); //1.5 DIV 2048
	float ACTUAL_DEPTH = distance(LIGHT.POSITION, fragPos);
	if (ACTUAL_DEPTH > LIGHT.MAX_DIST) {
		return 1.0;
	}
	float CURRENT_DEPTH = clamp(ACTUAL_DEPTH, LIGHT.MAX_DIST/100, LIGHT.MAX_DIST)/LIGHT.MAX_DIST; //0.0 is the light's position, 1.0 at the light's maximum distance. Linear.
	float MAPPING_BIAS = (-1.5e-2 * max(1.0 - dot(NORMAL, LIGHT_DIRECTION), 0.01)) - (3e-3 * dot(NORMAL, LIGHT_DIRECTION));



	int KERNEL_SIZE = 5; //5 appears to be a good value for this, not too extreme but also not too low.
	//Iterate over a square with KERNEL_SIZE "radius" to calculate PCF values.
	for (int X = -KERNEL_SIZE; X <= KERNEL_SIZE; ++X) {
		for (int Y = -KERNEL_SIZE; Y <= KERNEL_SIZE; ++Y) {
			float SHADOW_MAP_DEPTH = texture(SHADOW_MAPS, vec3(vec2(PROJECTED_COORDINATES.xy + vec2(X, Y) * TEXEL_SIZE), float(LIGHT_ID))).r;
			SHADOW += ((CURRENT_DEPTH + MAPPING_BIAS) > SHADOW_MAP_DEPTH) ? 1.0 : 0.0;
		}
	}

	//Divide by the KERNEL_SIZE's created sample area, so that the value returned is in the [0.0 - 1.0] range again.
	SHADOW /= float((KERNEL_SIZE * 2 + 1) * (KERNEL_SIZE * 2 + 1));
	return SHADOW;
}


void main() {
	if (WIREFRAME_DEBUG) {
		fragColour = vec4(1.0, 1.0, 1.0, 1.0);
		return;
	}

	//Actual fragment depth.
	float FRAG_DEPTH = length(CAMERA_POSITION - fragPos);
	if (FRAG_DEPTH >= VIEW_MAX_DIST) {
		fragColour = VOID_COLOUR;
		return;
	}

	//Initialise colours (texture and default final)
	vec4 TEXTURE_COLOUR = texture(SHEETS, vec3(fragTexCoords, float(fragSheetID)));
	vec3 FINAL_COLOUR = vec3(0.05);
	
	if (fragNormal == vec3(0.0)) {
		//For raycasts, helps identify them better.
		//Uses the sheet ID for a fade-out effect instead, as they are a solid colour.
		fragColour = vec4(1.0, 1.0, 0.0, (fragSheetID / MAX_RAY_PERSIST_SECONDS));
		return;
	} else if (TEXTURE_COLOUR.a < 0.05) {
		discard;
	}

	//Assorted other fragment data.
	vec3 NORMAL = (gl_FrontFacing) ? normalize(fragNormal) : normalize(fragNormal) * -1;
	float DISTANCE_FADE = 1.0 - (FRAG_DEPTH / VIEW_MAX_DIST);


	//Iterate through each light and check if the fragment is within the light's FOV, then calculate brightness and colour impact of said light.
	for (int I = 0; I < LIGHT_COUNT; I++) {
		if (!LIGHTS[I].ENABLED) {
			continue;
		}

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
		float SHADOW = FIND_SHADOW(I, LIGHTS[I], LIGHT_DIRECTION, NORMAL, FRAGMENT_POSITION_LIGHT_SPACE, fragPos); //Fragment shadow or not.
		float BRIGHTNESS = clamp(ATTENUATION * LIGHTS[I].INTENSITY * DIFFUSE * (1.0 - SHADOW), 0.05, 1.0) * abs(NORMAL_LIGHT_ANGLE); //Combine all the rest into one.

		//Add this light's influence to the final colour.
		FINAL_COLOUR += vec3(TEXTURE_COLOUR.rgb * BRIGHTNESS);
	}



	if (HEADLAMP_ENABLED) {
		//If the player's headlamp is turned on, cast a light from the camera with fixed FOV/max dist, and no shadows
		//(Any shadows would simply be hidden from the player's view anyhow, and this saves performance.)
		vec4 HEADLAMP_COLOUR = vec4(1.0, 1.0, 1.0, 1.0); //R, G, B, Intensity.
		vec3 HEADLAMP_OFFSET = vec3(0.0, 0.0, 0.0);
		float HEADLAMP_MAX_DIST = 10.0;
		float HEADLAMP_FOV = 45.0;

		vec3 HEADLAMP_POSITION = CAMERA_POSITION + HEADLAMP_OFFSET; //Allows for an offset, if needed (Unlikely, but supported.)



		float FRAG_CAMERA_DISTANCE = length(HEADLAMP_POSITION - fragPos);
		vec3 FRAG_HEADLAMP_DIRECTION = normalize(HEADLAMP_POSITION - fragPos); // Direction to the light
		vec3 HEADLAMP_FORWARD = normalize(HEADLAMP_POSITION - CAMERA_LOOK_AT); // Light's forward direction

		//Calculate the angle between the light direction and the light's forward direction
		float FOV_COS = dot(FRAG_HEADLAMP_DIRECTION, HEADLAMP_FORWARD); //Dot product of normalized vectors

		if (degrees(acos(FOV_COS)) <= (HEADLAMP_FOV * 0.5)) {
			//Calculate the angle between the light's directional vector and the view's surface normal
			float NORMAL_LIGHT_ANGLE = clamp(dot(NORMAL, FRAG_HEADLAMP_DIRECTION), 0.0, 1.0);

			//Prevent excessive FOV values from messing with the rest of the light calculations (negative values, 0 values)
			if (NORMAL_LIGHT_ANGLE > 0.01) {
				//Brightness component calculations.
				float ATTENUATION = max(0.0, 1.0 - (FRAG_CAMERA_DISTANCE / HEADLAMP_MAX_DIST)); //"Distance fade from light".
				float DIFFUSE =  2.0 * FOV_COS * FOV_COS - 1.0; //Dimmer as you go further from the "centre" of the light's direction.
				float BRIGHTNESS = clamp(ATTENUATION * HEADLAMP_COLOUR.w * DIFFUSE, 0.05, 1.0) * abs(NORMAL_LIGHT_ANGLE); //Combine all the rest into one.

				//Add this light's influence to the final colour.
				FINAL_COLOUR += vec3(TEXTURE_COLOUR.rgb * BRIGHTNESS);
			}
		}


	}



	if (!NORMAL_DEBUG) {
		//Display final colour
		fragColour = vec4(FINAL_COLOUR * DISTANCE_FADE, TEXTURE_COLOUR.a);
	} else {
		//Display the surface normals as RGB, where (0, 0, 0) would be (0.5, 0.5, 0.5).
		fragColour = vec4((NORMAL.xyz * 0.5) + vec3(0.5), 1.0);
	}
}