shader_type sky;
// Deep space: a scatter of stars and a faint nebula wash, drawn at infinity.
uniform vec3 nebula : source_color = vec3(0.3, 0.4, 0.8);

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

void sky() {
	vec3 d = normalize(EYEDIR);
	vec3 c = vec3(0.006, 0.008, 0.016);
	float n = noise(d * 2.5) * 0.6 + noise(d * 6.0) * 0.4;
	c += nebula * pow(n, 3.0) * 0.07;
	vec3 cell = floor(d * 260.0);
	float h = hash(cell);
	if (h > 0.985) {
		vec3 ctr = (cell + 0.5) / 260.0;
		float dist = length(d - normalize(ctr)) * 260.0;
		c += vec3(0.85, 0.9, 1.0) * smoothstep(0.5, 0.0, dist) * (h - 0.985) * 66.0;
	}
	COLOR = c;
}
