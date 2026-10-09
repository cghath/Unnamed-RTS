extends RefCounted
## Player outposts on a world. Found one at an open (or cleared) base location or at the
## landing zone with a command post (HQ), then build round it: barracks that train
## riflemen, a supply depot that rearms troops and patches vehicles, gun emplacements,
## sandbag walls, an ore extractor, a motor pool. Structures go on the ground and the
## navigation is rebaked under them; they stay on the world between visits.
##   world[base key] = {"team": 1, "outpost": true, "structs": [[type, x, z, yaw], ...]}
## Lose the command post and the outpost falls (the location is open again).

const OUTPOST := preload("res://scripts/campaign/outpost.gd")
const RUINS := preload("res://scripts/campaign/ruins.gd")
const SURFACE := preload("res://scripts/campaign/surface.gd")
const REACH := 150.0                 # how far from the command post you can build

const STRUCTS := {
	"hq": {"label": "Command post (founds the outpost)", "alloys": 600, "circuitry": 150, "size": Vector3(16, 5, 12), "hp": 6000.0},
	"barracks": {"label": "Barracks (trains 4 riflemen every 90 s: 40 alloys + 4 cores)", "alloys": 300, "circuitry": 40, "size": Vector3(14, 4, 10), "hp": 3000.0},
	"depot": {"label": "Supply depot (rearms troops, refills med pens, repairs vehicles)", "alloys": 200, "circuitry": 10, "size": Vector3(9, 3, 9), "hp": 1800.0},
	"turret": {"label": "Gun emplacement (heavy gun, manned by the outpost)", "alloys": 220, "circuitry": 60, "size": Vector3(5, 3, 5), "hp": 1600.0},
	"wall": {"label": "Sandbag wall (cover)", "alloys": 30, "circuitry": 0, "size": Vector3(12, 1.2, 1.2), "hp": 900.0},
	"extractor": {"label": "Ore extractor (+1.2 ore/s to stores)", "alloys": 260, "circuitry": 40, "size": Vector3(8, 9, 8), "hp": 2000.0},
	"motor_pool": {"label": "Motor pool (repairs vehicles fast)", "alloys": 260, "circuitry": 50, "size": Vector3(16, 5, 12), "hp": 2500.0},
}


static func _ground_y(m: Node, x: float, z: float) -> float:
	return m.ground_y(x, z)


## The base locations in this zone where we could found an outpost, or have one:
##   [{key, pos, state: "open" / "ours" / "held", name}]
static func sites(m: Node) -> Array:
	var c = G.campaign
	var out: Array = []
	var L: Dictionary = m.system
	var lz: Vector3 = L["landing"]
	var lzk := "%d_%d_%d_lz" % [c.current, int(c.surface["planet"]), int(c.surface["site"])]
	var wl: Dictionary = c.world.get(lzk, {})
	out.append({"key": lzk, "pos": Vector3(lz.x, 0, lz.z) + Vector3(180, 0, 0), "state": "ours" if wl.get("outpost", false) else "open", "name": "Landing zone"})
	for i in L["bases"].size():
		var bs: Dictionary = L["bases"][i]
		var w: Dictionary = c.world.get(bs["key"], {})
		var state := "held"
		if w.get("outpost", false):
			state = "ours"
		elif w.get("destroyed", false) or bs["kind"] in ["outpost_site", "ruins"] and int(w.get("team", 0)) == 0:
			state = "open"
		out.append({"key": bs["key"], "pos": Vector3(bs["pos"].x, 0, bs["pos"].z), "state": state,
			"name": "Base location %d (%s)" % [i + 1, String(bs["kind"]).replace("_", " ")]})
	return out


