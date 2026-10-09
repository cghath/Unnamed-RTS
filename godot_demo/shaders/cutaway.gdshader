// Ship and station surfaces. Everything above the global cut_height is cut away so the
// commander can look into a deck (cut_height is 10000 when the cutaway is off).
shader_type spatial;
render_mode cull_disabled;

global uniform float cut_height;
uniform vec4 albedo : source_color = vec4(1.0);
uniform float metallic = 0.3;
uniform float roughness = 0.6;
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
	METALLIC = metallic;
	ROUGHNESS = roughness;
	EMISSION = emission * emission_energy;
}
