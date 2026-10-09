shader_type spatial;
render_mode unshaded, blend_add, cull_front, depth_draw_never;
// A soft glow around a planet's limb.

uniform vec4 tint : source_color = vec4(0.5, 0.75, 1.0, 0.5);

void fragment() {
	float rim = 1.0 - abs(dot(NORMAL, VIEW));
	float a = pow(clamp(1.0 - rim, 0.0, 1.0), 3.0) * tint.a;
	ALBEDO = tint.rgb * a;
}
