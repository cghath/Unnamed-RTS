shader_type spatial;
// A procedural planet: fractal noise over the sphere picks sea, lowland, highland and peaks;
// gas giants get bands instead; infected worlds glow along creeping veins.

uniform vec4 col_deep : source_color = vec4(0.1, 0.2, 0.4, 1.0);
uniform vec4 col_low : source_color = vec4(0.3, 0.45, 0.2, 1.0);
uniform vec4 col_high : source_color = vec4(0.45, 0.4, 0.3, 1.0);
uniform vec4 col_peak : source_color = vec4(0.9, 0.9, 0.9, 1.0);
uniform float sea = 0.4;
uniform float seed = 0.0;
uniform float gas = 0.0;
uniform float infected = 0.0;
uniform float lava = 0.0;

varying vec3 obj_n;

float hash(vec3 p) {
	p = fract(p * 0.3183099 + vec3(0.1, 0.2, 0.3) + seed * 0.0137);
	p *= 17.0;
	return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
}

float noise(vec3 x) {
	vec3 i = floor(x);
	vec3 f = fract(x);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(mix(hash(i + vec3(0, 0, 0)), hash(i + vec3(1, 0, 0)), f.x),
				   mix(hash(i + vec3(0, 1, 0)), hash(i + vec3(1, 1, 0)), f.x), f.y),
			   mix(mix(hash(i + vec3(0, 0, 1)), hash(i + vec3(1, 0, 1)), f.x),
				   mix(hash(i + vec3(0, 1, 1)), hash(i + vec3(1, 1, 1)), f.x), f.y), f.z);
}

float fbm(vec3 p) {
	float v = 0.0;
	float a = 0.5;
	for (int i = 0; i < 6; i++) {
		v += a * noise(p);
		p = p * 2.03 + vec3(1.7, 9.2, 3.1);
		a *= 0.5;
	}
	return v;
}

void vertex() {
	obj_n = normalize(VERTEX);
}

void fragment() {
	vec3 p = obj_n * 2.2 + vec3(seed);
	float h = fbm(p);
	vec3 c;
	float rough = 0.9;
	float glow = 0.0;
	if (gas > 0.5) {
		float band = sin(obj_n.y * 14.0 + fbm(p * vec3(0.6, 3.0, 0.6)) * 5.0);
		float t = band * 0.5 + 0.5;
		c = mix(mix(col_low.rgb, col_high.rgb, t), col_peak.rgb, smoothstep(0.7, 1.0, fbm(p * 2.0)) * 0.5);
		c = mix(c, col_deep.rgb, smoothstep(0.62, 0.8, fbm(p * 1.3 + 4.0)) * 0.4);
		rough = 0.6;
	} else {
		float s = mix(0.3, 0.62, sea);
		if (h < s && sea > 0.01) {
			c = col_deep.rgb * (0.7 + 0.5 * h);
			rough = lava > 0.5 ? 0.9 : 0.25;
			if (lava > 0.5) glow = 2.2 * (1.0 - h / s);
		} else {
			float t = clamp((h - s) / (1.0 - s), 0.0, 1.0);
			c = mix(col_low.rgb, col_high.rgb, smoothstep(0.05, 0.45, t));
			c = mix(c, col_peak.rgb, smoothstep(0.42, 0.62, t));
		}
		// polar caps on temperate worlds
		if (sea > 0.2 && lava < 0.5 && infected < 0.5) {
			c = mix(c, vec3(0.92, 0.95, 1.0), smoothstep(0.78, 0.9, abs(obj_n.y) + h * 0.15));
		}
		// cloud wisps
		float cl = smoothstep(0.55, 0.75, fbm(p * 1.6 + vec3(TIME * 0.003)));
		if (sea > 0.2 && lava < 0.5) c = mix(c, vec3(0.95), cl * 0.6);
	}
	if (infected > 0.5) {
		float v = abs(fbm(p * 3.0) - 0.5);
		float vein = 1.0 - smoothstep(0.0, 0.035, v);
		c = mix(c, vec3(0.8, 0.3, 1.0), vein * 0.8);
		glow += vein * 1.6;
	}
	ALBEDO = c;
	ROUGHNESS = rough;
	EMISSION = (lava > 0.5 ? vec3(1.0, 0.4, 0.1) : vec3(0.8, 0.3, 1.0)) * glow;
}
