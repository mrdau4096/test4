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
    vec3 POSITION; // Where the light is
    vec3 LOOK_AT;   // Where the light should look at
    vec3 COLOUR;   // The light's colour (RGB)
    float INTENSITY; // Light intensity
    float FOV;     // Field of view in degrees
    float MAX_DIST; // Maximum effective distance for the light
    mat4 LIGHT_SPACE_MATRIX; //The matrix for the light's position etc.
    sampler2D SHADOW_MAP; //Mapping of shadows from the light's perspective
};

uniform int LIGHT_COUNT;   // Number of active lights
uniform LIGHT LIGHTS[64]; // Array of light structures, with a maximum of 64 lights

float calculateShadow(LIGHT LIGHT, vec3 NORMAL, vec3 LIGHT_DIRECTION, vec4 FRAGMENT_POSITION_LIGHT_SPACE) {
    //Perform perspective division
    vec3 PROJECTED_COORDINATES = FRAGMENT_POSITION_LIGHT_SPACE.xyz / FRAGMENT_POSITION_LIGHT_SPACE.w;
    PROJECTED_COORDINATES = PROJECTED_COORDINATES * 0.5 + 0.5; // Transform to [0,1] range

    //Check if fragment is outside the light's frustum
    if (PROJECTED_COORDINATES.z > 1.0) {
        return 1.0;
    }

    float SHADOW = 0.0;
    vec2 TEXEL_SIZE = 1.0 / textureSize(LIGHT.SHADOW_MAP, 0);
    float CURRENT_DEPTH = PROJECTED_COORDINATES.z;

    //PCF = Percentage Closer Filtering of shadows
    //PCF kernel size;
    int KERNEL_SIZE = 5; //5 appears to be a good value for this.

    //Iterate over the kernel
    for (int x = -KERNEL_SIZE; x <= KERNEL_SIZE; ++x) {
        for (int y = -KERNEL_SIZE; y <= KERNEL_SIZE; ++y) {
            float PCF_DEPTH = texture(LIGHT.SHADOW_MAP, PROJECTED_COORDINATES.xy + vec2(x, y) * TEXEL_SIZE).r;
		    float PCF_BIAS = -0.025e-4 * max(1.0 - dot(NORMAL, LIGHT_DIRECTION), 0.01);
            SHADOW += CURRENT_DEPTH - PCF_BIAS > PCF_DEPTH ? 1.0 : 0.0; // Adjust bias value as needed
        }
    }

    SHADOW /= (KERNEL_SIZE * 2 + 1) * (KERNEL_SIZE * 2 + 1);
    return SHADOW;
}

void main() {
    // Calculate the distance from the fragment to the camera
    float FRAG_DEPTH = length(CAMERA_POSITION - fragPos);

    // If the fragment is beyond the maximum view distance, set it to the void colour
    if (FRAG_DEPTH >= VIEW_MAX_DIST) {
        fragColour = VOID_COLOUR;
        return;
    }

    // Get the texture color
    vec4 TEXTURE_COLOUR = texture(TRI_TEXTURE, fragTexCoords);
    vec3 FINAL_COLOUR = vec3(0.05); //Initialize final color
    vec3 NORMAL = (gl_FrontFacing) ? normalize(fragNormal) : normalize(fragNormal) * -1; //Initialise the fragment's normal.

    if (TEXTURE_COLOUR.a <= 0.25) {
        discard;
    }

    // Iterate through each light and check if the fragment is within the light's FOV
    for (int i = 0; i < LIGHT_COUNT; i++) {
    	float FRAG_LIGHT_DISTANCE = length(LIGHTS[i].POSITION - fragPos);
        vec3 LIGHT_DIRECTION = normalize(LIGHTS[i].LOOK_AT - fragPos); // Direction to the light
        vec3 LIGHT_FORWARD = normalize(LIGHTS[i].POSITION - LIGHTS[i].LOOK_AT); // Light's forward direction

        // Calculate the angle between the light direction and the light's forward direction
        float FOV_COS = dot(LIGHT_DIRECTION, LIGHT_FORWARD); // Dot product of normalized vectors
        bool IN_FOV = degrees(acos(FOV_COS)) <= (LIGHTS[i].FOV * 0.5); // Angle in degrees

        //Calculate the angle between the light's surface normal and the view's surface normal
        float NORMAL_LIGHT_ANGLE = clamp(dot(NORMAL, LIGHT_DIRECTION), 0.0, 1.0);

        if (NORMAL_LIGHT_ANGLE == 0.0) {
            continue;
        }
        
        vec4 FRAGMENT_POSITION_LIGHT_SPACE = LIGHTS[i].LIGHT_SPACE_MATRIX * vec4(fragPos, 1.0);
        float ATTENUATION = max(0.0, 1.0 - (FRAG_LIGHT_DISTANCE / LIGHTS[i].MAX_DIST));
        float DIFFUSE = max(1.0 - abs(dot(NORMAL, LIGHT_DIRECTION) / 90), 0.0);
        float SHADOW = calculateShadow(LIGHTS[i], NORMAL, LIGHT_DIRECTION, FRAGMENT_POSITION_LIGHT_SPACE);
        float BRIGHTNESS = clamp(ATTENUATION * LIGHTS[i].INTENSITY * DIFFUSE * (1.0 - SHADOW), 0.05, 1.0) * abs(NORMAL_LIGHT_ANGLE);

        if (IN_FOV) {
            // If within the FOV, add the texture color to the final color
            FINAL_COLOUR += TEXTURE_COLOUR.rgb * BRIGHTNESS * LIGHTS[i].COLOUR;
        }
    }

    if (!NORMAL_DEBUG) {
        //Display texture colour with lighting
        fragColour = vec4(FINAL_COLOUR, TEXTURE_COLOUR.a);
    } else {
        //Visualise normals of surfaces
        fragColour = vec4((NORMAL.xyz * 0.5) + vec3(0.5), 1.0);
    }
}
