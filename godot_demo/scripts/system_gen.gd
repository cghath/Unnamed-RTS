extends RefCounted
## Procedural star system: everything about the battlefield that changes from match to
## match, from one seed (the host's seed in multiplayer, so every client builds the same).
##
##   layout(seed) -> Dictionary   where the stations, fleets, pirates and derelict go, the
##                                asteroid fields, the sun, the planet and the system's name
##   build(parent, layout)        makes the scenery: sun light, sky tint, planet (with a
##                                ring sometimes), nebula glow and the asteroid fields

const NAMES_A := ["Kepler", "Varga", "Oris", "Tamsin", "Hale", "Morrow", "Calder", "Ixion", "Seren", "Durrow", "Achen", "Vey"]
const NAMES_B := ["Reach", "Drift", "Expanse", "Gate", "Deep", "Hollow", "Verge", "Narrows", "Crossing", "Belt"]


const SCALE := 1.35               # the system is spread out: ships are small in a big sandbox
const ORES := {"iron": ["alloys", Color(0.36, 0.3, 0.27)], "ice": ["fuel", Color(0.55, 0.62, 0.68)],
	"crystal": ["circuitry", Color(0.32, 0.36, 0.46)], "core": ["cores", Color(0.42, 0.3, 0.38)]}


static func layout(seed_: int) -> Dictionary:
	var r := RandomNumberGenerator.new()
	r.seed = seed_ * 7919 + 13
	var S := SCALE
	var L := {}
	L["name"] = "%s %s" % [NAMES_A[r.randi() % NAMES_A.size()], NAMES_B[r.randi() % NAMES_B.size()]]
	# the two home stations face each other across the system, never quite on a line
	var hx := r.randf_range(1700.0, 2150.0) * S
	L["home1"] = Vector3(-hx, 0, r.randf_range(-450.0, 450.0) * S)
	L["home2"] = Vector3(hx, 0, r.randf_range(-450.0, 450.0) * S)
	# pirates in the north or the south (on a big asteroid), the derelict on the other side
	var ps := 1.0 if r.randf() < 0.5 else -1.0
	L["pirate"] = Vector3(r.randf_range(-450.0, 450.0) * S, 0, -ps * r.randf_range(1050.0, 1500.0) * S)
	L["pirate_rock"] = r.randf_range(170.0, 230.0)                 # the asteroid the haven is dug into
	L["pirate_mine"] = L["pirate"] + Vector3(r.randf_range(-1, 1), 0, r.randf_range(-1, 1)).normalized() * 120.0
	L["pirate_ship"] = L["pirate"] + Vector3(r.randf_range(-250.0, 250.0), 0, ps * r.randf_range(380.0, 520.0)) * S
	L["pirate_raider"] = r.randf() < 0.6                 # sometimes the pirates have a bigger ship out
	L["raider_pos"] = L["pirate"] + Vector3(r.randf_range(-500.0, 500.0), 0, ps * r.randf_range(320.0, 480.0)) * S
	L["derelict"] = Vector3(r.randf_range(-550.0, 550.0) * S, 0, ps * r.randf_range(950.0, 1350.0) * S)
	L["derelict_yaw"] = r.randf_range(-PI, PI)
	# fleet stations: flagship, frigate, drop frigate and supply ship near home, toward the enemy
	for t in [1, 2]:
		var h: Vector3 = L["home%d" % t]
		var toward := -signf(h.x)
		var flip := 1.0 if r.randf() < 0.5 else -1.0
		L["flag%d" % t] = h + Vector3(toward * r.randf_range(380.0, 520.0), 0, flip * r.randf_range(240.0, 340.0))
		L["frigate%d" % t] = h + Vector3(toward * r.randf_range(380.0, 520.0), 0, -flip * r.randf_range(300.0, 400.0))
		L["dropfrig%d" % t] = h + Vector3(toward * r.randf_range(560.0, 680.0), 0, flip * r.randf_range(-60.0, 60.0))
		L["support%d" % t] = h + Vector3(toward * r.randf_range(200.0, 280.0), 0, flip * r.randf_range(-80.0, 80.0))
	# asteroid fields: maybe none, maybe several, each with its own ore; a few huge rocks
	# in each to fight around (they stop gunfire), and sometimes a mining base on the biggest
	var keep := [L["home1"], L["home2"], L["pirate"], L["derelict"], L["flag1"], L["flag2"], L["frigate1"], L["frigate2"],
		L["raider_pos"], L["dropfrig1"], L["dropfrig2"]]
	var fields: Array = []
	var tries := 0
	var roll := r.randf()
	var want := 0 if roll < 0.12 else (1 + r.randi() % 5)
	while fields.size() < want and tries < 80:
		tries += 1
		var c := Vector3(r.randf_range(-1600.0, 1600.0) * S, r.randf_range(-60.0, 60.0), r.randf_range(-1400.0, 1400.0) * S)
		var rad := r.randf_range(260.0, 520.0)
		var ok := true
		for k in keep:
			if Vector2(c.x - k.x, c.z - k.z).length() < rad + 350.0:
				ok = false
		for f in fields:
			if Vector2(c.x - f["center"].x, c.z - f["center"].z).length() < rad + f["radius"] + 120.0:
				ok = false
		if not ok:
			continue
		var ore: String = ["iron", "iron", "ice", "crystal", "core"][r.randi() % 5]
		var big: Array = []
		for i in 3 + r.randi() % 5:
			var d := Vector3(r.randfn(), r.randfn() * 0.15, r.randfn()).normalized() * r.randf_range(0.0, 0.85) * rad
			big.append({"pos": c + d, "radius": r.randf_range(35.0, 110.0), "seed": r.randi()})
		fields.append({"center": c, "radius": rad, "count": int(rad * 0.6), "seed": r.randi(), "ore": ore,
			"resource": ORES[ore][0], "amount": r.randf_range(3000.0, 9000.0) * (0.35 if ore == "core" else 1.0), "big": big})
	L["fields"] = fields
	L["field_mine"] = -1
	if not fields.is_empty() and r.randf() < 0.7:
		L["field_mine"] = r.randi() % fields.size()             # a pirate-held mining base in that field
	# sky
	L["sun_rot"] = Vector3(r.randf_range(-55.0, -25.0), r.randf_range(0.0, 360.0), 0)
	var warm := r.randf()
	L["sun_color"] = Color(1.0, lerpf(0.85, 1.0, warm), lerpf(0.7, 1.0, warm))
	L["nebula"] = Color.from_hsv(r.randf(), r.randf_range(0.45, 0.8), 1.0)
	L["planet"] = {"dir": Vector3(r.randf_range(-1, 1), r.randf_range(-0.35, 0.1), r.randf_range(-1, 1)).normalized(),
		"radius": r.randf_range(900.0, 2200.0), "color": Color.from_hsv(r.randf(), r.randf_range(0.2, 0.6), r.randf_range(0.35, 0.7)),
		"ring": r.randf() < 0.45}
	return L


