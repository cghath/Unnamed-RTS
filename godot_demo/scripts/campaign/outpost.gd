extends StaticBody3D
## One piece of a ground installation built straight onto the terrain (outlaw camps,
## infected hives). It's part of the ground the infantry walk (baked into the open-ground
## navigation, so troops path right into and through the camp) and it can be shot to bits:
##   core    the camp's command bunker / the hive heart. Destroy it and the base falls.
##   gun     an outlaw gun nest: a heavy gun that shoots infantry and vehicles
##   spore   an infected spore tower: poisons anything nearby every few seconds
##   nest    an infected egg cluster: hatches infected while enemies are close
## It looks enough like a station to ships (aabb, team, destroyed, take_hit, armor) that
## turrets, artillery and drop orders can target it.

var kind := "outpost"
var cls := "GROUND_OUTPOST"
var part := "core"
var team := 3
var faction := 3
var hp := 1000.0
var max_hp := 1000.0
var hull := 1000.0
var max_hull := 1000.0
var shields := 0.0
var max_shields := 0.0
var destroyed := false
var display_name := ""
var aabb := AABB()
var base_key := ""
var base: Array = []              # every part of the same base (shared)
var visual: Node3D
var _cool := 0.0
var _hatched := 0
var _t := 0.0
var _heart: Node3D

const ARMOR := {"core": 3.0, "gun": 2.0, "spore": 1.2, "nest": 1.0, "brood": 1.2, "gravemind": 3.0}


func init(part_: String, team_: int, name_: String, size: Vector3, hp_: float, key: String, parts: Array) -> void:
	part = part_
	team = team_
	faction = 3
	display_name = name_
	max_hp = hp_
	hp = hp_
	hull = hp_
	max_hull = hp_
	base_key = key
	base = parts
	parts.append(self)
	aabb = AABB(Vector3(-size.x * 0.5, 0, -size.z * 0.5), size)
	collision_layer = G.LAYER_WORLD
	set_meta("vehicle", self)                    # small-arms hits land on it (see character.gd)
	visual = Node3D.new()
	add_child(visual)
	var pk := Area3D.new()
	pk.collision_layer = G.LAYER_PICK
	pk.monitoring = false
	var cs := CollisionShape3D.new()
	var sp := SphereShape3D.new()
	sp.radius = maxf(size.x, size.z) * 0.55
	cs.shape = sp
	cs.position.y = size.y * 0.5
	pk.add_child(cs)
	pk.set_meta("unit", self)
	add_child(pk)
	_cool = randf() * 3.0


func armor() -> float:
	return float(ARMOR.get(part, 1.5))


func set_heart(n: Node3D) -> void:
	_heart = n


func take_hit(d: float, at: Vector3 = Vector3.ZERO, _by: Node = null, pen: float = 1.0) -> void:
	if destroyed:
		return
	hp -= d * clampf(pow(pen / armor(), 1.1), 0.15, 1.2)
	hull = hp
	if randf() < 0.15:
		G.flash(at if at != Vector3.ZERO else global_position, Color(1.0, 0.6, 0.3) if team != 4 else Color(0.8, 0.3, 1.0), 2.0, 3.0, 0.06)
	if hp <= 0.0:
		_die(true)


