#version 330 core
layout(location = 0) in vec3 Position;
layout(location = 1) in vec2 TexCoords;

out vec2 fragTexCoords;

void main()
{
	//Basic vertex shader for the UI quads.
	fragTexCoords = TexCoords;
	gl_Position = vec4(Position, 1.0);
}