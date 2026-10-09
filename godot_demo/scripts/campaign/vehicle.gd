extends Node3D
## Ground vehicles and mechs for the Vanguard and the Ascendancy (and the infection's
## overgrown copies). They drive the open-ground navigation, pick their own targets and
## take orders from the commander like ships do (select, right-click move / attack).
##   tank      main gun (anti-armour, anti-structure) + coaxial gun
##   ifv       carries a squad of 6; autocannon with a little anti-armour bite
##   mrap_ai / mrap_aa / mrap_av   gatling vs infantry / flak vs aircraft / missiles vs armour
##   mech      walker: twin guns + rockets; Vanguard after the Cyclops, Ascendancy after the Goliath
##   mortar    self-propelled mortar: indirect area fire, never precise, 80-650 m
## Vanguard designs: heavy, angular, tracked or wheeled (Scorpion / Nova in spirit).
## Ascendancy designs: sleek hover hulls with red light strips (AW / BO3 / IW in spirit).

const SPECS := {
	"tank": {"hp": 2600.0, "armor": 3.0, "speed": 9.0, "label": "Tank", "range": 420.0},
	"ifv": {"hp": 1500.0, "armor": 2.0, "speed": 12.0, "label": "IFV", "range": 320.0},
	"mrap_ai": {"hp": 900.0, "armor": 1.5, "speed": 15.0, "label": "MRAP (anti-infantry)", "range": 260.0},
	"mrap_aa": {"hp": 900.0, "armor": 1.5, "speed": 15.0, "label": "MRAP (anti-air)", "range": 900.0},
	"mrap_av": {"hp": 900.0, "armor": 1.5, "speed": 15.0, "label": "MRAP (anti-vehicle)", "range": 380.0},
	"mech": {"hp": 1300.0, "armor": 2.0, "speed": 6.5, "label": "Mech", "range": 300.0},
	"mortar": {"hp": 1000.0, "armor": 1.5, "speed": 8.0, "label": "Mortar carrier", "range": 650.0},
}
## [damage, cooldown, penetration, against: "inf" / "veh" / "air" / "area"]
const GUNS := {
	"tank": [[260.0, 4.0, 3.0, "veh"], [9.0, 0.15, 0.5, "inf"]],
	"ifv": [[40.0, 0.6, 1.5, "veh"], [9.0, 0.6, 1.0, "inf"]],
	"mrap_ai": [[9.0, 0.09, 0.5, "inf"]],
	"mrap_aa": [[30.0, 0.25, 1.0, "air"]],
	"mrap_av": [[220.0, 5.0, 3.0, "veh"]],
	"mech": [[14.0, 0.18, 1.0, "inf"], [120.0, 3.5, 2.0, "veh"]],
	"mortar": [[180.0, 6.5, 2.0, "area"]],
}

var kind := "tank"
var team := 1
var faction := 1
var hp := 1000.0
var max_hp := 1000.0
var display_name := ""
var ground: Node3D
var goal := Vector3.INF            # ground-local
var path := PackedVector3Array()
var path_i := 0
var attack_target: Node = null
var passengers := 0                # IFV: troops aboard
var selected := false
var is_vehicle := true
var destroyed := false
var _cool: Array = []
var _turret: Node3D
var _legs: Array = []
var _t := 0.0
var _sel: MeshInstance3D
var _think := 0.0
var driver: Node = null            # the player, when they've taken the controls
var drive_vel := 0.0
var aim_point := Vector3.INF
var cargo_of: Node = null          # the supply ship carrying this vehicle in its front bay