func _die(announce: bool) -> void:
	if destroyed:
		return
	destroyed = true
	hp = 0.0
	hull = 0.0
	G.explosion(global_position + Vector3.UP * aabb.size.y * 0.4, maxf(6.0, aabb.size.length() * 0.35),
		Color(0.8, 0.3, 1.0) if team == 4 else Color(1.0, 0.55, 0.15))
	# what's left: a scorched, slumped shell (still cover, still in the nav)
	for mi in visual.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		m.material_override = G._mat(Color(0.1, 0.09, 0.09) if team != 4 else Color(0.18, 0.08, 0.16))
	visual.scale = Vector3(1.0, 0.45, 1.0)
	for l in find_children("*", "OmniLight3D", true, false):
		(l as Node3D).visible = false
	if G.match_node and G.match_node.get("outposts") != null:
		G.match_node.outposts.erase(self)
	if part == "gravemind":
		if G.campaign:
			var hk: String = get_meta("gm_of", "")
			var rec: Dictionary = G.campaign.world.get(hk, {})
			rec["gravemind"] = false
			rec["biomass"] = 0.0
			G.campaign.world[hk] = rec
			G.campaign.credits += 1500
		G.say("The GRAVEMIND is dead (+1500 cr)", 1)
		G.stat("graveminds_killed")
		return
	if part == "core" and team == 1:
		# one of our outposts has fallen: everything round it goes, the site is open again
		for p in base:
			if is_instance_valid(p) and p != self:
				p._die(false)
		if G.campaign:
			G.campaign.world[base_key] = {"team": 0, "destroyed": true}
		G.say("OUTPOST LOST: the command post was destroyed", 1)
		return
	if part == "core":
		for p in base:
			if is_instance_valid(p) and p != self:
				p._die(false)
		if G.campaign:
			G.campaign.world[base_key] = {"team": team, "destroyed": true}
			G.campaign.credits += 600
			var r: Dictionary = G.campaign.stores
			r["alloys"] = float(r.get("alloys", 0.0)) + 250.0
		G.say("%s destroyed: the base has fallen (+600 cr, +250 alloys)" % display_name, 1)
		G.stat("bases_destroyed")
	elif announce:
		G.say("%s destroyed" % display_name, 1)


# ------------------------------------------------------------------ what each part does

func _physics_process(dt: float) -> void:
	if destroyed or G.is_client():
		return
	_t += dt
	if _heart and is_instance_valid(_heart):
		var k := 1.0 + sin(_t * 2.6) * 0.08 + maxf(0.0, sin(_t * 5.2)) * 0.05
		_heart.scale = Vector3.ONE * k
	_cool -= dt
	if _cool > 0.0:
		return
	match part:
		"gun":
			_cool = 0.22
			_gun()
		"spore":
			_cool = 5.0
			_spores()
		"nest":
			_cool = 18.0
			_hatch()
		"brood":
			_cool = 14.0
			_brood()
		"gravemind":
			_cool = 6.0
			_gravemind()
		_:
			_cool = 5.0


func _enemies_near(r: float, with_vehicles: bool = true) -> Array:
	var out: Array = []
	var me := global_position
	var gnd: Node = G.match_node.ground if G.match_node else null
	if gnd:
		for c in gnd.occupants:
			if is_instance_valid(c) and c.state == "alive" and G.enemies(team, c.team) and c.global_position.distance_to(me) < r:
				out.append(c)
	if with_vehicles:
		for v in G.vehicles:
			if is_instance_valid(v) and G.enemies(team, v.team) and v.global_position.distance_to(me) < r:
				out.append(v)
	return out


func _gun() -> void:
	var near := _enemies_near(260.0)
	if near.is_empty():
		_cool = 1.0
		return
	var muzzle: Vector3 = global_position + Vector3.UP * 2.4
	near.sort_custom(func(a, b): return a.global_position.distance_to(muzzle) < b.global_position.distance_to(muzzle))
	for tgt in near:
		var at: Vector3 = tgt.global_position + Vector3.UP * (1.0 if tgt.get("rig") != null else 2.0)
		var h := G.ray(muzzle, at, [get_rid()], G.LAYER_WORLD)
		if not h.is_empty() and (h.position as Vector3).distance_to(at) > 3.0:
			continue
		at += Vector3(randf_range(-1, 1), randf_range(-0.4, 0.4), randf_range(-1, 1)) * 1.2
		G.tracer(muzzle, at, Color(0.55, 1.0, 0.35), 0.05, 0.05)
		if G.sfx and randf() < 0.4:
			G.sfx.play("heavy", muzzle, -6.0)
		if randf() < 0.55:
			if tgt.get("rig") != null:
				tgt.take_damage(11.0, null, muzzle)
			else:
				tgt.take_hit(16.0, at, null, 1.2)
		return
	_cool = 0.8


