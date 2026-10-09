extends RefCounted
## Ground installations built directly on a world's terrain (no separate station interior),
## so the open-ground navigation runs straight into and through them:
##   outlaw camp   a ring of containers, sandbags and scrap barricades with gaps for gates,
##                 gun nests covering the gaps, watchtowers, tents and fuel, and a fortified
##                 two-storey command house (garrisonable, with windows) as its core.
##   infected hive a creep-stained clearing walled by fleshy tendril ridges, spore towers
##                 that poison anything close, egg clusters that hatch infected, and a
##                 pulsing hive heart under a cage of ribs as its core.
## Destroy the core and the base falls (outpost.gd).

const OUTPOST := preload("res://scripts/campaign/outpost.gd")
const RUINS := preload("res://scripts/campaign/ruins.gd")
const MRAP := preload("res://scripts/campaign/mrap.gd")
const SURFACE := preload("res://scripts/campaign/surface.gd")


static func _gy(P: Dictionary, L: Dictionary, x: float, z: float) -> float:
	return SURFACE.GROUND_Y - 2.0 + SURFACE.height(P, L, x, z)


static func _mat(c: Color, emit: float = 0.0, rough: float = 0.85) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.roughness = rough
	if emit > 0.0:
		m.emission_enabled = true
		m.emission = c
		m.emission_energy_multiplier = emit
	return m


static func _body(m: Node, p: Vector3, yaw: float = 0.0) -> StaticBody3D:
	var b := StaticBody3D.new()
	b.collision_layer = G.LAYER_WORLD
	m.add_child(b)
	b.global_position = p
	b.rotation.y = yaw
	return b


static func _part(m: Node, part: String, team: int, name_: String, size: Vector3, hp: float, key: String, parts: Array, p: Vector3, yaw: float = 0.0) -> StaticBody3D:
	var o: StaticBody3D = OUTPOST.new()
	m.add_child(o)
	o.global_position = p
	o.rotation.y = yaw
	o.init(part, team, name_, size, hp, key, parts)
	if m.get("outposts") != null:
		m.outposts.append(o)
	return o


static func _mesh(parent: Node3D, mesh: Mesh, pos: Vector3, mat: Material, rot: Vector3 = Vector3.ZERO, scl: Vector3 = Vector3.ONE) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.material_override = mat
	mi.position = pos
	mi.rotation = rot
	mi.scale = scl
	parent.add_child(mi)
	return mi


static func _shape(b: StaticBody3D, size: Vector3, pos: Vector3, yaw: float = 0.0) -> void:
	var cs := CollisionShape3D.new()
	var bs := BoxShape3D.new()
	bs.size = size
	cs.shape = bs
	cs.position = pos
	cs.rotation.y = yaw
	b.add_child(cs)


static func _sphere(r: float, segs: int = 10) -> SphereMesh:
	var s := SphereMesh.new()
	s.radius = r
	s.height = r * 2.0
	s.radial_segments = segs
	s.rings = maxi(4, segs / 2)
	return s


static func _cyl(rt: float, rb: float, h: float, segs: int = 8) -> CylinderMesh:
	var c := CylinderMesh.new()
	c.top_radius = rt
	c.bottom_radius = rb
	c.height = h
	c.radial_segments = segs
	return c


# ================================================================== outlaw camp