func setup(kind_: String, team_: int, faction_: int, gnd: Node3D, local_p: Vector3) -> void:
	kind = kind_
	team = team_
	faction = faction_
	ground = gnd
	max_hp = SPECS[kind]["hp"] * (1.0 + G.tech_bonus(team, "vehicle_hp"))
	hp = max_hp
	display_name = "%s %s" % [G.team_short(team), SPECS[kind]["label"]]
	for g in GUNS[kind]:
		_cool.append(randf())
	_build()
	gnd.add_child(self)
	position = local_p
	_settle()
	var pk := Area3D.new()
	pk.collision_layer = G.LAYER_PICK
	pk.monitoring = false
	var cs := CollisionShape3D.new()
	var sp := SphereShape3D.new()
	sp.radius = 4.5
	cs.shape = sp
	cs.position.y = 2.0
	pk.add_child(cs)
	pk.set_meta("unit", self)
	add_child(pk)
	_sel = MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = 4.6
	tm.outer_radius = 5.0
	_sel.mesh = tm
	_sel.material_override = G._mat(G.team_color(team), 1.5)
	_sel.visible = false
	add_child(_sel)
	G.vehicles.append(self)


func set_selected(on: bool) -> void:
	selected = on
	_sel.visible = on


# ------------------------------------------------------------------ models

