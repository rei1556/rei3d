// MESHSETUP.GLSL
// sets up a mesh for rendering

#ifdef VERTEX_SHADER
in vec3 position;
in vec2 uv;
uniform mat4 u_mvp;
out vec2 v_uv;
void main() {
    v_uv = uv;
    gl_Position = u_mvp * vec4(position, 1.0);
}
#endif

#ifdef FRAGMENT_SHADER
in vec2 v_uv;
uniform vec4 u_color;
uniform sampler2D u_tex;
out vec4 fragColor;
void main() {
    fragColor = vec4(texture(u_tex, v_uv).rgb, 1.0);
    //fragColor = texture(u_tex, v_uv) * u_color;   
}
#endif