static func outlaw_camp(m: Node, C: Vector3, key: String, L: Dictionary, P: Dictionary) -> void:
	var r := RandomNumberGenerator.new()
	r.seed = hash(key)
	var parts: Array = []
	var gy0 := _gy(P, L, C.x, C.z)
	var scrap := _mat(Color(0.42, 0.34, 0.26))
	var rust := _mat(Color(0.5, 0.3, 0.2))
	var dark := _mat(Color(0.13, 0.13, 0.13))
	var sand := _mat(Color(0.62, 0.55, 0.4), 0.0, 1.0)
	var tarp := _mat(Color(0.35, 0.4, 0.3), 0.0, 1.0)
	var cont_cols := [Color(0.55, 0.2, 0.15), Color(0.2, 0.35, 0.5), Color(0.6, 0.5, 0.2), Color(0.3, 0.4, 0.3)]
	# the core: a fortified command house, two storeys with firing windows
	var core := _part(m, "core", 3, "Outlaw Command", Vector3(16, 8, 14), 5200.0, key, parts, Vector3(C.x, gy0, C.z), r.randf() * TAU)
	RUINS._house(m, core, 16.0, 14.0, 10.0, scrap, rust, dark, r, P, L, SURFACE.GROUND_Y - 2.0)
	var mast := _mesh(core.visual, _cyl(0.12, 0.2, 12.0, 6), Vector3(5.5, 13.0, 4.5), dark)
	var flag := _mesh(core.visual, BoxMesh.new(), Vector3(6.4, 17.5, 4.5), _mat(Color(0.8, 0.2, 0.15), 0.4))
	flag.scale = Vector3(1.8, 1.1, 0.05)
	mast.name = "Mast"
	# the perimeter: containers, sandbags, scrap barricades, with three gaps (gates)
	var ring_r := r.randf_range(52.0, 64.0)
	var segs := 18
	var gates: Array = []
	var g0 := r.randi() % segs
	for k in 3:
		gates.append((g0 + k * segs / 3) % segs)
	for i in segs:
		if i in gates:
			continue
		var a := float(i) / segs * TAU + r.randf_range(-0.05, 0.05)
		var p := C + Vector3(cos(a), 0, sin(a)) * (ring_r + r.randf_range(-3.0, 3.0))
		p.y = _gy(P, L, p.x, p.z)
		var yaw := -a                                  # lie along the ring
		var b := _body(m, p, yaw)
		var kindr := r.randf()
		var inward := Vector3(-cos(a), 0, -sin(a))
		if kindr < 0.4:
			var cc: Color = cont_cols[r.randi() % cont_cols.size()]
			var cm := _mat(cc.darkened(r.randf() * 0.3))
			RUINS._block(b, Vector3(2.6, 2.6, 12.0), Vector3(0, 1.3, 0), cm, true)
			if r.randf() < 0.35:
				RUINS._block(b, Vector3(2.6, 2.6, 6.0), Vector3(0, 3.9, r.randf_range(-3, 3)), _mat((cont_cols[r.randi() % 4] as Color).darkened(0.2)), true)
			for s in [-3.5, 3.5]:
				m.ground_cover.append([b.to_global(Vector3(0, 0, s)) + inward * 2.2, false, -inward])
		elif kindr < 0.75:
			for k in 3:
				RUINS._block(b, Vector3(1.0, 1.1, 3.8), Vector3(0, 0.55, -4.0 + k * 4.0), sand, true)
			for s in [-4.0, 0.0, 4.0]:
				m.ground_cover.append([b.to_global(Vector3(0, 0, s)) + inward * 1.2, true, -inward])
				m.ground_cover.append([b.to_global(Vector3(0, 0, s)) - inward * 1.2, true, inward])
		else:
			for k in 3:
				var sh := RUINS._block(b, Vector3(0.3, r.randf_range(1.8, 2.6), 4.2), Vector3(0, 1.1, -4.0 + k * 4.0), scrap if k % 2 == 0 else rust, true)
				sh.rotation.z = r.randf_range(-0.12, 0.12)
			for s in [-4.0, 4.0]:
				m.ground_cover.append([b.to_global(Vector3(0, 0, s)) + inward * 1.0, false, -inward])
	# gun nests covering the gates
	for gi in gates:
		var a2 := float(gi) / segs * TAU
		var gp := C + Vector3(cos(a2), 0, sin(a2)) * (ring_r - 14.0)
		gp.y = _gy(P, L, gp.x, gp.z)
		var gun := _part(m, "gun", 3, "Outlaw gun nest", Vector3(5, 2.6, 5), 1100.0, key, parts, gp, -a2 + PI * 0.5)
		for k in 3:
			var ang := -PI * 0.5 + k * PI * 0.5
			var off := Vector3(sin(ang), 0, -cos(ang)) * 2.2
			var blk := RUINS._block(gun, Vector3(3.6, 1.1, 0.9), off + Vector3(0, 0.55, 0), sand, true)
			blk.rotation.y = ang
			(gun.get_child(gun.get_child_count() - 1) as Node3D).rotation.y = ang
		_mesh(gun.visual, _cyl(0.1, 0.1, 1.6, 6), Vector3(0, 0.8, 0), dark)
		_mesh(gun.visual, BoxMesh.new(), Vector3(0, 1.75, 0), dark, Vector3.ZERO, Vector3(0.5, 0.45, 1.2))
		_mesh(gun.visual, _cyl(0.07, 0.07, 1.8, 6), Vector3(0, 1.8, -1.4), dark, Vector3(PI * 0.5, 0, 0))
	# watchtowers
	for k in 2:
		var a3 := r.randf() * TAU
		var tp := C + Vector3(cos(a3), 0, sin(a3)) * (ring_r - 6.0)
		tp.y = _gy(P, L, tp.x, tp.z)
		var tb := _body(m, tp, r.randf() * TAU)
		for sx in [-1.4, 1.4]:
			for sz in [-1.4, 1.4]:
				RUINS._block(tb, Vector3(0.3, 8.0, 0.3), Vector3(sx, 4.0, sz), rust, true)
		RUINS._block(tb, Vector3(3.6, 0.25, 3.6), Vector3(0, 8.0, 0), scrap, false)
		RUINS._block(tb, Vector3(3.8, 1.0, 0.15), Vector3(0, 8.6, 1.8), scrap, false)
		RUINS._block(tb, Vector3(3.8, 1.0, 0.15), Vector3(0, 8.6, -1.8), scrap, false)
		var roof := RUINS._block(tb, Vector3(4.2, 0.15, 4.2), Vector3(0, 10.4, 0), tarp, false)
		roof.rotation.x = 0.12
	# the yard: tents, fuel tanks, crate stacks, burn barrels, a stripped wreck
	for i in 14:
		var a4 := r.randf() * TAU
		var d := r.randf_range(14.0, ring_r - 12.0)
		var pp := C + Vector3(cos(a4), 0, sin(a4)) * d
		pp.y = _gy(P, L, pp.x, pp.z)
		var yb := _body(m, pp, r.randf() * TAU)
		match i % 5:
			0:   # tent
				for sx in [-1, 1]:
					var t := RUINS._block(yb, Vector3(2.4, 0.08, 4.5), Vector3(sx * 0.9, 1.0, 0), tarp, false)
					t.rotation.z = sx * 0.85
				m.ground_cover.append([yb.to_global(Vector3(2.4, 0, 0)), true, Vector3.ZERO])
			1:   # fuel tank
				_mesh(yb, _cyl(1.2, 1.2, 5.0, 10), Vector3(0, 1.3, 0), rust, Vector3(0, 0, PI * 0.5))
				_shape(yb, Vector3(5.0, 2.4, 2.4), Vector3(0, 1.2, 0))
				m.ground_cover.append([yb.to_global(Vector3(0, 0, 2.2)), true, yb.global_basis * Vector3(0, 0, -1)])
			2:   # crates
				for q in 3:
					RUINS._block(yb, Vector3(1.4, 1.2, 1.4), Vector3(q * 1.5 - 1.5, 0.6, 0), _mat(Color(0.4, 0.33, 0.2)), true)
				RUINS._block(yb, Vector3(1.4, 1.2, 1.4), Vector3(-0.75, 1.8, 0), _mat(Color(0.36, 0.3, 0.18)), true)
				m.ground_cover.append([yb.to_global(Vector3(0, 0, 1.5)), false, yb.global_basis * Vector3(0, 0, -1)])
			3:   # burn barrel
				_mesh(yb, _cyl(0.4, 0.4, 1.0, 8), Vector3(0, 0.5, 0), dark)
				_mesh(yb, _sphere(0.35, 6), Vector3(0, 1.15, 0), _mat(Color(1.0, 0.5, 0.15), 4.0))
				if i < 9:
					var ol := OmniLight3D.new()
					ol.light_color = Color(1.0, 0.55, 0.25)
					ol.omni_range = 14.0
					ol.light_energy = 1.6
					ol.position = Vector3(0, 1.8, 0)
					yb.add_child(ol)
			_:   # a scrap pile
				for q in 4:
					var sp := RUINS._block(yb, Vector3(r.randf_range(1.0, 2.4), r.randf_range(0.3, 0.8), r.randf_range(1.0, 2.4)),
						Vector3(r.randf_range(-1, 1), 0.3 + q * 0.2, r.randf_range(-1, 1)), rust if q % 2 == 0 else scrap, q == 0)
					sp.rotation = Vector3(r.randf_range(-0.3, 0.3), r.randf() * TAU, r.randf_range(-0.3, 0.3))
				m.ground_cover.append([yb.to_global(Vector3(1.8, 0, 0)), true, yb.global_basis * Vector3(-1, 0, 0)])
	# who's home: a gang holding the camp, and 1-3 MRAP convoys (how many depends on how
	# lawless the region is), each with a squad of 8 walking escort. The first patrols round
	# the camp; the rest roam the whole zone.
	m.ground_spawns.append([C + Vector3(r.randf_range(-20, 20), 0, r.randf_range(-20, 20)), 3,
		["squad_leader", "rifleman", "rifleman", "heavy", "rifleman", "medic"]])
	var sysd: Dictionary = G.campaign.system() if G.campaign else {}
	var vol: int = 1 + (1 if sysd.get("pirates", false) else 0) + (1 if sysd.get("region", "") == "free" and r.randf() < 0.6 else 0)
	vol = clampi(vol, 1, 3)
	for k in vol:
		var mr: Node3D = MRAP.new()
		m.add_child(mr)
		if k == 0:
			mr.setup(3, C, ring_r + 70.0, L, P)
		else:
			mr.setup(3, Vector3(0, C.y, 0), SURFACE.AREA * 0.75, L, P)
			mr.position = C + Vector3(r.randf_range(-1, 1), 0, r.randf_range(-1, 1)).normalized() * (ring_r + 30.0)
			mr._ground_y()
			mr.goal = mr.position
		mr.pace = 4.2
		m.ground_spawns.append([mr.position + Vector3(8, 0, 8), 3,
			["squad_leader", "rifleman", "rifleman", "heavy", "rifleman", "medic", "rifleman", "breacher"], {"escort": mr}])


