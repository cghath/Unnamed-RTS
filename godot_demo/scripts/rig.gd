extends Node3D
## Procedural animation for the jointed robot characters.
##
## The character file is a tree of joints (Godot humanoid names) facing +Z in its
## own space. Poses are written as directions for each limb in that space, and a
## two-bone IK puts the hands on the weapon's Grip and SupportHand markers, so any
## weapon is held properly without hand-made animations.
##
## The owner sets the inputs every frame: speed, aim_pitch, aiming, crouch, mode.
## Modes: "normal", "work", "carry", "kneel", "downed", "dead", "seated".

const BONES := ["Root", "Hips", "Spine", "Chest", "UpperChest", "Neck", "Head",
	"LeftShoulder", "LeftUpperArm", "LeftLowerArm", "LeftHand",
	"RightShoulder", "RightUpperArm", "RightLowerArm", "RightHand",
	"LeftUpperLeg", "LeftLowerLeg", "LeftFoot", "LeftToes",
	"RightUpperLeg", "RightLowerLeg", "RightFoot", "RightToes"]
const CHILD := {"Hips": "Spine", "Spine": "Chest", "Chest": "UpperChest", "UpperChest": "Neck", "Neck": "Head",
	"LeftShoulder": "LeftUpperArm", "LeftUpperArm": "LeftLowerArm", "LeftLowerArm": "LeftHand",
	"RightShoulder": "RightUpperArm", "RightUpperArm": "RightLowerArm", "RightLowerArm": "RightHand",
	"LeftUpperLeg": "LeftLowerLeg", "LeftLowerLeg": "LeftFoot", "LeftFoot": "LeftToes",
	"RightUpperLeg": "RightLowerLeg", "RightLowerLeg": "RightFoot", "RightFoot": "RightToes"}

var model: Node3D                 # the character file's root, faces +Z
var b := {}                       # bone name -> Node3D
var rest_pos := {}                # bone name -> local position at rest
var rest_model := {}              # bone name -> head position in model space at rest
var axis := {}                    # bone name -> rest direction (model space)
var arm_len := {}                 # side -> [upper, lower]
var leg_len := 0.0
var weapon: Node3D = null
var wm := {}                      # weapon markers
var held: Node3D = null           # tool / crate / item in hands
var faction := 1

# inputs
var speed := 0.0
var aim_pitch := 0.0
var aiming := false
var crouch := false
var mode := "normal"
var work_target := Vector3(0, 1.15, 0.5)    # model space, for "work"
var first_person := false
var ads := false                  # aiming down sights (first person): the sight lines up with the eye
var recoil := 0.0                 # kicks to 1 on each shot, settles by itself
var reload := -1.0                # 0..1 while reloading (left hand fetches a new mag), -1 otherwise
var throw_t := -1.0               # 0..1 while throwing a grenade
var kick_t := -1.0               # 0..1 while kicking a door
var _jerk := Vector3.ZERO
var _jerk_t := 0.0
var twitch := 0.0                 # infected units jerk and twitch
var _hand_mag: Node3D = null      # the magazine/cell in the left hand during a reload

var _phase := 0.0
var _crouch_amt := 0.0
var _aim_amt := 0.0
var _t := 0.0


func setup(char_path: String, fac: int) -> void:
	faction = fac
	model = load(char_path).instantiate()
	add_child(model)
	rotation.y = PI                      # characters face +Z in the file; Godot forward is -Z
	for n in BONES:
		var node: Node3D = model.find_child(n, true, false)
		if node:
			b[n] = node
			rest_pos[n] = node.position
	for n in b:
		rest_model[n] = model.to_local(b[n].global_position) if is_inside_tree() else _model_pos(n)
	for n in b:
		if CHILD.has(n) and b.has(CHILD[n]):
			axis[n] = (rest_model[CHILD[n]] - rest_model[n]).normalized()
	axis["LeftHand"] = Vector3.RIGHT
	axis["RightHand"] = Vector3.LEFT
	axis["Head"] = Vector3.UP
	for side in ["Left", "Right"]:
		arm_len[side] = [rest_model[side + "UpperArm"].distance_to(rest_model[side + "LowerArm"]),
			rest_model[side + "LowerArm"].distance_to(rest_model[side + "Hand"])]
	leg_len = rest_model["LeftUpperLeg"].distance_to(rest_model["LeftLowerLeg"])


