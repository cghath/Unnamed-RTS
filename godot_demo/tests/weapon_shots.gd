extends Node
## First-person weapon pictures:  godot --path . res://match.tscn -- --weaponshots <folder>
## Each gun type: at the hip looking level, up and down; aimed down the sights.

var out := ""
var t := 0.0
var c: Node
var shots: Array = []
var i := 0
var wait := 0.0


func _ready() -> void:
	out = OS.get_cmdline_user_args()[-1]
	DirAccess.make_dir_recursive_absolute(out)
	for m in ["F1_AssaultRifle", "F1_Magnum", "F1_BattleRifle", "F1_Sniper", "F2_PlasmaRifle", "F1_Shotgun"]:
		for pose in ["hip", "up", "down", "ads"]:
			shots.append([m, pose])
	shots.append(["F1_AssaultRifle", "reload"])
	shots.append(["F1_AssaultRifle", "sprint"])


func _physics_process(dt: float) -> void:
	t += dt
	if t < 3.0:
		return
	if c == null:
		for v in G.vessels:
			if v.get_meta("slot", "") == "flag1":
				for o in v.occupants:
					if o.role == "rifleman" and o.state == "alive":
						c = o
						break
		G.match_node.ai.attack_after = 99999.0
		G.commander.possess(c)
		G.commander._help = false
		G.commander.hud.show_help(false)
		# stand them in a hangar looking down its length (room to see)
		var pads: Array = c.vessel.marks_like("Hangar_ShuttlePad")
		if not pads.is_empty():
			c.position = c.vessel.snap_local(c.vessel.local_of(pads[0]) + Vector3(0, 0, 9))
		c.look_yaw = 0.0
		return
	if busy:
		return
	if wait > 0.0:
		wait -= dt
		# hold the pose every frame (the player code would otherwise reset it)
		_pose()
		if wait <= 0.0:
			busy = true
			_snap()
		return
	if i >= shots.size():
		get_tree().quit()
		return
	if c.weapon_model != shots[i][0]:
		c.give_weapon(shots[i][0])
	_pose()
	wait = 1.4


var busy := false


func _pose() -> void:
	var s: Array = shots[i]
	c.set_meta("force_ads", s[1] == "ads")
	c.look_pitch = {"up": 0.95, "down": -0.95}.get(s[1], 0.0)
	if s[1] == "reload" and c.reload_t < 0.5:
		c.reload_t = 1.2


func _snap() -> void:
	await RenderingServer.frame_post_draw
	if i >= shots.size():
		return
	var s: Array = shots[i]
	get_viewport().get_texture().get_image().save_png("%s/%02d_%s_%s.png" % [out, i, s[0], s[1]])
	print("SHOT ", s[0], " ", s[1])
	i += 1
	busy = false
