// Glass and energy shields, with the same deck cutaway.
shader_type spatial;
render_mode cull_disabled, depth_draw_never;

global uniform float cut_height;
uniform vec4 albedo : source_color = vec4(1.0);
uniform vec3 emission : source_color = vec3(0.0);
uniform float emission_energy = 0.0;
varying vec3 wpos;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	if (wpos.y > cut_height) {
		discard;
	}
	ALBEDO = albedo.rgb;
	EMISSION = emission * emission_energy;
	ALPHA = albedo.a;
	ROUGHNESS = 0.1;
}