func _model_pos(n: String) -> Vector3:
	var p := Vector3.ZERO
	var node: Node = b[n]
	while node and node != model:
		p += (node as Node3D).position
		node = node.get_parent()
	return p


func set_weapon(path: String) -> void:
	if weapon:
		weapon.queue_free()
		weapon = null
	wm.clear()
	if path == "":
		return
	weapon = load(path).instantiate()
	model.add_child(weapon)
	weapon.visible = not first_person
	for k in ["Grip", "SupportHand", "Muzzle", "Sight", "MagWell", "CellPort", "Mag"]:
		var m: Node3D = weapon.find_child(k, true, false)
		if m:
			wm["MagWell" if k == "CellPort" else k] = m
	if _hand_mag:
		_hand_mag.queue_free()
		_hand_mag = null
	if wm.has("Mag") and wm["Mag"] is MeshInstance3D:
		var hm := MeshInstance3D.new()
		hm.mesh = (wm["Mag"] as MeshInstance3D).mesh
		hm.visible = false
		model.add_child(hm)
		_hand_mag = hm


func set_held(node: Node3D) -> void:
	if held:
		held.queue_free()
	held = node
	if node:
		model.add_child(node)


func muzzle_position() -> Vector3:
	if weapon and wm.has("Muzzle"):
		return wm["Muzzle"].global_position
	return global_position + Vector3.UP * 1.4


func show_slot(slot: String, visible_: bool) -> void:
	var n: Node = model.find_child("Slot_" + slot, true, false)
	if n:
		n.visible = visible_


func set_first_person(on: bool) -> void:
	first_person = on
	# the camera's viewmodel (viewmodel.gd) shows the gun and forearms instead
	if weapon:
		weapon.visible = not on
	# ...and the shoulders, collar and arms would only block the view looking down
	for bn in ["LeftShoulder", "LeftUpperArm", "LeftLowerArm", "LeftHand", "RightShoulder", "RightUpperArm",
			"RightLowerArm", "RightHand", "UpperChest", "Neck"]:
		if b.has(bn):
			for ch in b[bn].get_children():
				if ch is GeometryInstance3D or String(ch.name).ends_with("_mesh"):
					ch.visible = not on
	if b.has("Head"):
		for c in b["Head"].get_children():
			if c is MeshInstance3D or String(c.name).ends_with("_mesh"):
				c.visible = not on
				for cc in c.get_children():
					if cc is GeometryInstance3D:
						cc.visible = not on


# ------------------------------------------------------------------ pose helpers

## Point a bone along `dir` (model space) with as little twist as possible.
func aim_bone(n: String, dir: Vector3) -> void:
	if not b.has(n) or dir.length() < 0.0001:
		return
	var bone: Node3D = b[n]
	var pb: Basis = (bone.get_parent() as Node3D).global_basis.orthonormalized()
	var ax: Vector3 = axis[n]
	var from := (pb * ax).normalized()
	var to := (model.global_basis.orthonormalized() * dir).normalized()
	if from.dot(to) > 0.99999:
		bone.global_basis = pb
		return
	var q := Quaternion(from, to) if from.dot(to) > -0.9999 else Quaternion(pb * Vector3.UP, PI)
	bone.global_basis = Basis(q) * pb


## Two-bone IK: put the hand of `side` at `target` (model space) with the elbow toward `pole`.
func reach(side: String, target: Vector3, pole: Vector3) -> void:
	var s := model.to_local(b[side + "UpperArm"].global_position)
	var l1: float = arm_len[side][0]
	var l2: float = arm_len[side][1]
	var to_t := target - s
	var d: float = clamp(to_t.length(), 0.05, l1 + l2 - 0.002)
	var dir := to_t.normalized()
	var a := (l1 * l1 + d * d - l2 * l2) / (2.0 * d)
	var h := sqrt(max(0.0, l1 * l1 - a * a))
	var perp := (pole - dir * pole.dot(dir))
	perp = perp.normalized() if perp.length() > 0.001 else Vector3.DOWN
	var elbow := s + dir * a + perp * h
	aim_bone(side + "UpperArm", elbow - s)
	aim_bone(side + "LowerArm", (s + dir * d) - elbow)
	aim_bone(side + "Hand", (s + dir * d) - elbow)