## Every big rock in the system (fields and the bases' asteroids): [centre, radius].
static func big_rocks(L: Dictionary) -> Array:
	var out: Array = []
	for f in L.get("fields", []):
		for b in f["big"]:
			out.append([b["pos"], b["radius"]])
	if L.has("pirate"):
		out.append([L["pirate"] - Vector3(0, L["pirate_rock"] * 0.95, 0), L["pirate_rock"]])
	out += L.get("extra_rocks", [])
	return out


## Does the segment a-b pass through a big rock? Returns the hit point or Vector3.INF.
static func rock_hit(rocks: Array, a: Vector3, b: Vector3) -> Vector3:
	var d := b - a
	var l := d.length()
	if l < 0.01:
		return Vector3.INF
	var u := d / l
	var best := INF
	for rk in rocks:
		var c: Vector3 = rk[0]
		var rad: float = rk[1] * 0.8                     # the lumps are a little inside the bounding sphere
		var t := (c - a).dot(u)
		if t < 0.0 or t > l:
			continue
		if (a + u * t).distance_to(c) < rad:
			var back := sqrt(maxf(0.0, rad * rad - (a + u * t).distance_squared_to(c)))
			best = minf(best, maxf(0.0, t - back))
	return a + u * best if best < INF else Vector3.INF


static func build(parent: Node3D, L: Dictionary) -> void:
	# a faint nebula wash on the sky
	for i in 5:
		var q := MeshInstance3D.new()
		var qm := QuadMesh.new()
		qm.size = Vector2(9000, 5000) * (0.7 + 0.15 * i)
		q.mesh = qm
		var m := StandardMaterial3D.new()
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
		m.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
		var c: Color = L["nebula"]
		m.albedo_color = Color(c.r, c.g, c.b, 0.025)
		m.albedo_texture = _soft_texture()
		q.material_override = m
		q.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var a := float(i) * 1.1 + c.h * 6.0
		q.position = Vector3(cos(a), 0.25 - 0.1 * i, sin(a)) * 10500.0
		parent.add_child(q)
	# the planet, far off, with a ring sometimes (the campaign builds its own worlds)
	var P: Dictionary = L["planet"]
	if P.is_empty():
		_rocks_and_fields(parent, L)
		return
	var pl := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = P["radius"]
	sm.height = P["radius"] * 2.0
	sm.radial_segments = 48
	sm.rings = 24
	pl.mesh = sm
	var pm := StandardMaterial3D.new()
	pm.albedo_color = P["color"]
	pm.roughness = 0.9
	pm.rim_enabled = true
	pm.rim = 0.6
	pl.material_override = pm
	pl.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	pl.position = (P["dir"] as Vector3) * 9000.0
	parent.add_child(pl)
	if P["ring"]:
		var ring := MeshInstance3D.new()
		var tm := TorusMesh.new()
		tm.inner_radius = P["radius"] * 1.35
		tm.outer_radius = P["radius"] * 1.9
		tm.rings = 64
		ring.mesh = tm
		ring.scale = Vector3(1, 0.02, 1)
		var rm := StandardMaterial3D.new()
		rm.albedo_color = Color(P["color"].r * 1.2, P["color"].g * 1.15, P["color"].b, 0.55)
		rm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		ring.material_override = rm
		ring.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		ring.position = pl.position
		ring.rotation = Vector3(0.35, 0.4, 0.1)
		parent.add_child(ring)
	_rocks_and_fields(parent, L)