static func found(m: Node, site: Dictionary) -> String:
	var c = G.campaign
	if site["state"] != "open":
		return "That location isn't open (clear it first)"
	var r: Dictionary = c.stores
	var cost: Dictionary = STRUCTS["hq"]
	if float(r.get("alloys", 0.0)) < cost["alloys"] or float(r.get("circuitry", 0.0)) < cost["circuitry"]:
		return "A command post needs %d alloys and %d circuitry" % [cost["alloys"], cost["circuitry"]]
	r["alloys"] = float(r["alloys"]) - cost["alloys"]
	r["circuitry"] = float(r["circuitry"]) - cost["circuitry"]
	var p: Vector3 = site["pos"]
	c.world[site["key"]] = {"team": 1, "outpost": true, "structs": [["hq", p.x, p.z, 0.0]]}
	build(m, "hq", Vector3(p.x, 0, p.z), 0.0, site["key"], true)
	return "Outpost founded: %s. Build round the command post (within %d m)" % [site["name"], int(REACH)]


## The command posts we have in this zone (live nodes).
static func hqs(m: Node) -> Array:
	return m.outposts.filter(func(o): return is_instance_valid(o) and not o.destroyed and o.team == 1 and o.part == "core")


static func can_place(m: Node, type: String, p: Vector3) -> String:
	var hq: Node = null
	for h in hqs(m):
		if Vector2(h.global_position.x - p.x, h.global_position.z - p.z).length() < REACH:
			hq = h
	if hq == null:
		return "Too far from a command post (%d m)" % int(REACH)
	var sz: Vector3 = STRUCTS[type]["size"]
	for o in m.outposts:
		if is_instance_valid(o) and o.team == 1 and not o.destroyed:
			var other: Vector3 = o.aabb.size
			var need := (maxf(sz.x, sz.z) + maxf(other.x, other.z)) * 0.5 * (0.6 if type == "wall" or o.part == "wall" else 0.85)
			if Vector2(o.global_position.x - p.x, o.global_position.z - p.z).length() < need:
				return "Too close to the %s" % o.display_name
	var r: Dictionary = G.campaign.stores
	if float(r.get("alloys", 0.0)) < STRUCTS[type]["alloys"] or float(r.get("circuitry", 0.0)) < STRUCTS[type]["circuitry"]:
		return "Needs %d alloys and %d circuitry" % [STRUCTS[type]["alloys"], STRUCTS[type]["circuitry"]]
	return ""


static func place(m: Node, type: String, p: Vector3, yaw: float) -> String:
	var why := can_place(m, type, p)
	if why != "":
		return why
	var hq: Node = null
	for h in hqs(m):
		if Vector2(h.global_position.x - p.x, h.global_position.z - p.z).length() < REACH:
			hq = h
	var r: Dictionary = G.campaign.stores
	r["alloys"] = float(r["alloys"]) - STRUCTS[type]["alloys"]
	r["circuitry"] = float(r["circuitry"]) - STRUCTS[type]["circuitry"]
	var key: String = hq.base_key
	var w: Dictionary = G.campaign.world.get(key, {})
	var lst: Array = w.get("structs", [])
	lst.append([type, p.x, p.z, yaw])
	w["structs"] = lst
	G.campaign.world[key] = w
	build(m, type, p, yaw, key, true)
	return "%s built" % String(STRUCTS[type]["label"]).get_slice(" (", 0)