func leg(side: String, thigh: float, knee: float) -> void:
	## thigh > 0 swings the leg forward, knee > 0 bends the knee (foot goes back).
	var up_dir := Vector3(0, -cos(thigh), sin(thigh))
	var lo_dir := Vector3(0, -cos(thigh - knee), sin(thigh - knee))
	aim_bone(side + "UpperLeg", up_dir)
	aim_bone(side + "LowerLeg", lo_dir)
	aim_bone(side + "Foot", Vector3(0, -0.35, 1.0))


func _reset() -> void:
	for n in b:
		b[n].position = rest_pos[n]
		b[n].rotation = Vector3.ZERO
	model.position = Vector3.ZERO
	model.rotation = Vector3.ZERO


# ------------------------------------------------------------------ the animation

func animate(dt: float) -> void:
	if model == null:
		return
	_t += dt
	_reset()
	if mode == "downed" or mode == "dead":
		_lying(mode == "dead")
		return
	var moving: float = clamp(speed / 4.0, 0.0, 1.6)
	_crouch_amt = move_toward(_crouch_amt, 1.0 if (crouch or mode == "kneel") else 0.0, dt * 4.0)
	_aim_amt = move_toward(_aim_amt, 1.0 if aiming else 0.0, dt * 5.0)
	_phase += dt * (2.0 + speed * 1.7) if speed > 0.2 else 0.0
	# ---- legs and hips
	var sw: float = sin(_phase) * 0.55 * min(moving, 1.0)
	var lift: float = max(0.0, cos(_phase)) * 0.7 * min(moving, 1.0)
	var lift2: float = max(0.0, -cos(_phase)) * 0.7 * min(moving, 1.0)
	var c := _crouch_amt
	if mode == "kneel":
		leg("Left", 1.3, 1.35)
		leg("Right", -0.15, 1.9)
		b["Hips"].position = rest_pos["Hips"] + Vector3(0, -leg_len * 0.95, 0)
	elif mode == "seated":
		leg("Left", 1.5, 1.5)
		leg("Right", 1.5, 1.5)
		b["Hips"].position = rest_pos["Hips"] + Vector3(0, -leg_len * 0.95, -0.05)
	else:
		leg("Left", sw + c * 0.9, lift + c * 1.6)
		leg("Right", -sw + c * 0.9, lift2 + c * 1.6)
		var drop := leg_len * (1.0 - cos(c * 0.9)) + leg_len * (1.0 - cos(c * 0.7)) * 0.6
		var bob: float = abs(sin(_phase)) * 0.03 * min(moving, 1.0)
		b["Hips"].position = rest_pos["Hips"] + Vector3(0, -drop - bob, c * 0.05)
		if kick_t >= 0.0:                        # front kick: chamber the knee, drive the heel out
			kick_t += dt * 2.6
			var ph: float = clampf(kick_t, 0.0, 1.0)
			var thigh: float = sin(ph * PI) * 1.45
			var knee: float = 1.6 * (1.0 - smoothstep(0.3, 0.5, ph)) + 1.2 * smoothstep(0.6, 0.9, ph) * (1.0 - smoothstep(0.9, 1.0, ph))
			leg("Right", thigh, knee)
			leg("Left", -0.12, 0.15)
			b["Spine"].rotation.x -= sin(ph * PI) * 0.25
			if kick_t >= 1.0:
				kick_t = -1.0
	# ---- spine: lean into the run, look up/down, breathe
	var breathe := sin(_t * 1.6) * 0.015
	var lean: float = -0.12 * min(moving, 1.4) - c * 0.25
	b["Spine"].rotation.x = -lean * 0.5 + breathe
	b["Chest"].rotation.x = -aim_pitch * 0.25 * _aim_amt
	b["UpperChest"].rotation.x = -aim_pitch * 0.25 * _aim_amt
	b["Neck"].rotation.x = -aim_pitch * (0.5 - 0.5 * _aim_amt) * 0.5
	b["Head"].rotation.x = -aim_pitch * (0.5 - 0.25 * _aim_amt)
	# ---- arms
	var out := 1.0
	if mode == "work":
		var wob := sin(_t * 5.0) * 0.04
		reach("Right", work_target + Vector3(-0.12, wob, 0), Vector3(-1, -1, -0.3))
		reach("Left", work_target + Vector3(0.12, -wob, 0), Vector3(1, -1, -0.3))
		if weapon:
			_place_weapon_slung()
		if held:
			held.position = model.to_local(b["RightHand"].global_position)
			held.rotation = Vector3(-0.6, 0, 0)
		return
	if mode == "carry":
		reach("Right", Vector3(-0.2, 1.05, 0.33), Vector3(-1, -1, -0.5))
		reach("Left", Vector3(0.2, 1.05, 0.33), Vector3(1, -1, -0.5))
		if held:
			held.position = Vector3(0, 1.08, 0.36)
			held.rotation = Vector3.ZERO
		if weapon:
			_place_weapon_slung()
		return
	if twitch > 0.0:
		# a slow, wrong-feeling sway, and every few seconds one sharp jerk that eases back
		_jerk_t -= dt
		if _jerk_t <= 0.0:
			_jerk_t = randf_range(2.0, 5.0)
			_jerk = Vector3(randf_range(-0.5, 0.5), randf_range(-0.7, 0.7), randf_range(-0.4, 0.4))
		_jerk = _jerk.lerp(Vector3.ZERO, clampf(dt * 3.0, 0.0, 1.0))
		b["Head"].rotation += (Vector3(sin(_t * 1.3) * 0.12, sin(_t * 0.9 + 1.0) * 0.18, sin(_t * 1.7 + 2.0) * 0.1) + _jerk) * twitch
		b["Spine"].rotation.z += sin(_t * 13.0) * 0.08 * twitch
	if throw_t >= 0.0:
		throw_t += dt * 2.2
		var ang: float = lerpf(-0.6, 2.4, clamp(throw_t, 0.0, 1.0))
		aim_bone("RightUpperArm", Vector3(-0.3, sin(ang - 1.0) * 1.0 + 0.3, -cos(ang) * 0.8))
		aim_bone("RightLowerArm", Vector3(-0.1, 0.9, 0.2 + throw_t))
		if throw_t >= 1.0:
			throw_t = -1.0
	if weapon:
		var hip := Vector3(-0.14, 1.12 - c * 0.38, 0.30)
		var shoulder := Vector3(-0.11, 1.44 - c * 0.40, 0.22)
		if first_person:                      # viewmodel: low and to the right, the muzzle well out of the way
			shoulder = Vector3(-0.22, 1.40 - c * 0.40, 0.42)
			hip = Vector3(-0.24, 1.30 - c * 0.38, 0.40)
		var p := hip.lerp(shoulder, _aim_amt)
		if first_person and ads:                # bring the sight onto the eye line, centred
			var eye_y: float = rest_model.get("Head", Vector3(0, 1.7, 0)).y + 0.11 - c * 0.42
			var sight: Vector3 = model.to_local(wm["Sight"].global_position) - model.to_local(weapon.global_position) if wm.has("Sight") else Vector3(0, 0.15, 0.1)
			p = Vector3(-sight.x, eye_y - sight.y - 0.015, 0.42 - sight.z)
		var pitch := lerpf(-0.45, aim_pitch, _aim_amt)
		recoil = move_toward(recoil, 0.0, dt * 9.0)
		weapon.position = p + Vector3(0, recoil * 0.015, -recoil * 0.07)
		weapon.rotation = Vector3(-pitch - recoil * 0.09, 0.0, 0.0)
		if mode == "kneel":
			weapon.position.y -= 0.45
		var rl := reload
		if rl >= 0.0:                                   # tilt the gun to show the mag well
			var tilt := sin(clampf(rl, 0.0, 1.0) * PI)
			weapon.rotation.z = tilt * 0.55
			weapon.rotation.x += tilt * 0.25
		var grip: Vector3 = model.to_local(wm["Grip"].global_position) if wm.has("Grip") else p
		var sup: Vector3 = model.to_local(wm["SupportHand"].global_position) if wm.has("SupportHand") else p + Vector3(0, 0, 0.3)
		reach("Right", grip + Vector3(0, 0.03, -0.05), Vector3(-1.0, -1.2, -0.6))
		if rl >= 0.0:
			_reload_hand(rl, sup)
		else:
			reach("Left", sup + Vector3(0, 0.02, 0), Vector3(1.0, -1.0, -0.4))
			if wm.has("Mag"):
				wm["Mag"].visible = true
			if _hand_mag:
				_hand_mag.visible = false
	elif mode == "kneel":
		reach("Right", Vector3(-0.15, 0.45, 0.55), Vector3(-1, 0, -1))
		reach("Left", Vector3(0.15, 0.45, 0.55), Vector3(1, 0, -1))
	else:
		var swing: float = sin(_phase) * 0.45 * min(moving, 1.2)
		aim_bone("LeftUpperArm", Vector3(0.18, -1.0, -swing))
		aim_bone("LeftLowerArm", Vector3(0.1, -1.0, 0.25 - swing * 0.5))
		aim_bone("RightUpperArm", Vector3(-0.18, -1.0, swing))
		aim_bone("RightLowerArm", Vector3(-0.1, -1.0, 0.25 + swing * 0.5))
		if held:
			held.position = model.to_local(b["RightHand"].global_position) + Vector3(0, -0.05, 0.05)
			held.rotation = Vector3(-PI / 2, 0, 0)


