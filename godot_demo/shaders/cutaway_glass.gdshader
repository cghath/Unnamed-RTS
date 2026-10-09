// Transparent version (glass, energy shields) of cutaway.gdshader.
shader_type spatial;
render_mode cull_disabled, blend_mix, depth_draw_never;

global uniform float cut_height;
uniform vec4 albedo : source_color = vec4(1.0);
uniform vec3 emission_color : source_color = vec3(0.0);
uniform float emission_energy = 0.0;
varying vec3 world_pos;

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	if (world_pos.y > cut_height) {
		discard;
	}
	ALBEDO = albedo.rgb;
	ALPHA = albedo.a;
	ROUGHNESS = 0.1;
	EMISSION = emission_color * emission_energy;
}
