// Drawn over a character's own materials: pirate rust (mode 0) or infection veins (mode 1).
shader_type spatial;
render_mode blend_add, unshaded, cull_back, depth_draw_never;
uniform int mode = 0;
uniform vec3 color : source_color = vec3(0.6, 0.25, 0.1);
varying vec3 world_pos;

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	if (mode == 1) {
		float v = smoothstep(0.75, 1.0, sin(world_pos.y * 22.0 + sin(world_pos.x * 13.0 + TIME) * 2.5) * 0.5 + 0.5);
		float pulse = 0.6 + 0.4 * sin(TIME * 4.0 + world_pos.y * 3.0);
		ALBEDO = color * (0.25 + v * 1.6 * pulse);
	} else {
		ALBEDO = color * 0.35;
	}
}