# ================================================================== infected hive

static func hive(m: Node, C: Vector3, key: String, L: Dictionary, P: Dictionary) -> void:
	var r := RandomNumberGenerator.new()
	r.seed = hash(key)
	var parts: Array = []
	var gy0 := _gy(P, L, C.x, C.z)
	var flesh := _mat(Color(0.28, 0.12, 0.26), 0.15, 0.6)
	var flesh2 := _mat(Color(0.38, 0.16, 0.3), 0.2, 0.55)
	var bone := _mat(Color(0.62, 0.55, 0.5), 0.0, 0.7)
	var glow := _mat(Color(0.85, 0.3, 1.0), 3.5)
	var vein := _mat(Color(0.6, 0.2, 0.75), 1.4)
	var creep := _mat(Color(0.16, 0.06, 0.15), 0.25, 0.9)
	# the creep: a stain on the ground with glowing veins running out from the heart
	var deco := Node3D.new()
	m.add_child(deco)
	deco.global_position = Vector3(C.x, gy0, C.z)
	_mesh(deco, _cyl(95.0, 98.0, 0.3, 40), Vector3(0, 0.12, 0), creep)
	for i in 14:
		var a := float(i) / 14.0 * TAU + r.randf_range(-0.2, 0.2)
		var ln := r.randf_range(40.0, 90.0)
		var vb := _mesh(deco, BoxMesh.new(), Vector3(cos(a), 0, sin(a)) * ln * 0.5 + Vector3(0, 0.32, 0), vein, Vector3(0, -a, 0), Vector3(ln, 0.12, 0.35))
		vb.name = "Vein"
	# the warren: a domed chamber of fleshy walls you can get inside (three mouths), the
	# heart in its middle, brood sacs along the walls that birth replacement infected,
	# and low ridges inside to fight over. The dome peels away in the cutaway (X).
	var RW := 20.0
	var wall := _body(m, Vector3(C.x, gy0, C.z))
	var mouths: Array = []
	var m0 := r.randi() % 30
	for k in 3:
		mouths.append((m0 + k * 10) % 30)
		mouths.append((m0 + k * 10 + 1) % 30)
	for i in 30:
		if i in mouths:
			continue
		var a1 := float(i) / 30.0 * TAU
		var wp := Vector3(cos(a1), 0, sin(a1)) * RW
		var wy := _gy(P, L, C.x + wp.x, C.z + wp.z) - gy0
		var seg := _mesh(wall, BoxMesh.new(), wp + Vector3(0, wy + 3.2, 0), flesh if i % 2 == 0 else flesh2,
			Vector3(r.randf_range(-0.08, 0.08), -a1 + PI * 0.5, 0), Vector3(4.6, 6.8, 1.6))
		seg.name = "WarrenWall"
		_shape(wall, Vector3(4.6, 6.8, 1.6), wp + Vector3(0, wy + 3.4, 0), -a1 + PI * 0.5)
		if i % 3 == 0:          # bone struts up the outside
			_mesh(wall, _cyl(0.3, 0.5, 8.0, 6), wp * 1.06 + Vector3(0, wy + 4.0, 0), bone, Vector3(0, 0, 0.0))
		var inw := -wp.normalized()
		if i % 2 == 1:
			m.ground_cover.append([wall.to_global(wp + inw * 1.6), false, -inw])
	for mi in mouths:
		if not ((mi + 1) % 30 in mouths):
			continue
		var am := (float(mi) + 0.5) / 30.0 * TAU
		var mp := Vector3(cos(am), 0, sin(am)) * RW
		_mesh(wall, _cyl(0.0, 0.6, 3.0, 5), mp + Vector3(0, 6.6, 0), bone, Vector3(PI, 0, 0))     # fangs over the mouth
	var dome := _mesh(wall, _sphere(RW + 1.5, 24), Vector3(0, 5.5, 0), flesh2, Vector3.ZERO, Vector3(1.0, 0.42, 1.0))
	dome.name = "WarrenDome"
	if m.get("roofs") != null:
		m.roofs.append([dome, 1])
	# inner ridges: cover inside the chamber
	for k in 4:
		var ak := float(k) / 4.0 * TAU + r.randf_range(0.2, 0.5)
		for q in 3:
			var rp := Vector3(cos(ak), 0, sin(ak)) * (10.0 + q * 2.4)
			_mesh(wall, _sphere(1.3, 8), rp + Vector3(0, 0.6, 0), flesh, Vector3(0, -ak, 0), Vector3(1.3, 0.75, 1.0))
			_shape(wall, Vector3(2.2, 1.2, 2.2), rp + Vector3(0, 0.6, 0), -ak)
		var rpc := Vector3(cos(ak), 0, sin(ak)) * 12.4
		var side := Vector3(-sin(ak), 0, cos(ak)) * 1.8
		m.ground_cover.append([wall.to_global(rpc + side), true, -side.normalized()])
		m.ground_cover.append([wall.to_global(rpc - side), true, side.normalized()])
	# the heart (the core)
	var core := _part(m, "core", 4, "Hive Heart", Vector3(12, 9, 12), 7000.0, key, parts, Vector3(C.x, gy0, C.z))
	_mesh(core.visual, _sphere(5.5, 16), Vector3(0, 0.4, 0), flesh, Vector3.ZERO, Vector3(1.0, 0.5, 1.0))
	_shape(core, Vector3(7.5, 3.0, 7.5), Vector3(0, 1.5, 0))
	var heart := _mesh(core.visual, _sphere(2.4, 14), Vector3(0, 4.2, 0), glow)
	core.set_heart(heart)
	for k in 6:
		var a5 := float(k) / 6.0 * TAU
		for s in 4:
			var t := float(s) / 3.0
			var ang := t * PI * 0.55
			var rad := 6.0 - sin(ang) * 3.5
			var p := Vector3(cos(a5) * rad, sin(ang) * 6.5 + 0.8, sin(a5) * rad)
			var rib := _mesh(core.visual, _cyl(0.22, 0.35, 2.4, 6), p, bone)
			rib.look_at(core.visual.to_global(Vector3(0, 7.5, 0)), Vector3.UP)
			rib.rotate_object_local(Vector3.RIGHT, PI * 0.5)
	var hl := OmniLight3D.new()
	hl.light_color = Color(0.85, 0.3, 1.0)
	hl.omni_range = 30.0
	hl.light_energy = 2.5
	hl.position = Vector3(0, 5.0, 0)
	core.add_child(hl)
	# brood sacs on the inside wall: they birth replacement infected
	for k in 2:
		var ab := r.randf() * TAU
		var bp := C + Vector3(cos(ab), 0, sin(ab)) * (RW - 3.5)
		bp.y = _gy(P, L, bp.x, bp.z)
		var brood := _part(m, "brood", 4, "Brood sac", Vector3(4, 5, 4), 1200.0, key, parts, bp, -ab)
		_mesh(brood.visual, _cyl(0.5, 0.9, 3.0, 7), Vector3(0, 1.5, 0), flesh)
		var sac := _mesh(brood.visual, _sphere(1.8, 12), Vector3(0, 3.6, 0), _mat(Color(0.8, 0.4, 0.75), 1.6, 0.25), Vector3.ZERO, Vector3(1.0, 1.25, 1.0))
		brood.set_heart(sac)
		_shape(brood, Vector3(2.0, 3.0, 2.0), Vector3(0, 1.5, 0))
	# tendril ridges: low fleshy walls in broken arcs (cover, with gaps to push through)
	for w in 6:
		var a0 := float(w) / 6.0 * TAU + r.randf_range(-0.2, 0.2)
		var rr := r.randf_range(42.0, 62.0)
		var wb := _body(m, Vector3(C.x, gy0, C.z))
		for s2 in 7:
			var a6 := a0 + (s2 - 3) * 0.06
			var lp := Vector3(cos(a6), 0, sin(a6)) * rr
			var wy := _gy(P, L, C.x + lp.x, C.z + lp.z) - gy0
			var hgt := r.randf_range(1.2, 2.2)
			_mesh(wb, _sphere(1.6, 8), lp + Vector3(0, wy + hgt * 0.4, 0), flesh2 if s2 % 2 == 0 else flesh, Vector3(0, -a6, 0), Vector3(1.3, hgt / 1.6 * 0.8, 1.0))
			_shape(wb, Vector3(2.6, hgt, 2.6), lp + Vector3(0, wy + hgt * 0.5, 0), -a6)
			if s2 % 3 == 1:
				var inw := -lp.normalized()
				m.ground_cover.append([wb.to_global(lp + inw * 2.0), true, -inw])
				m.ground_cover.append([wb.to_global(lp - inw * 2.0), true, inw])
		if r.randf() < 0.6:     # a thorn growing out of the ridge
			var tp := Vector3(cos(a0), 0, sin(a0)) * rr
			_mesh(wb, _cyl(0.0, 0.7, 6.0, 6), tp + Vector3(0, 3.0, 0), bone, Vector3(r.randf_range(-0.3, 0.3), 0, r.randf_range(-0.3, 0.3)))
	# spore towers
	for i in 3:
		var a7 := float(i) / 3.0 * TAU + r.randf_range(-0.3, 0.3)
		var sp := C + Vector3(cos(a7), 0, sin(a7)) * r.randf_range(24.0, 34.0)
		sp.y = _gy(P, L, sp.x, sp.z)
		var tw := _part(m, "spore", 4, "Spore tower", Vector3(4, 16, 4), 1500.0, key, parts, sp, r.randf() * TAU)
		var y := 0.0
		var off := Vector3.ZERO
		for s3 in 5:
			var h := 3.4 - s3 * 0.25
			var rb := 1.6 - s3 * 0.28
			off += Vector3(r.randf_range(-0.35, 0.35), 0, r.randf_range(-0.35, 0.35))
			_mesh(tw.visual, _cyl(rb - 0.25, rb, h, 7), off + Vector3(0, y + h * 0.5, 0), flesh if s3 % 2 == 0 else flesh2,
				Vector3(r.randf_range(-0.12, 0.12), r.randf() * TAU, r.randf_range(-0.12, 0.12)))
			y += h * 0.92
		_mesh(tw.visual, _sphere(1.5, 10), off + Vector3(0, y + 1.0, 0), glow, Vector3.ZERO, Vector3(1.0, 1.3, 1.0))
		for k2 in 4:
			var aa := k2 * PI * 0.5
			_mesh(tw.visual, _cyl(0.0, 0.25, 2.2, 5), off + Vector3(cos(aa) * 1.2, y + 0.4, sin(aa) * 1.2), bone, Vector3(cos(aa) * 0.9, 0, -sin(aa) * 0.9))
		_shape(tw, Vector3(2.6, y, 2.6), Vector3(0, y * 0.5, 0))
	# egg clusters
	for i in 3:
		var a8 := float(i) / 3.0 * TAU + PI / 3.0 + r.randf_range(-0.3, 0.3)
		var np := C + Vector3(cos(a8), 0, sin(a8)) * r.randf_range(30.0, 40.0)
		np.y = _gy(P, L, np.x, np.z)
		var nest := _part(m, "nest", 4, "Egg cluster", Vector3(6, 3, 6), 900.0, key, parts, np, r.randf() * TAU)
		_mesh(nest.visual, _sphere(3.0, 12), Vector3(0, 0.3, 0), flesh, Vector3.ZERO, Vector3(1.0, 0.35, 1.0))
		for k3 in 7:
			var ea := k3 * TAU / 7.0
			var er := 1.4 if k3 > 0 else 0.0
			_mesh(nest.visual, _sphere(0.7, 8), Vector3(cos(ea) * er, 1.4, sin(ea) * er), _mat(Color(0.75, 0.45, 0.6), 1.2, 0.3),
				Vector3(r.randf_range(-0.3, 0.3), 0, r.randf_range(-0.3, 0.3)), Vector3(0.85, 1.3, 0.85))
		_shape(nest, Vector3(5.0, 1.8, 5.0), Vector3(0, 0.9, 0))
		m.ground_cover.append([nest.to_global(Vector3(0, 0, 3.6)), true, nest.global_basis * Vector3(0, 0, -1)])
	# pustules and spikes scattered over the creep
	for i in 26:
		var a9 := r.randf() * TAU
		var dd := r.randf_range(14.0, 85.0)
		var lp2 := Vector3(cos(a9), 0, sin(a9)) * dd
		var wy2 := _gy(P, L, C.x + lp2.x, C.z + lp2.z) - gy0
		if i % 2 == 0:
			_mesh(deco, _sphere(r.randf_range(0.4, 0.9), 7), lp2 + Vector3(0, wy2 + 0.3, 0), glow)
		else:
			_mesh(deco, _cyl(0.0, r.randf_range(0.3, 0.6), r.randf_range(2.0, 4.5), 5), lp2 + Vector3(0, wy2 + 1.2, 0), bone,
				Vector3(r.randf_range(-0.4, 0.4), 0, r.randf_range(-0.4, 0.4)))
	# the swarm
	for k in 3:
		m.ground_spawns.append([C + Vector3(r.randf_range(-40, 40), 0, r.randf_range(-40, 40)), 4, ["x", "x", "x", "x", "x"]])
	m.ground_vehicles.append([C + Vector3(r.randf_range(-70, 70), 0, r.randf_range(-70, 70)), ["tank", "mrap_ai", "mech"][r.randi() % 3], 4, 1])


