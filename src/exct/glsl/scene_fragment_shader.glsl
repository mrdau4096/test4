#version 330 core

in vec2 fragTexCoords;
in vec3 fragNormal;
in vec3 fragPos;

out vec4 fragColour;

uniform sampler2D texture1;
uniform vec3 cameraPos;
uniform vec4 voidColour;
uniform float maxViewDistance;

struct Light {
    vec3 position; // Where the light is
    vec3 lookat;   // Where the light should look at
    vec3 colour;   // The light's colour (RGB)
    float intensity; // Light intensity
    float fov;     // Field of view in degrees
    float maxDistance; // Maximum effective distance for the light
    mat4 lightSpaceMatrix; //The matrix for the light's position etc.
    sampler2D shadowMap; //Mapping of shadows from the light's perspective
};

uniform int numLights;   // Number of active lights
uniform Light LIGHTS[10]; // Array of light structures, with a maximum of 1 light

float calculateShadow(Light light, vec3 norm, vec3 lightDir, vec4 fragPosLightSpace) {
    // Perform perspective division
    vec3 projCoords = fragPosLightSpace.xyz / fragPosLightSpace.w;
    projCoords = projCoords * 0.5 + 0.5; // Transform to [0,1] range

    // Check if fragment is outside the light's frustum
    if (projCoords.z > 1.0) {
        return 1.0;
    }

    float shadow = 0.0;
    vec2 texelSize = 1.0 / textureSize(light.shadowMap, 0);
    float currentDepth = projCoords.z;

    // PCF kernel size
    int kernelSize = 5; // Can be adjusted for higher quality

    // Iterate over the kernel
    for (int x = -kernelSize; x <= kernelSize; ++x) {
        for (int y = -kernelSize; y <= kernelSize; ++y) {
            float pcfDepth = texture(light.shadowMap, projCoords.xy + vec2(x, y) * texelSize).r;
		    float bias = 0.05e-7 * max(1.0 - dot(norm, lightDir), 0.01);
            shadow += currentDepth - bias > pcfDepth ? 1.0 : 0.0; // Adjust bias value as needed
        }
    }

    shadow /= (kernelSize * 2 + 1) * (kernelSize * 2 + 1);
    return shadow;
}

void main() {
    // Calculate the distance from the fragment to the camera
    float depth = length(cameraPos - fragPos);

    // If the fragment is beyond the maximum view distance, set it to the void colour
    if (depth >= maxViewDistance) {
        fragColour = vec4(0.0);
        return;
    }

    // Get the texture color
    vec4 texColour = texture(texture1, fragTexCoords);
    vec3 finalColour = vec3(0.05); // Initialize final color
    vec3 norm = normalize(fragNormal);

    // Iterate through each light and check if the fragment is within the light's FOV
    for (int i = 0; i < numLights; i++) {
    	float distance = length(LIGHTS[i].position - fragPos);
        vec3 lightDir = normalize(LIGHTS[i].lookat - fragPos); // Direction to the light
        vec3 lightForward = normalize(LIGHTS[i].position - LIGHTS[i].lookat); // Light's forward direction

        // Calculate the angle between the light direction and the light's forward direction
        float cosTheta = dot(lightDir, lightForward); // Dot product of normalized vectors
        float angle = degrees(acos(cosTheta)); // Angle in degrees

        vec4 fragPosLightSpace = LIGHTS[i].lightSpaceMatrix * vec4(fragPos, 1.0);

        float attenuation = max(0.0, 1.0 - (distance / LIGHTS[i].maxDistance));
        float diff = max(1.0 - abs(dot(norm, lightDir) / 90), 0.0);
        float shadow = calculateShadow(LIGHTS[i], norm, lightDir, fragPosLightSpace);
        float brightness = attenuation * LIGHTS[i].intensity * diff * (1.0 - shadow);

        // Check if the angle is within the light's field of view
        if (angle <= LIGHTS[i].fov * 0.5) {
            // If within the FOV, add the texture color to the final color
            if (brightness <= 0.05){
            finalColour += texColour.rgb * 0.05 * LIGHTS[i].colour;	
            }
            else {
	            finalColour += texColour.rgb * brightness * LIGHTS[i].colour;
            }
        }
    }
	fragColour = vec4(finalColour, texColour.a);

}
