// MESHSETUP.GLSL
// sets up a mesh for rendering

#ifdef VERTEX_SHADER
in vec3 position;
uniform mat4 u_mvp;
void main() {
    gl_Position = u_mvp * vec4(position, 1.0);
}
#endif

#ifdef FRAGMENT_SHADER
uniform vec4 u_color;
out vec4 fragColor;
void main() {
    fragColor = u_color;
}
#endif