func _spores() -> void:
	var near := _enemies_near(75.0)
	if near.is_empty():
		_cool = 2.0
		return
	var top: Vector3 = global_position + Vector3.UP * aabb.size.y
	for tgt in near:
		var p: Vector3 = tgt.global_position
		G.tracer(top, p + Vector3.UP, Color(0.7, 0.3, 1.0), 0.25, 0.4)
		G.flash(p + Vector3.UP, Color(0.7, 0.3, 1.0), 3.0, 6.0, 0.4)
		if tgt.get("rig") != null:
			tgt.take_damage(18.0, null, top)
		else:
			tgt.take_hit(40.0, p, null, 1.0)
	if G.sfx:
		G.sfx.play("cannon", top, -10.0)


func _hatch() -> void:
	if _hatched >= 12 or G.match_node == null or G.match_node.ground == null:
		return
	if _enemies_near(450.0).is_empty():
		_cool = 4.0
		return
	var gnd: Node3D = G.match_node.ground
	var n := 2 + randi() % 2
	_hatched += n
	var roles: Array = []
	for i in n:
		roles.append("x")
	G.match_node.spawn_squad(gnd, gnd.near_local(gnd.to_local(global_position) + Vector3(0, 0, 6.0), 5.0), 4, 3, roles, false)
	G.flash(global_position + Vector3.UP * 2.0, Color(0.8, 0.3, 1.0), 4.0, 10.0, 0.5)


## Brood sacs keep the hive's numbers up: while the swarm round the heart is thin, they
## split open and birth a couple more.
var _born := 0


func _brood() -> void:
	if _born >= 60 or G.match_node == null or G.match_node.ground == null:
		return
	var gnd: Node3D = G.match_node.ground
	var home: Vector3 = global_position
	for p in base:
		if is_instance_valid(p) and p.part == "core":
			home = p.global_position
	var n := 0
	for c in gnd.occupants:
		if is_instance_valid(c) and c.team == 4 and c.state == "alive" and c.global_position.distance_to(home) < 130.0:
			n += 1
	if n >= 10:
		return
	_born += 2
	var out: Vector3 = (home - global_position).normalized() * 3.0
	G.match_node.spawn_squad(gnd, gnd.snap_local(gnd.to_local(global_position + out)), 4, 3, ["x", "x"], false)
	G.flash(global_position + Vector3.UP * 3.6, Color(0.9, 0.4, 0.9), 4.0, 8.0, 0.4)
	if G.sfx:
		G.sfx.play("cannon", global_position, -12.0)


## The gravemind: lashes out at anything close with its tendrils.
func _gravemind() -> void:
	var near := _enemies_near(120.0)
	var top: Vector3 = global_position + Vector3.UP * 12.0
	for tgt in near.slice(0, 4):
		var p: Vector3 = tgt.global_position
		G.tracer(top, p + Vector3.UP, Color(0.75, 0.25, 0.9), 0.6, 0.35)
		if tgt.get("rig") != null:
			tgt.take_damage(35.0, null, top)
		else:
			tgt.take_hit(120.0, p, null, 2.0)


## A spreader ship tears free of the gravemind and climbs away (galaxy-level record kept
## by infection.gd).
func launch_spreader() -> void:
	var m: Node = G.match_node
	if m == null:
		return
	var p := Vector3(global_position.x, 0.0, global_position.z)
	var s: Node3D = m.spawn_runtime_ship("SMALL_FRIGATE", 4, 3, "Infected Spreader", p, [], "hive")
	load("res://scripts/campaign/sandbox_ai.gd").overgrow_ship(s)
	G.flash(global_position + Vector3.UP * 10.0, Color(0.85, 0.3, 1.0), 12.0, 40.0, 0.8)
	G.say("The gravemind birthed an infected ship: it's climbing for orbit to spread the infection", 1)
	get_tree().create_timer(45.0).timeout.connect(func():
		if is_instance_valid(s) and not s.destroyed:
			G.vessels.erase(s)
			s.queue_free()
			G.say("An infected spreader has left orbit", 1))