static func _rocks_and_fields(parent: Node3D, L: Dictionary) -> void:
	# the huge rocks (fight around these) and the pirates' asteroid
	for rk in big_rocks(L):
		var gr := RandomNumberGenerator.new()
		gr.seed = int(rk[0].x * 13.0 + rk[0].z * 7.0)
		var mi := MeshInstance3D.new()
		mi.mesh = _rock_mesh(gr)
		var gm := StandardMaterial3D.new()
		gm.albedo_color = Color(0.29, 0.26, 0.24)
		gm.roughness = 0.97
		mi.material_override = gm
		mi.position = rk[0]
		mi.scale = Vector3(rk[1], rk[1] * gr.randf_range(0.6, 0.9), rk[1] * gr.randf_range(0.8, 1.1))
		mi.rotation = Vector3(gr.randf_range(-0.4, 0.4), gr.randf() * TAU, gr.randf_range(-0.4, 0.4))
		parent.add_child(mi)
	# asteroid fields: a few rock shapes, scattered with a MultiMesh per shape, tinted by their ore
	for f in L["fields"]:
		var rock_mat := StandardMaterial3D.new()
		rock_mat.albedo_color = ORES.get(f.get("ore", "iron"), ["", Color(0.3, 0.27, 0.25)])[1]
		rock_mat.roughness = 0.95
		var fr := RandomNumberGenerator.new()
		fr.seed = f["seed"]
		var shapes: Array = []
		for k in 4:
			shapes.append(_rock_mesh(fr))
		var mms: Array = []
		for k in 4:
			var mm := MultiMesh.new()
			mm.transform_format = MultiMesh.TRANSFORM_3D
			mm.mesh = shapes[k]
			mm.instance_count = int(f["count"] / 4.0) + 1
			mms.append(mm)
		for k in 4:
			var mm: MultiMesh = mms[k]
			for i in mm.instance_count:
				var d := Vector3(fr.randfn(), fr.randfn() * 0.25, fr.randfn()).normalized() * fr.randf_range(0.0, 1.0)
				var s := fr.randf_range(5.0, 24.0) if fr.randf() < 0.85 else fr.randf_range(30.0, 70.0)
				var b := Basis(Vector3(fr.randfn(), fr.randfn(), fr.randfn()).normalized(), fr.randf_range(0, TAU)).scaled(Vector3(s, s * fr.randf_range(0.6, 1.0), s))
				mm.set_instance_transform(i, Transform3D(b, f["center"] + d * f["radius"]))
			var mi := MultiMeshInstance3D.new()
			mi.multimesh = mm
			mi.material_override = rock_mat
			parent.add_child(mi)


## A lumpy rock: a low-poly sphere with each vertex pushed in or out.
static func _rock_mesh(r: RandomNumberGenerator) -> ArrayMesh:
	var sm := SphereMesh.new()
	sm.radius = 1.0
	sm.height = 2.0
	sm.radial_segments = 10
	sm.rings = 6
	var arr: Array = sm.get_mesh_arrays()
	var verts: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
	var bumps: Array = []
	for i in 7:
		bumps.append([Vector3(r.randfn(), r.randfn(), r.randfn()).normalized(), r.randf_range(-0.35, 0.3)])
	for i in verts.size():
		var v := verts[i]
		var k := 1.0
		for b in bumps:
			k += b[1] * maxf(0.0, v.normalized().dot(b[0])) ** 3
		verts[i] = v * k
	arr[Mesh.ARRAY_VERTEX] = verts
	arr[Mesh.ARRAY_NORMAL] = null
	var st := SurfaceTool.new()
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	st.create_from(am, 0)
	st.generate_normals()
	return st.commit()


static var _tex: Texture2D = null


static func _soft_texture() -> Texture2D:
	if _tex:
		return _tex
	var g := Gradient.new()
	g.set_color(0, Color(1, 1, 1, 1))
	g.set_color(1, Color(1, 1, 1, 0))
	var gt := GradientTexture2D.new()
	gt.gradient = g
	gt.fill = GradientTexture2D.FILL_RADIAL
	gt.fill_from = Vector2(0.5, 0.5)
	gt.fill_to = Vector2(0.5, 0.0)
	gt.width = 128
	gt.height = 128
	_tex = gt
	return _tex
