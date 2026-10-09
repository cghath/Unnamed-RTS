// The infection growing over a ship or station: violet veins and glowing nodes, drawn
// as an overlay only inside infected compartment boxes (in the vessel's own space).
shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_disabled;

global uniform float cut_height;
uniform mat4 to_local;
uniform int count = 0;
uniform vec3 bmin[32];
uniform vec3 bmax[32];
uniform float growth[32];
varying vec3 wpos;

float hash(vec3 p) {
	p = fract(p * 0.3183099 + 0.1);
	p *= 17.0;
	return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
}

float noise(vec3 x) {
	vec3 i = floor(x);
	vec3 f = fract(x);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(mix(hash(i), hash(i + vec3(1, 0, 0)), f.x), mix(hash(i + vec3(0, 1, 0)), hash(i + vec3(1, 1, 0)), f.x), f.y),
		mix(mix(hash(i + vec3(0, 0, 1)), hash(i + vec3(1, 0, 1)), f.x), mix(hash(i + vec3(0, 1, 1)), hash(i + vec3(1, 1, 1)), f.x), f.y), f.z);
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	if (wpos.y > cut_height) {
		discard;
	}
	vec3 lp = (to_local * vec4(wpos, 1.0)).xyz;
	float g = 0.0;
	for (int i = 0; i < 32; i++) {
		if (i >= count) {
			break;
		}
		vec3 c = (bmin[i] + bmax[i]) * 0.5;
		vec3 h = (bmax[i] - bmin[i]) * 0.5 * growth[i];
		vec3 d = abs(lp - c) - h;
		if (max(d.x, max(d.y, d.z)) < 0.0) {
			g = max(g, growth[i]);
		}
	}
	if (g <= 0.0) {
		discard;
	}
	float n = noise(lp * 1.7) * 0.6 + noise(lp * 4.3) * 0.4;
	float vein = smoothstep(0.46, 0.5, n) * (1.0 - smoothstep(0.5, 0.55, n));
	float blob = smoothstep(0.78, 0.86, noise(lp * 0.9 + 3.0));
	float a = max(vein, blob) * g;
	if (a < 0.05) {
		discard;
	}
	float pulse = 0.6 + 0.4 * sin(TIME * 2.0 + n * 12.0);
	ALBEDO = mix(vec3(0.08, 0.03, 0.10), vec3(0.22, 0.05, 0.28), blob);
	EMISSION = vec3(0.55, 0.12, 0.85) * (vein * 0.7 + blob * 0.15) * pulse;
	ALPHA = clamp(a * 0.85, 0.0, 0.9);
	ROUGHNESS = 0.3;
}
