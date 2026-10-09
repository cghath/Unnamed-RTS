// Overlay for infected robots and their gear: violet growth over the plating.
shader_type spatial;
render_mode blend_mix, depth_draw_never;

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

varying vec3 opos;

void vertex() {
	opos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz - NODE_POSITION_WORLD;
}

void fragment() {
	float n = noise(opos * 11.0) * 0.6 + noise(opos * 27.0) * 0.4;
	float a = smoothstep(0.38, 0.55, n);
	if (a < 0.05) {
		discard;
	}
	float pulse = 0.6 + 0.4 * sin(TIME * 3.0 + n * 9.0);
	ALBEDO = vec3(0.16, 0.03, 0.2);
	EMISSION = vec3(0.6, 0.12, 1.0) * smoothstep(0.55, 0.62, n) * 2.0 * pulse;
	ALPHA = a * 0.92;
}
