extends Node
## The grenadier:  godot --headless --path . res://match.tscn -- --grenadiertest
## Kit and gun, a launcher shell into a target 15 m off, a dud at point-blank range, and the
## AI's choice to fire (a group, yes; a friend near the target, no). Prints PASS/FAIL lines
## and "GRENADIER TEST DONE <fails>".

var t := 0.0
var step := 0
var fails := 0
var c: Node
var foe: Node
var foe2: Node
var shell: Node3D
var _wait := 0.0
var _hp0 := 0.0


func _check(ok: bool, what: String) -> void:
	print("PASS " if ok else "FAIL ", what)
	if not ok:
		fails += 1


func _physics_process(dt: float) -> void:
	t += dt
	if t < 2.0:
		return
	if _wait > 0.0:
		_wait -= dt
		return
	match step:
		0:
			var n := 0
			for o in G.characters:
				if is_instance_valid(o) and o.role == "grenadier":
					n += 1
			_check(n > 0, "the match spawned grenadiers (%d)" % n)
			# a fresh one in the team 1 flagship's hangar, a hostile 15 m down it
			var v: Node = null
			for vv in G.vessels:
				if vv.get_meta("slot", "") == "flag1":
					v = vv
			var pads: Array = v.marks_like("Hangar_ShuttlePad") if v else []
			_check(not pads.is_empty(), "the flagship has a hangar")
			if pads.is_empty():
				_done()
				return
			var base: Vector3 = v.local_of(pads[0])
			c = G.match_node.spawn_character(v, v.snap_local(base + Vector3(0, 0, 9)), v.team, G.team_fac(v.team), "grenadier")
			c.rotation.y = 0.0
			c.order = {"type": "hold", "pos": c.position, "vessel": v}
			G.match_node.ai.attack_after = 99999.0
			_check(c.weapon_model == ("F2_BullpupGL" if c.faction == 2 else "F1_BullpupGL"), "carries the BullpupGL (%s)" % c.weapon_model)
			_check(c.spare.size() == 4 and c.medpens.size() >= 1, "4 spare mags (%d), a medpen" % c.spare.size())
			_check(c.gl_ammo == 6 and c.gl_rounds.size() == 6, "6 shells on the bandolier")
			_check(c.breach_ammo == 2 and c.breach_rounds.size() == 2, "2 breaching rounds on the pack")
			_check(c.rig.weapon != null and c.rig.weapon.find_child("GLMuzzle", true, false) != null, "the gun has a GLMuzzle")
			foe = G.match_node.spawn_character(v, v.snap_local(base + Vector3(0, 0, -6)), 2, 2, "rifleman")
			foe.rotation.y = 0.0
			foe.order = {"type": "hold", "pos": foe.position, "vessel": c.vessel}
			step = 1
			_wait = 0.5
		1:
			_hp0 = foe.hp
			var from: Vector3 = c._gl_muzzle()
			var dir: Vector3 = c._lob(from, foe.global_position + Vector3.UP * 0.3, 50.0)
			_check(dir != Vector3.ZERO, "a firing solution to 15 m")
			shell = c.fire_launcher(from, dir)
			_check(shell != null and c.gl_ammo == 5, "fired: 5 shells left")
			var shown := 0
			for n in c.gl_rounds:
				shown += 1 if (n as Node3D).visible else 0
			_check(shown == 5, "the bandolier shows 5 shells (%d)" % shown)
			step = 2
			_wait = 1.2
		2:
			_check(not is_instance_valid(shell), "the shell burst")
			_check(foe.hp < _hp0 or foe.state != "alive", "the target was hurt (%.0f -> %.0f, %s)" % [_hp0, foe.hp, foe.state])
			# point-blank: into the floor a metre ahead, before it arms
			var from2: Vector3 = c.eye()
			var fwd: Vector3 = -c.global_transform.basis.z
			shell = c.fire_launcher(from2, (fwd + Vector3.DOWN * 1.2).normalized())
			step = 3
			_wait = 0.3
		3:
			_check(is_instance_valid(shell) and shell.dud, "a shell that hits within 4 m is a dud")
			# AI: two hostiles together 18 m off -> fires
			for o in [foe]:
				if is_instance_valid(o) and o.state == "alive":
					o.hp = o.max_hp
			if not is_instance_valid(foe) or foe.state != "alive":
				var base: Vector3 = c.vessel.local_of(c.vessel.marks_like("Hangar_ShuttlePad")[0])
				foe = G.match_node.spawn_character(c.vessel, c.vessel.snap_local(base + Vector3(0, 0, -9)), 2, 2, "rifleman")
			foe2 = G.match_node.spawn_character(c.vessel, foe.position + Vector3(1.5, 0, 0), 2, 2, "rifleman")
			c._gl_cd = 0.0
			c.target = foe
			var n0: int = c.gl_ammo
			_check(c._ai_launcher() and c.gl_ammo == n0 - 1, "AI fires into a group of two (%.1f m)" % c.global_position.distance_to(foe.global_position))
			# a friend beside the target -> holds
			var pal: Node = G.match_node.spawn_character(c.vessel, foe.position + Vector3(-1.5, 0, 0), 1, c.faction, "rifleman")
			c._gl_cd = 0.0
			_check(not c._ai_launcher(), "AI holds fire with a friend near the target")
			pal.state = "dead"
			# too close -> holds
			c._gl_cd = 0.0
			foe2.state = "dead"
			c.target = foe
			var save: Vector3 = c.position
			c.position = foe.position + Vector3(0, 0, 4)
			_check(not c._ai_launcher(), "AI holds fire under 8 m")
			c.position = save
			_done()


func _done() -> void:
	print("GRENADIER TEST DONE %d" % fails)
	set_physics_process(false)
	get_tree().quit()