# ================================================================== the gravemind

## A hive that's gorged itself on an abandoned city grows a gravemind in its heart: a vast
## mound with a glowing maw and tendrils coiled through the ruins. It lashes out at anything
## near and births infected ships that leave to seed new hives (infection.gd).
static func gravemind(m: Node, C: Vector3, hive_key: String, L: Dictionary, P: Dictionary) -> Node3D:
	var r := RandomNumberGenerator.new()
	r.seed = hash(hive_key + "gm")
	var gy0 := _gy(P, L, C.x, C.z)
	var flesh := _mat(Color(0.3, 0.1, 0.25), 0.2, 0.55)
	var flesh2 := _mat(Color(0.42, 0.15, 0.32), 0.3, 0.5)
	var bone := _mat(Color(0.66, 0.6, 0.52), 0.0, 0.7)
	var glow := _mat(Color(0.95, 0.35, 1.0), 4.0)
	var parts: Array = []
	var gm := _part(m, "gravemind", 4, "GRAVEMIND", Vector3(34, 22, 34), 15000.0, "gm_" + hive_key, parts, Vector3(C.x, gy0, C.z))
	gm.set_meta("gm_of", hive_key)
	_mesh(gm.visual, _sphere(17.0, 20), Vector3(0, 1.0, 0), flesh, Vector3.ZERO, Vector3(1.0, 0.6, 1.0))
	_mesh(gm.visual, _sphere(9.0, 16), Vector3(2.0, 10.0, -1.0), flesh2, Vector3.ZERO, Vector3(1.0, 0.8, 0.9))
	var maw := TorusMesh.new()
	maw.inner_radius = 2.6
	maw.outer_radius = 4.6
	_mesh(gm.visual, maw, Vector3(2.0, 12.5, -7.5), bone, Vector3(PI * 0.5 - 0.3, 0, 0))
	var core_glow := _mesh(gm.visual, _sphere(2.8, 12), Vector3(2.0, 12.3, -6.8), glow)
	gm.set_heart(core_glow)
	for k in 8:                                           # teeth round the maw
		var a := float(k) / 8.0 * TAU
		_mesh(gm.visual, _cyl(0.0, 0.45, 1.8, 5), Vector3(2.0 + cos(a) * 3.4, 12.5 + sin(a) * 3.0, -7.9), bone, Vector3(PI * 0.5, 0, a))
	# tendrils coiling out through the ruins
	for t in 7:
		var a0 := float(t) / 7.0 * TAU + r.randf_range(-0.2, 0.2)
		var p := Vector3(cos(a0), 0, sin(a0)) * 14.0 + Vector3(0, 4.0, 0)
		var dir := Vector3(cos(a0), 0.35, sin(a0))
		var rad := 2.2
		for s in 9:
			var nxt := p + dir * 5.0
			var seg := _mesh(gm.visual, _cyl(rad * 0.8, rad, 5.6, 7), (p + nxt) * 0.5, flesh if s % 2 == 0 else flesh2)
			seg.look_at(gm.visual.to_global(nxt), Vector3.UP if absf(dir.y) < 0.95 else Vector3.RIGHT)
			seg.rotate_object_local(Vector3.RIGHT, PI * 0.5)
			p = nxt
			dir = (dir + Vector3(r.randf_range(-0.4, 0.4), -0.18, r.randf_range(-0.4, 0.4))).normalized()
			rad *= 0.86
		_mesh(gm.visual, _sphere(0.9, 8), p, glow)
	_shape(gm, Vector3(22.0, 9.0, 22.0), Vector3(0, 4.5, 0))
	var gl := OmniLight3D.new()
	gl.light_color = Color(0.9, 0.3, 1.0)
	gl.omni_range = 70.0
	gl.light_energy = 3.0
	gl.position = Vector3(0, 14.0, -6.0)
	gm.add_child(gl)
	var lab := Label3D.new()
	lab.text = "GRAVEMIND"
	lab.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lab.font_size = 64
	lab.pixel_size = 0.25
	lab.modulate = Color(0.9, 0.5, 1.0)
	lab.position = Vector3(0, 30.0, 0)
	gm.add_child(lab)
	return gm