## Put one structure down. `runtime`: the ground's navigation is already baked, so carve
## the footprint out of it.
static func build(m: Node, type: String, p: Vector3, yaw: float, key: String, runtime: bool) -> Node3D:
	var gy := _ground_y(m, p.x, p.z)
	var spec: Dictionary = STRUCTS[type]
	var parts: Array = []
	for o in m.outposts:
		if is_instance_valid(o) and o.base_key == key and o.team == 1:
			parts = o.base
			break
	var part: String = {"hq": "core", "turret": "gun"}.get(type, type)
	var o: StaticBody3D = OUTPOST.new()
	(m.ground if m.ground != null and runtime else m).add_child(o)
	o.global_position = Vector3(p.x, gy, p.z)
	o.rotation.y = yaw
	o.init(part, 1, String(spec["label"]).get_slice(" (", 0), spec["size"], float(spec["hp"]) * (1.0 + G.tech_bonus(1, "outpost_hp")), key, parts)
	o.faction = 1
	o.set_meta("struct", type)
	m.outposts.append(o)
	var body := _mat(Color(0.42, 0.46, 0.42))
	var panel := _mat(Color(0.3, 0.33, 0.32))
	var dark := _mat(Color(0.12, 0.13, 0.14))
	var light := _mat(Color(0.4, 0.8, 1.0), 3.0)
	var sand := _mat(Color(0.62, 0.55, 0.4))
	var sz: Vector3 = spec["size"]
	match type:
		"hq":
			var hw := sz.x * 0.5
			var hd := sz.z * 0.5
			var walls := [[Vector3(-hw, 0, -hd), Vector3(hw, 0, -hd)], [Vector3(hw, 0, -hd), Vector3(hw, 0, hd)],
				[Vector3(hw, 0, hd), Vector3(-hw, 0, hd)], [Vector3(-hw, 0, hd), Vector3(-hw, 0, -hd)]]
			var r := RandomNumberGenerator.new()
			r.seed = hash(key)
			for k in 4:
				RUINS._window_wall(m, o, walls[k][0], walls[k][1], 3.6, body, k == 0 or k == 2, r, 0.0, 1.4)
			var roof := RUINS._block(o, Vector3(sz.x + 0.6, 0.4, sz.z + 0.6), Vector3(0, 3.8, 0), panel, true)
			if m.get("roofs") != null:
				m.roofs.append([roof, 1])
			RUINS._block(o, Vector3(3.0, 1.0, 1.2), Vector3(0, 0.5, 0), dark, true)          # the command table
			_cyl(o.visual, 0.1, 9.0, Vector3(hw - 1.0, 8.0, hd - 1.0), dark)                 # antenna
			_mesh(o.visual, BoxMesh.new(), Vector3(hw - 1.0, 12.6, hd - 1.0), light, Vector3(0.3, 0.3, 0.3))
			var fl := _mesh(o.visual, BoxMesh.new(), Vector3(-hw + 1.6, 7.5, -hd + 1.0), _mat(G.team_color(1)), Vector3(1.8, 1.1, 0.05))
			fl.name = "Flag"
			_cyl(o.visual, 0.08, 7.0, Vector3(-hw + 0.6, 3.5, -hd + 1.0), dark)
			var lab := Label3D.new()
			lab.text = "OUTPOST"
			lab.billboard = BaseMaterial3D.BILLBOARD_ENABLED
			lab.font_size = 48
			lab.pixel_size = 0.12
			lab.modulate = G.team_color(1)
			lab.position = Vector3(0, 16.0, 0)
			o.add_child(lab)
		"barracks":
			RUINS._block(o, Vector3(sz.x, 3.2, sz.z), Vector3(0, 1.6, 0), body, true)
			_mesh(o.visual, _cyl_mesh(sz.z * 0.5, sz.x), Vector3(0, 3.2, 0), panel, Vector3(0.45, 1.0, 1.0), Vector3(0, 0, PI * 0.5))
			_mesh(o.visual, BoxMesh.new(), Vector3(0, 1.3, sz.z * 0.5 + 0.02), dark, Vector3(2.4, 2.6, 0.1))
			_mesh(o.visual, BoxMesh.new(), Vector3(0, 2.9, sz.z * 0.5 + 0.1), light, Vector3(2.6, 0.12, 0.1))
		"depot":
			for k in 4:
				var cp := Vector3((k % 2) * 3.0 - 1.5, 0.6, (k / 2) * 3.0 - 1.5)
				RUINS._block(o, Vector3(2.2, 1.2, 2.2), cp, _mat(Color(0.5, 0.45, 0.25) if k % 2 == 0 else Color(0.85, 0.85, 0.88)), true)
			RUINS._block(o, Vector3(2.2, 1.2, 2.2), Vector3(-1.5, 1.8, -1.5), _mat(Color(0.5, 0.45, 0.25)), true)
			_mesh(o.visual, BoxMesh.new(), Vector3(0, 0.05, 0), _mat(Color(0.9, 0.75, 0.2), 0.6), Vector3(sz.x, 0.08, sz.z))
			for k in 4:
				var d := Vector3(sin(k * PI * 0.5), 0, cos(k * PI * 0.5))
				m.ground_cover.append([o.global_position + d * 4.0, true, -d])
		"turret":
			for k in 3:
				var ang := -PI * 0.5 + k * PI * 0.5
				var blk := RUINS._block(o, Vector3(3.6, 1.1, 0.9), Vector3(sin(ang), 0, -cos(ang)) * 2.2 + Vector3(0, 0.55, 0), sand, true)
				blk.rotation.y = ang
				(o.get_child(o.get_child_count() - 1) as Node3D).rotation.y = ang
			_cyl(o.visual, 0.15, 1.6, Vector3(0, 0.8, 0), dark, Vector3.ZERO)
			_mesh(o.visual, BoxMesh.new(), Vector3(0, 1.8, 0), body, Vector3(0.9, 0.6, 1.4))
			_cyl(o.visual, 0.09, 2.2, Vector3(0, 1.85, -1.6), dark, Vector3(PI * 0.5, 0, 0))
		"wall":
			for k in 3:
				RUINS._block(o, Vector3(3.9, 1.1, 1.0), Vector3(-4.0 + k * 4.0, 0.55, 0), sand, true)
			for s in [-4.0, 0.0, 4.0]:
				m.ground_cover.append([o.to_global(Vector3(s, 0, 1.2)), true, o.global_basis * Vector3(0, 0, -1)])
				m.ground_cover.append([o.to_global(Vector3(s, 0, -1.2)), true, o.global_basis * Vector3(0, 0, 1)])
		"extractor":
			RUINS._block(o, Vector3(6.0, 1.5, 6.0), Vector3(0, 0.75, 0), body, true)
			for sx in [-2.2, 2.2]:
				for sz2 in [-2.2, 2.2]:
					_cyl(o.visual, 0.2, 8.0, Vector3(sx, 4.5, sz2), dark, Vector3(0, 0, 0))
			_mesh(o.visual, BoxMesh.new(), Vector3(0, 8.4, 0), panel, Vector3(5.4, 0.6, 5.4))
			_cyl(o.visual, 0.5, 9.0, Vector3(0, 3.5, 0), _mat(Color(0.6, 0.45, 0.3)), Vector3.ZERO)
			_mesh(o.visual, BoxMesh.new(), Vector3(0, 9.0, 0), light, Vector3(0.6, 0.4, 0.6))
		"motor_pool":
			RUINS._block(o, Vector3(sz.x, 0.3, sz.z), Vector3(0, 0.15, 0), panel, false)
			for sx in [-1, 1]:
				RUINS._block(o, Vector3(0.6, 4.5, sz.z), Vector3(sx * (sz.x * 0.5 - 0.3), 2.25, 0), body, true)
			RUINS._block(o, Vector3(sz.x, 0.3, sz.z), Vector3(0, 4.6, 0), panel, false)
			RUINS._block(o, Vector3(2.0, 1.5, 3.0), Vector3(-sz.x * 0.5 + 2.0, 0.75, -sz.z * 0.5 + 2.0), dark, true)
			_mesh(o.visual, BoxMesh.new(), Vector3(0, 4.3, sz.z * 0.5), light, Vector3(sz.x * 0.8, 0.12, 0.1))
	if runtime and m.ground != null and m.ground.has_method("add_obstacle") and type != "motor_pool":
		m.ground.add_obstacle(o.global_position, Vector2(sz.x, sz.z), yaw)
	return o