## Left hand during a reload: pull the mag, fetch a fresh one from the chest rig, seat it.
func _reload_hand(rl: float, sup: Vector3) -> void:
	var well: Vector3 = model.to_local(wm["MagWell"].global_position) if wm.has("MagWell") else sup
	var chest := Vector3(0.02, 1.36 - _crouch_amt * 0.38, 0.2)
	var hand: Vector3
	if rl < 0.2:
		hand = sup.lerp(well, rl / 0.2)
	elif rl < 0.5:
		hand = well.lerp(chest, (rl - 0.2) / 0.3)
	elif rl < 0.8:
		hand = chest.lerp(well, (rl - 0.5) / 0.3)
	else:
		hand = well.lerp(sup, (rl - 0.8) / 0.2)
	reach("Left", hand, Vector3(1.0, -1.0, -0.2))
	var mag_out := rl > 0.18 and rl < 0.8
	if wm.has("Mag"):
		wm["Mag"].visible = not mag_out
	if _hand_mag:
		_hand_mag.visible = mag_out and not (rl > 0.38 and rl < 0.5)   # old one dropped, new one grabbed
		_hand_mag.position = model.to_local(b["LeftHand"].global_position) + Vector3(0, -0.06, 0.04)
		_hand_mag.rotation = Vector3.ZERO


func _place_weapon_slung() -> void:
	weapon.position = Vector3(0.0, 1.35, -0.22)
	weapon.rotation = Vector3(0, 0, 0.9)


func _lying(dead: bool) -> void:
	model.rotation = Vector3(-PI / 2, 0, 0)          # on its back, head toward -Z of the model
	model.position = Vector3(0, 0.22, 0)
	var flop := 0.0 if dead else sin(_t * 2.0) * 0.08
	aim_bone("LeftUpperArm", Vector3(1.0, -0.2 + flop, 0.5))
	aim_bone("LeftLowerArm", Vector3(0.6, -0.4, 0.8))
	aim_bone("RightUpperArm", Vector3(-1.0, -0.3, 0.6 + flop))
	aim_bone("RightLowerArm", Vector3(-0.5, -0.6, 0.6))
	leg("Left", 0.15, 0.3 if not dead else 0.0)
	leg("Right", -0.05, 0.1)
	if weapon:
		weapon.position = Vector3(-0.55, 0.9, 0.2)
		weapon.rotation = Vector3(0.3, 1.2, 0)
