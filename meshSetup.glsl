// MESHSETUP.GLSL
// sets up a mesh for rendering

#ifdef VERTEX_SHADER
in vec3 position;
uniform vec3 u_position;
void main() {
    gl_Position = vec4(position + u_position, 1.0);
    
}
#endif

#ifdef FRAGMENT_SHADER
uniform vec4 u_color;
out vec4 fragColor;
void main() {
    fragColor = u_color;
}
#endif