## Rebuild what we've built on this world (called while the surface loads, before its
## navigation is baked, so it's part of it).
static func restore(m: Node) -> void:
	var c = G.campaign
	for k in c.world.keys():
		var w = c.world[k]
		if not (w is Dictionary) or not w.get("outpost", false):
			continue
		var bits: PackedStringArray = String(k).split("_")
		if bits.size() < 4 or int(bits[0]) != c.current or int(bits[1]) != int(c.surface["planet"]) or int(bits[2]) != int(c.surface["site"]):
			continue
		for st in w.get("structs", []):
			build(m, String(st[0]), Vector3(float(st[1]), 0, float(st[2])), float(st[3]), String(k), false)


## Once a campaign second on a world: what the outposts do.
static func tick(m: Node) -> void:
	var c = G.campaign
	var r: Dictionary = c.stores
	if m.ground == null:
		return
	for o in m.outposts:
		if not is_instance_valid(o) or o.destroyed or o.team != 1:
			continue
		var type: String = o.get_meta("struct", "")
		var p: Vector3 = o.global_position
		match type:
			"barracks":
				var t: float = float(o.get_meta("train_t", 90.0)) - 1.0
				if t <= 0.0:
					t = 90.0
					var near := 0
					for ch in m.ground.occupants:
						if is_instance_valid(ch) and ch.team == 1 and ch.state == "alive" and ch.global_position.distance_to(p) < 200.0:
							near += 1
					if near < 24 and float(r.get("alloys", 0.0)) >= 40.0 and float(r.get("cores", 0.0)) >= 4.0:
						r["alloys"] = float(r["alloys"]) - 40.0
						r["cores"] = float(r["cores"]) - 4.0
						m.spawn_squad(m.ground, m.ground.near_local(m.ground.to_local(p + o.global_basis.z * 9.0), 4.0), 1, 1,
							["squad_leader", "rifleman", "rifleman", "medic"], false)
						G.say("Outpost barracks: a fresh squad of 4 is ready", 1)
				o.set_meta("train_t", t)
			"depot":
				for ch in m.ground.occupants:
					if is_instance_valid(ch) and ch.team == 1 and ch.state == "alive" and ch.global_position.distance_to(p) < 25.0:
						if ch.armed and ch.spare.size() < 3:
							ch.spare = ["re_1", "re_2", "re_3"]
						if ch.medpens.size() < ch.pen_cap():
							ch.top_up_pens(true)
				for v in G.vehicles:
					if is_instance_valid(v) and v.team == 1 and v.global_position.distance_to(p) < 30.0:
						v.hp = minf(v.max_hp, v.hp + 15.0)
			"motor_pool":
				for v in G.vehicles:
					if is_instance_valid(v) and v.team == 1 and v.global_position.distance_to(p) < 35.0:
						v.hp = minf(v.max_hp, v.hp + 40.0)
			"extractor":
				r["ore"] = float(r.get("ore", 0.0)) + 1.2


# ------------------------------------------------------------------ meshes

static func _mat(c: Color, emit: float = 0.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.roughness = 0.7
	m.metallic = 0.25
	if emit > 0.0:
		m.emission_enabled = true
		m.emission = c
		m.emission_energy_multiplier = emit
	return m


static func _mesh(parent: Node3D, mesh: Mesh, pos: Vector3, mat: Material, scl: Vector3 = Vector3.ONE, rot: Vector3 = Vector3.ZERO) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.material_override = mat
	mi.position = pos
	mi.scale = scl
	mi.rotation = rot
	parent.add_child(mi)
	return mi


static func _cyl_mesh(r: float, h: float) -> CylinderMesh:
	var c := CylinderMesh.new()
	c.top_radius = r
	c.bottom_radius = r
	c.height = h
	c.radial_segments = 12
	return c


static func _cyl(parent: Node3D, r: float, h: float, pos: Vector3, mat: Material, rot: Vector3 = Vector3.ZERO) -> MeshInstance3D:
	return _mesh(parent, _cyl_mesh(r, h), pos, mat, Vector3.ONE, rot)