# ================================================================== an infested city

## An abandoned city the infection has taken: creep spreading over the streets, growths
## and pustules on the buildings, a spore tower or two, and brood sacs in the ruins that
## keep birthing infected to replace the fallen.
static func infest_city(m: Node, center: Vector3, radius: float, key: String, L: Dictionary, P: Dictionary) -> void:
	var r := RandomNumberGenerator.new()
	r.seed = hash(key + "inf")
	var flesh := _mat(Color(0.3, 0.1, 0.26), 0.2, 0.6)
	var flesh2 := _mat(Color(0.44, 0.15, 0.36), 0.3, 0.55)
	var bone := _mat(Color(0.66, 0.6, 0.52), 0.0, 0.7)
	var glow := _mat(Color(0.95, 0.35, 1.0), 3.5)
	var creep := _mat(Color(0.16, 0.06, 0.15), 0.25, 0.9)
	var parts: Array = []
	var deco := Node3D.new()
	m.add_child(deco)
	var pts: Array = []
	for i in 22:
		var a := r.randf() * TAU
		var d := sqrt(r.randf()) * radius * 0.85
		var p := center + Vector3(cos(a), 0, sin(a)) * d
		p.y = _gy(P, L, p.x, p.z)
		pts.append(p)
	# creep pools over the streets
	for i in 14:
		var p: Vector3 = pts[i]
		_mesh(deco, _cyl(r.randf_range(8.0, 22.0), r.randf_range(9.0, 24.0), 0.25, 18), p + Vector3(0, 0.1, 0), creep)
		for k in 4:
			var pa := r.randf() * TAU
			_mesh(deco, _sphere(r.randf_range(0.3, 0.8), 7), p + Vector3(cos(pa), 0, sin(pa)) * r.randf_range(2.0, 12.0) + Vector3(0, 0.3, 0),
				glow if k % 2 == 0 else flesh2)
	# fleshy growths climbing the ruins (where there's something to climb)
	for i in 40:
		var a2 := r.randf() * TAU
		var p2 := center + Vector3(cos(a2), 0, sin(a2)) * r.randf_range(10.0, radius * 0.9)
		var top := G.ray(Vector3(p2.x, SURFACE.GROUND_Y + 200.0, p2.z), Vector3(p2.x, SURFACE.GROUND_Y - 200.0, p2.z), [], G.LAYER_WORLD)
		var gy := _gy(P, L, p2.x, p2.z)
		var hy: float = (top.position as Vector3).y if not top.is_empty() else gy
		if hy - gy < 1.5:
			continue                                   # open ground: leave it
		_mesh(deco, _sphere(r.randf_range(0.8, 1.8), 8), Vector3(p2.x, hy, p2.z), flesh if i % 2 == 0 else flesh2, Vector3.ZERO,
			Vector3(1.0, r.randf_range(0.5, 1.1), 1.0))
		if i % 3 == 0:
			_mesh(deco, _cyl(0.0, 0.35, r.randf_range(1.5, 3.0), 5), Vector3(p2.x, hy + 1.0, p2.z), bone,
				Vector3(r.randf_range(-0.4, 0.4), 0, r.randf_range(-0.4, 0.4)))
	# brood sacs and a spore tower in the ruins
	for i in 3:
		var bp: Vector3 = pts[14 + i]
		var brood := _part(m, "brood", 4, "Brood sac", Vector3(4, 5, 4), 1200.0, key, parts, bp, r.randf() * TAU)
		_mesh(brood.visual, _cyl(0.5, 0.9, 3.0, 7), Vector3(0, 1.5, 0), flesh)
		var sac := _mesh(brood.visual, _sphere(1.8, 12), Vector3(0, 3.6, 0), _mat(Color(0.8, 0.4, 0.75), 1.6, 0.25), Vector3.ZERO, Vector3(1.0, 1.25, 1.0))
		brood.set_heart(sac)
		_shape(brood, Vector3(2.0, 3.0, 2.0), Vector3(0, 1.5, 0))
	var sp: Vector3 = pts[18]
	var tw := _part(m, "spore", 4, "Spore tower", Vector3(4, 14, 4), 1500.0, key, parts, sp, 0.0)
	var y := 0.0
	for s3 in 4:
		var h := 3.2 - s3 * 0.3
		_mesh(tw.visual, _cyl(1.2 - s3 * 0.28, 1.5 - s3 * 0.28, h, 7), Vector3(0, y + h * 0.5, 0), flesh if s3 % 2 == 0 else flesh2,
			Vector3(r.randf_range(-0.12, 0.12), 0, r.randf_range(-0.12, 0.12)))
		y += h * 0.92
	_mesh(tw.visual, _sphere(1.4, 10), Vector3(0, y + 1.0, 0), glow, Vector3.ZERO, Vector3(1.0, 1.3, 1.0))
	_shape(tw, Vector3(2.4, y, 2.4), Vector3(0, y * 0.5, 0))