func _mat(c: Color, emit: float = 0.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.metallic = 0.35
	m.roughness = 0.55
	if emit > 0.0:
		m.emission_enabled = true
		m.emission = c
		m.emission_energy_multiplier = emit
	return m


func _box(p: Node3D, s: Vector3, pos: Vector3, m: Material, rot: Vector3 = Vector3.ZERO) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = s
	mi.mesh = bm
	mi.material_override = m
	mi.position = pos
	mi.rotation = rot
	p.add_child(mi)
	return mi


func _cyl(p: Node3D, r: float, h: float, pos: Vector3, m: Material, rot: Vector3 = Vector3(PI * 0.5, 0, 0)) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = r
	cm.bottom_radius = r
	cm.height = h
	cm.radial_segments = 10
	mi.mesh = cm
	mi.material_override = m
	mi.position = pos
	mi.rotation = rot
	p.add_child(mi)
	return mi


func _build() -> void:
	var asc := faction == 2
	var infected := team == 4
	var body := _mat(Color(0.36, 0.4, 0.33) if not asc else Color(0.78, 0.8, 0.84))
	if infected:
		body = _mat(Color(0.3, 0.18, 0.32))
	var dark := _mat(Color(0.12, 0.12, 0.13))
	var glow := _mat(Color(1.0, 0.2, 0.25) if asc else Color(0.4, 0.8, 1.0), 2.5)
	if infected:
		glow = _mat(Color(0.8, 0.3, 1.0), 2.5)
	var root := Node3D.new()
	add_child(root)
	_turret = Node3D.new()
	match kind:
		"tank":
			if asc:
				_box(root, Vector3(4.6, 1.2, 8.0), Vector3(0, 1.6, 0), body)                # a flat wedge hull...
				_box(root, Vector3(4.0, 0.6, 2.2), Vector3(0, 1.4, -4.4), body, Vector3(0.3, 0, 0))
				for sx in [-1, 1]:
					_box(root, Vector3(1.2, 0.5, 6.6), Vector3(sx * 2.2, 0.8, 0), dark)       # ...riding on hover skirts
					_box(root, Vector3(0.1, 0.1, 6.0), Vector3(sx * 2.35, 1.95, 0), glow)
				_turret.position = Vector3(0, 2.4, 0.4)
				_box(_turret, Vector3(3.0, 0.9, 3.6), Vector3.ZERO, body)
				for sx in [-0.3, 0.3]:
					_box(_turret, Vector3(0.22, 0.22, 5.5), Vector3(sx, 0.1, -4.2), dark)      # twin rail barrels
				_box(_turret, Vector3(2.6, 0.08, 0.1), Vector3(0, 0.46, -1.7), glow)
			else:
				_box(root, Vector3(4.2, 1.5, 7.4), Vector3(0, 1.6, 0), body)                # a slab hull...
				_box(root, Vector3(3.6, 0.8, 1.6), Vector3(0, 1.3, -4.2), body, Vector3(-0.35, 0, 0))
				for sx in [-1, 1]:
					for sz in [-1, 1]:
						_box(root, Vector3(1.4, 1.5, 3.0), Vector3(sx * 2.5, 0.9, sz * 2.3), dark)   # ...on four track pods
				_turret.position = Vector3(0, 2.75, 0.6)
				_box(_turret, Vector3(3.0, 1.1, 3.8), Vector3.ZERO, body)
				_cyl(_turret, 0.28, 6.5, Vector3(0, 0.1, -5.0), dark)                       # long main gun
				_box(_turret, Vector3(0.6, 0.6, 1.0), Vector3(0, 0.1, -8.2), dark)
		"ifv":
			if asc:
				_box(root, Vector3(4.0, 2.0, 7.2), Vector3(0, 1.9, 0), body)
				_box(root, Vector3(3.6, 0.8, 2.0), Vector3(0, 1.6, -4.0), body, Vector3(0.35, 0, 0))
				for sx in [-1, 1]:
					_box(root, Vector3(1.0, 0.5, 6.4), Vector3(sx * 2.0, 0.8, 0), dark)
					_box(root, Vector3(0.1, 0.1, 6.0), Vector3(sx * 2.05, 2.6, 0), glow)
			else:
				_box(root, Vector3(3.6, 2.2, 7.6), Vector3(0, 2.0, 0), body)
				for k in 4:
					for sx in [-1, 1]:
						_cyl(root, 0.75, 0.6, Vector3(sx * 1.95, 0.8, -2.7 + k * 1.8), dark, Vector3(0, 0, PI * 0.5))
			_turret.position = Vector3(0, 3.2, -0.6)
			_box(_turret, Vector3(1.8, 0.7, 2.0), Vector3.ZERO, body)
			_cyl(_turret, 0.12, 2.8, Vector3(0, 0.1, -2.2), dark)
		"mrap_ai", "mrap_aa", "mrap_av":
			_box(root, Vector3(3.0, 2.4, 6.2), Vector3(0, 2.1, 0), body if not asc else _mat(Color(0.7, 0.72, 0.76)))
			_box(root, Vector3(2.8, 1.3, 2.0), Vector3(0, 1.6, -3.6), body)
			_box(root, Vector3(2.6, 0.8, 1.0), Vector3(0, 2.9, -2.5), _mat(Color(0.2, 0.3, 0.4)))   # windscreen
			for k in 2:
				for sx in [-1, 1]:
					_cyl(root, 0.8, 0.55, Vector3(sx * 1.6, 0.8, -2.4 + k * 4.0), dark, Vector3(0, 0, PI * 0.5))
			_turret.position = Vector3(0, 3.6, 0.4)
			match kind:
				"mrap_ai":
					_box(_turret, Vector3(0.8, 0.6, 1.4), Vector3.ZERO, dark)
					_cyl(_turret, 0.1, 1.8, Vector3(0, 0.05, -1.4), dark)
				"mrap_aa":
					_box(_turret, Vector3(1.6, 0.8, 1.4), Vector3.ZERO, body)
					for sx in [-0.35, 0.35]:
						_cyl(_turret, 0.1, 2.4, Vector3(sx, 0.7, -0.9), dark, Vector3(PI * 0.5 - 0.6, 0, 0))
				"mrap_av":
					_box(_turret, Vector3(1.8, 1.0, 1.6), Vector3(0, 0.2, 0), body)
					for k in 4:
						_cyl(_turret, 0.16, 0.3, Vector3(-0.45 + (k % 2) * 0.9, 0.05 + (k / 2) * 0.45, -0.82), glow)
		"mech":
			if asc:
				# Goliath-style: a slim armoured exoframe, shoulder rocket pods
				_box(root, Vector3(1.6, 2.0, 1.3), Vector3(0, 3.6, 0), body)
				_box(root, Vector3(0.8, 0.6, 0.8), Vector3(0, 4.8, -0.1), _mat(Color(0.15, 0.15, 0.18)))
				for sx in [-1, 1]:
					_box(root, Vector3(0.5, 1.6, 0.5), Vector3(sx * 1.1, 3.4, -0.2), body)
					_box(root, Vector3(0.7, 0.7, 1.0), Vector3(sx * 0.9, 4.7, 0.2), dark)
					_legs.append(_box(root, Vector3(0.55, 2.6, 0.6), Vector3(sx * 0.55, 1.4, 0), dark))
			else:
				# Cyclops-style: a squat walking cockpit with heavy arms, one a gun, one a claw
				_box(root, Vector3(2.6, 2.4, 2.2), Vector3(0, 3.8, 0), body)
				_box(root, Vector3(1.4, 0.5, 0.2), Vector3(0, 4.3, -1.15), glow)
				for sx in [-1, 1]:
					_box(root, Vector3(0.9, 2.4, 0.9), Vector3(sx * 1.9, 3.4, -0.4), body)
					_legs.append(_box(root, Vector3(0.9, 2.8, 1.0), Vector3(sx * 0.8, 1.4, 0), dark))
			_turret.position = Vector3(0, 3.6, -0.6)
			_cyl(_turret, 0.12, 1.6, Vector3(1.4, -0.4, -0.8), dark)
		"mortar":
			_box(root, Vector3(3.6, 1.6, 6.4), Vector3(0, 1.5, 0), body)
			if asc:
				for sx in [-1, 1]:
					_box(root, Vector3(1.0, 0.5, 6.0), Vector3(sx * 1.8, 0.7, 0), dark)
			else:
				for sx in [-1, 1]:
					_box(root, Vector3(1.0, 1.2, 6.2), Vector3(sx * 2.1, 0.8, 0), dark)
			_turret.position = Vector3(0, 2.4, 1.2)
			_box(_turret, Vector3(2.2, 0.6, 2.2), Vector3.ZERO, body)
			_cyl(_turret, 0.32, 3.2, Vector3(0, 1.4, -0.4), dark, Vector3(PI * 0.5 - 1.05, 0, 0))
	root.add_child(_turret)
	if infected:
		_overgrow(root)
	if kind == "mech":
		root.scale = Vector3.ONE * 1.4                 # a walker stands taller than the trucks
	# a hitbox infantry can shoot at
	var hb := StaticBody3D.new()
	hb.collision_layer = G.LAYER_CHAR
	hb.set_meta("vehicle", self)
	var hcs := CollisionShape3D.new()
	var bs := BoxShape3D.new()
	bs.size = Vector3(3.6, 3.2, 6.5) if kind != "mech" else Vector3(2.4, 5.0, 2.0)
	hcs.shape = bs
	hcs.position.y = bs.size.y * 0.5
	hb.add_child(hcs)
	add_child(hb)


## The infection's vehicles: hulls split by fleshy masses, bone spines through the armour,
## tendrils hanging off the sides and dragging behind, glowing pustules and a pulsing sac.
func _overgrow(root: Node3D) -> void:
	var flesh := _mat(Color(0.34, 0.1, 0.28), 0.25)
	var flesh2 := _mat(Color(0.5, 0.17, 0.4), 0.35)
	var bone := _mat(Color(0.7, 0.62, 0.55))
	var glow := _mat(Color(0.95, 0.35, 1.0), 4.0)
	var mech := kind == "mech"
	var span := Vector3(1.4, 2.6, 1.2) if mech else Vector3(1.8, 2.2, 3.2)
	var y0 := 3.0 if mech else 2.2
	for i in 7:
		var sm := SphereMesh.new()
		sm.radius = randf_range(0.45, 1.0) * (0.7 if mech else 1.0)
		sm.height = sm.radius * 2.0
		sm.radial_segments = 8
		sm.rings = 4
		var mi := MeshInstance3D.new()
		mi.mesh = sm
		mi.material_override = flesh if i % 2 == 0 else flesh2
		mi.position = Vector3(randf_range(-span.x, span.x), y0 + randf_range(-0.4, 0.6), randf_range(-span.z, span.z))
		mi.scale = Vector3(1.0, randf_range(0.5, 0.9), randf_range(0.8, 1.4))
		root.add_child(mi)
	for i in 6:
		_cyl(root, 0.08, randf_range(0.8, 1.6), Vector3(randf_range(-span.x, span.x), y0 + 0.7, randf_range(-span.z, span.z)), bone,
			Vector3(randf_range(-0.7, 0.7), 0, randf_range(-0.7, 0.7)))
	for i in 4:                                   # tendrils hanging down the sides and dragging behind
		var side := -1.0 if i % 2 == 0 else 1.0
		_cyl(root, 0.12, 2.2, Vector3(side * (span.x + 0.2), y0 - 0.8, randf_range(-span.z, span.z * 1.3)), flesh,
			Vector3(randf_range(-0.4, 0.4), 0, side * 0.35))
	for i in 6:
		var pm := SphereMesh.new()
		pm.radius = randf_range(0.12, 0.24)
		pm.height = pm.radius * 2.0
		pm.radial_segments = 6
		pm.rings = 3
		var pu := MeshInstance3D.new()
		pu.mesh = pm
		pu.material_override = glow
		pu.position = Vector3(randf_range(-span.x, span.x), y0 + randf_range(0.2, 0.9), randf_range(-span.z, span.z))
		root.add_child(pu)
	var sac := SphereMesh.new()
	sac.radius = 0.7 if not mech else 0.5
	sac.height = sac.radius * 2.4
	var sm2 := MeshInstance3D.new()
	sm2.mesh = sac
	sm2.material_override = _mat(Color(0.85, 0.4, 0.8), 1.6)
	sm2.position = Vector3(0, y0 + 1.0, span.z * 0.6)
	sm2.name = "Sac"
	root.add_child(sm2)
	root.rotation.z = randf_range(-0.06, 0.06)     # listing under the weight of it


# ------------------------------------------------------------------ life

func take_hit(d: float, at: Vector3 = Vector3.ZERO, _by: Node = null, pen: float = 1.0) -> void:
	if destroyed:
		return
	hp -= d * clampf(pow(pen / float(SPECS[kind]["armor"]), 1.2), 0.15, 1.0)
	if hp <= 0.0:
		destroyed = true
		G.explosion(global_position + Vector3.UP * 2.0, 10.0)
		G.vehicles.erase(self)
		G.stat("vehicles_destroyed")
		if driver and is_instance_valid(driver) and G.commander:
			G.commander.on_vehicle_lost(self)
		if passengers > 0 and G.match_node:
			_unload()
		queue_free()


func order_move(world_p: Vector3) -> void:
	attack_target = null
	if has_meta("board_ship") and get_meta("board_ship") != null and is_instance_valid(get_meta("board_ship")):
		var f: Vector3 = load("res://scripts/campaign/bays.gd").ramp_foot(get_meta("board_ship"))
		if f.distance_to(world_p) > 30.0:
			remove_meta("board_ship")
	goal = ground.snap_local(ground.to_local(world_p))
	path = ground.path_local(position, goal)
	path_i = 0


func order_attack(t: Node) -> void:
	attack_target = t


func _settle() -> void:
	var from := global_position + Vector3.UP * 40.0
	var h := G.ray(from, from + Vector3.DOWN * 120.0, [], G.LAYER_WORLD)
	var gy := -1.0e9
	if G.match_node and G.match_node.get("on_surface") and not G.match_node.terrain_P.is_empty():
		gy = G.match_node.ground_y(global_position.x, global_position.z)
	if not h.is_empty():
		global_position.y = (h.position as Vector3).y
	elif gy > -1.0e8:
		global_position.y = gy                       # (the terrain's collision isn't up yet: use its height)


var _settle_t := 0.0


func _physics_process(dt: float) -> void:
	_t += dt
	if cargo_of != null:
		return                                    # stowed in a supply ship's bay
	_settle_t -= dt
	if _settle_t <= 0.0:
		_settle_t = 1.0
		_settle()                                 # (stay on the ground even when parked)
	if driver != null:
		for i in _cool.size():
			_cool[i] = float(_cool[i]) - dt
		return                                    # the player drives (player_drive)
	_think -= dt
	if _think <= 0.0:
		_think = 0.5
		_ai()
	# drive along the path
	var spd: float = SPECS[kind]["speed"]
	if path_i < path.size():
		var wp: Vector3 = path[path_i]
		var to := wp - position
		to.y = 0.0
		if to.length() < 2.5:
			path_i += 1
		else:
			var dir := to.normalized()
			rotation.y = lerp_angle(rotation.y, atan2(-dir.x, -dir.z), clampf(dt * 2.0, 0.0, 1.0))
			position += -transform.basis.z * spd * dt * clampf(1.0 - absf(angle_difference(rotation.y, atan2(-dir.x, -dir.z))), 0.15, 1.0)
			_settle()
			for k in _legs.size():                    # mech legs stride
				(_legs[k] as Node3D).rotation.x = sin(_t * 4.0 + k * PI) * 0.5
	# guns
	for i in _cool.size():
		_cool[i] = float(_cool[i]) - dt


func _enemy_in(radius: float, want: String) -> Node:
	var best: Node = null
	var bd := radius
	var me := global_position
	if want == "air":
		for f in G.fighters + G.pods + G.missiles:
			if is_instance_valid(f) and G.enemies(team, f.team):
				var d: float = me.distance_to(f.global_position)
				if d < bd:
					bd = d
					best = f
		for v in G.vessels:
			if is_instance_valid(v) and not v.destroyed and v.kind == "ship" and G.enemies(team, v.team):
				var d2: float = me.distance_to(v.global_position)
				if d2 < bd:
					bd = d2
					best = v
		return best
	if want in ["veh", "area"]:
		if attack_target != null and is_instance_valid(attack_target) and me.distance_to(attack_target.global_position) < radius:
			return attack_target
		for v in G.vehicles:
			if is_instance_valid(v) and v != self and G.enemies(team, v.team):
				var d3: float = me.distance_to(v.global_position)
				if d3 < bd:
					bd = d3
					best = v
		for p in G.pods:
			if is_instance_valid(p) and p.has_method("_ground_y") and G.enemies(team, p.team):   # outlaw MRAPs
				var d4: float = me.distance_to(p.global_position)
				if d4 < bd:
					bd = d4
					best = p
		for s in G.vessels:
			if is_instance_valid(s) and not s.destroyed and s.kind == "station" and G.enemies(team, s.team):
				var d5: float = me.distance_to(s.global_position)
				if d5 < bd:
					bd = d5
					best = s
		if G.match_node and G.match_node.get("outposts") != null:
			for o in G.match_node.outposts:
				if is_instance_valid(o) and not o.destroyed and G.enemies(team, o.team):
					var d7: float = me.distance_to(o.global_position)
					if d7 < bd:
						bd = d7
						best = o
		if best or want == "veh":
			return best
	# infantry
	if ground:
		for c in ground.occupants:
			if is_instance_valid(c) and c.state == "alive" and G.enemies(team, c.team):
				var d6: float = me.distance_to(c.global_position)
				if d6 < bd:
					bd = d6
					best = c
	return best


func _ai() -> void:
	if has_meta("board_ship"):
		var bs = get_meta("board_ship")
		if bs == null or not is_instance_valid(bs) or bs.destroyed:
			remove_meta("board_ship")
		else:
			var foot: Vector3 = load("res://scripts/campaign/bays.gd").ramp_foot(bs)
			if Vector2(global_position.x - foot.x, global_position.z - foot.z).length() < 16.0:
				remove_meta("board_ship")
				G.match_node.board_vehicle(self, bs)
				return
			if path_i >= path.size():
				order_move(foot)
	var guns: Array = GUNS[kind]
	var rng: float = SPECS[kind]["range"]
	for i in guns.size():
		if float(_cool[i]) > 0.0:
			continue
		var g: Array = guns[i]
		var tgt := _enemy_in(rng if g[3] != "inf" else minf(rng, 300.0), g[3])
		if tgt == null:
			continue
		var at: Vector3 = tgt.global_position + Vector3.UP * 1.0
		if tgt.get("aabb") != null:
			at = tgt.to_global(tgt.aabb.get_center())
		if g[3] != "area" and g[3] != "air":
			var h := G.ray(global_position + Vector3.UP * 3.0, at, [], G.LAYER_WORLD)
			if not h.is_empty() and (h.position as Vector3).distance_to(at) > 6.0:
				continue                              # no line of fire
		_cool[i] = g[1]
		_fire(g, tgt, at)
	# point the turret at whatever's closest
	var look := _enemy_in(rng, "veh")
	if look == null:
		look = _enemy_in(rng, "inf")
	if look and _turret:
		var lp: Vector3 = to_local(look.global_position)
		_turret.rotation.y = atan2(-lp.x, -lp.z)
	# the AI-run sides move on their own; ours follow orders but still close on attack targets
	if attack_target != null and is_instance_valid(attack_target) and path_i >= path.size() \
			and global_position.distance_to(attack_target.global_position) > rng * 0.8:
		order_move(attack_target.global_position)
		attack_target = attack_target


func _fire(g: Array, tgt: Node, at: Vector3) -> void:
	var from: Vector3 = (_turret.global_position if _turret else global_position + Vector3.UP * 3.0) + Vector3.UP * 0.3
	var dmg: float = g[0]
	var col := Color(1.0, 0.8, 0.4) if faction != 2 else Color(1.0, 0.3, 0.45)
	if team == 4:
		col = Color(0.8, 0.4, 1.0)
	match g[3]:
		"area":
			# mortar: lobbed, lands somewhere round the target
			var land := at + Vector3(randfn(0, 1), 0, randfn(0, 1)) * 18.0
			G.tracer(from, from + Vector3.UP * 30.0, col, 0.15, 0.2)
			if G.sfx:
				G.sfx.play("cannon", from, -4.0)
			get_tree().create_timer(clampf(from.distance_to(land) / 180.0, 1.0, 4.0)).timeout.connect(func():
				G.explosion(land, 7.0)
				G.blast(land, 12.0, 60.0, null)
				for v in G.vehicles.duplicate():
					if is_instance_valid(v) and v.global_position.distance_to(land) < 12.0:
						v.take_hit(dmg * 0.7, land, null, g[2])
				for s in G.vessels:
					if is_instance_valid(s) and s.kind == "station" and not s.destroyed and s.aabb.grow(10.0).has_point(s.to_local(land)):
						s.take_hit(dmg, land, null))
			return
		_:
			at += Vector3(randf_range(-1, 1), randf_range(-0.5, 0.5), randf_range(-1, 1)) * (0.8 if g[3] == "inf" else 1.5)
			G.tracer(from, at, col, 0.05 if dmg < 30.0 else 0.2, 0.06)
			if G.sfx:
				G.sfx.play("heavy" if dmg < 30.0 else "cannon", from, -6.0 if dmg < 30.0 else -2.0)
			if dmg >= 100.0:
				G.explosion(at, 4.0)
	if not is_instance_valid(tgt):
		return
	if tgt.get("rig") != null:
		tgt.take_damage(dmg, null, from)
	elif tgt.has_method("take_hit"):
		if tgt.get("is_vehicle"):
			tgt.take_hit(dmg, at, null, g[2])
		else:
			tgt.take_hit(dmg, at, null)


# ------------------------------------------------------------------ player driving

const TURN_RATE := {"tank": 0.9, "ifv": 1.1, "mrap_ai": 1.3, "mrap_aa": 1.3, "mrap_av": 1.3, "mech": 1.6, "mortar": 0.9}


## The player's controls, every frame they sit in the driver's seat: W/S throttle, A/D
## steer, the turret follows the mouse aim, LMB main gun, RMB the second weapon.
func player_drive(dt: float, throttle: float, turn: float, boost: bool, aim: Vector3, fire1: bool, fire2: bool) -> void:
	path = PackedVector3Array()
	path_i = 0
	attack_target = null
	aim_point = aim
	var spd: float = SPECS[kind]["speed"] * (1.35 if boost else 1.0)
	drive_vel = lerpf(drive_vel, throttle * spd * (1.0 if throttle >= 0.0 else 0.5), clampf(dt * 2.2, 0.0, 1.0))
	rotation.y -= turn * float(TURN_RATE.get(kind, 1.0)) * dt * (1.0 if drive_vel >= -0.1 else -1.0)
	var step := -transform.basis.z * drive_vel * dt
	if step.length() > 0.0005:
		# don't drive through buildings or wrecks: a ray at bumper height
		var from := global_position + Vector3.UP * 1.3
		var dir := step.normalized()
		var h := G.ray(from, from + dir * (step.length() + (2.0 if kind == "mech" else 4.0)), [], G.LAYER_WORLD)
		if h.is_empty():
			position += step
			_settle()
		else:
			drive_vel *= 0.3
		for k in _legs.size():
			(_legs[k] as Node3D).rotation.x = sin(_t * 4.0 * absf(drive_vel) / maxf(spd, 0.1) * 1.5 + k * PI) * 0.5
	if _turret and aim != Vector3.INF:
		var lp: Vector3 = to_local(aim)
		_turret.rotation.y = lerp_angle(_turret.rotation.y, atan2(-lp.x, -lp.z), clampf(dt * 4.0, 0.0, 1.0))
	var guns: Array = GUNS[kind]
	for i in guns.size():
		var want: bool = fire1 if i == 0 else fire2
		if not want or float(_cool[i]) > 0.0 or aim == Vector3.INF:
			continue
		_cool[i] = guns[i][1]
		var g: Array = guns[i]
		var at := aim
		var tgt := _target_near(at, 4.0 if g[3] == "inf" else 7.0)
		_fire(g, tgt, at)
		if g[0] >= 100.0 and g[3] != "area":
			G.blast(at, 5.0, float(g[0]) * 0.25, null)
	if driver and is_instance_valid(driver):
		driver.global_position = global_position + Vector3.UP * 0.5


## Whatever enemy is closest to where the player's shot lands.
func _target_near(at: Vector3, r: float) -> Node:
	var best: Node = null
	var bd := r
	for v in G.vehicles:
		if is_instance_valid(v) and v != self and G.enemies(team, v.team):
			var d: float = (v.global_position + Vector3.UP * 2.0).distance_to(at)
			if d < bd:
				bd = d
				best = v
	for p in G.pods:
		if is_instance_valid(p) and G.enemies(team, p.team):
			var d2: float = p.global_position.distance_to(at)
			if d2 < bd + 3.0:
				bd = d2
				best = p
	if ground:
		for c in ground.occupants:
			if is_instance_valid(c) and c.state == "alive" and G.enemies(team, c.team):
				var d3: float = (c.global_position + Vector3.UP).distance_to(at)
				if d3 < bd:
					bd = d3
					best = c
	if best == null and G.match_node and G.match_node.get("outposts") != null:
		for o in G.match_node.outposts:
			if is_instance_valid(o) and not o.destroyed and G.enemies(team, o.team) and o.aabb.grow(3.0).has_point(o.to_local(at)):
				return o
	if best == null:
		for s in G.vessels:
			if is_instance_valid(s) and not s.destroyed and G.enemies(team, s.team) and s.aabb.grow(4.0).has_point(s.to_local(at)):
				return s
	return best


func hud_line() -> String:
	var parts: Array = []
	for i in GUNS[kind].size():
		parts.append("%s %s" % ["LMB" if i == 0 else "RMB", "ready" if float(_cool[i]) <= 0.0 else "%.1fs" % float(_cool[i])])
	if kind == "ifv":
		parts.append("troops %d/6" % passengers)
	return "  ·  ".join(parts)


# ------------------------------------------------------------------ IFV troops

## Put the squad aboard down beside the vehicle.
func _unload() -> int:
	if passengers <= 0 or ground == null:
		return 0
	var n := passengers
	passengers = 0
	var roles: Array = ["squad_leader", "rifleman", "rifleman", "medic", "heavy", "breacher"].slice(0, n)
	G.match_node.spawn_squad(ground, ground.snap_local(position + transform.basis.z * 6.0), team, G.team_fac(team), roles, false)
	return n


func unload() -> int:
	return _unload()


## Friendly infantry within 15 m climb in (up to 6).
func load_troops() -> int:
	var n := 0
	for c in ground.occupants.duplicate():
		if passengers >= 6:
			break
		if c.team == team and c.state == "alive" and not c.is_crew() and c != G.possessed and c.position.distance_to(position) < 15.0:
			passengers += 1
			G.match_node.logistics._remove_person(c)
			n += 1
	return n
