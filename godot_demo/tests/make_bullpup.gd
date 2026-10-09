extends SceneTree
## Builds the bullpup battle rifle from primitives (there's no Blender in the container):
##   godot --headless --path . -s res://tests/make_bullpup.gd
## Writes res://models/weapons/weapon_F1_BattleRifle.tscn and weapon_P_BattleRifle.tscn, using
## the colours of the old battle rifle .glb of the same faction. character.give_weapon prefers
## a .tscn over the .glb when both exist.
##
## Godot axes: +z toward the muzzle, +y up. The grip sits at the origin like every other gun;
## the magazine goes in behind it (a bullpup), so the whole gun is only about 0.75 m long.
## The Sight marker sits on top of a plain mount on the rail; the first-person holo sight is
## added there by viewmodel.gd.

const MATS := ["WBody", "WAccent", "WDark", "Optic", "WPanel"]

var _st := {}                    # material name -> SurfaceTool


func _init() -> void:
	for tag in ["F1", "P"]:
		_save(tag)
	print("BULLPUP DONE")
	quit()


func _save(tag: String) -> void:
	var src: Node = load("res://models/weapons/weapon_%s_BattleRifle.glb" % tag).instantiate()
	var body_src: MeshInstance3D = src.find_child("Body", true, false)
	var mats := {}
	for i in body_src.mesh.get_surface_count():
		var m: Material = body_src.mesh.surface_get_material(i).duplicate()
		mats[m.resource_name.trim_prefix("C1_")] = m
	src.free()

	var root := Node3D.new()
	root.name = "weapon_%s_BattleRifle" % tag
	var body := MeshInstance3D.new()
	body.name = "Body"
	body.mesh = _body(mats)
	root.add_child(body)
	body.owner = root
	var mag := MeshInstance3D.new()
	mag.name = "Mag"
	mag.mesh = _mag(mats)
	mag.position = Vector3(0, -0.01, -0.165)          # the mesh is built around its own top centre
	mag.rotation.x = deg_to_rad(-8.0)                 # canted back a little, like the grip
	root.add_child(mag)
	mag.owner = root
	var marks := {"Grip": Vector3(0, -0.06, -0.01), "SupportHand": Vector3(0, 0.0, 0.29),
		"Muzzle": Vector3(0, 0.05, 0.42), "Sight": Vector3(0, 0.12, 0.05), "MagWell": Vector3(0, -0.02, -0.165)}
	for k in marks:
		var n := Node3D.new()
		n.name = k
		n.position = marks[k]
		root.add_child(n)
		n.owner = root
	var ps := PackedScene.new()
	ps.pack(root)
	var path := "res://models/weapons/weapon_%s_BattleRifle.tscn" % tag
	var err := ResourceSaver.save(ps, path)
	print("saved ", path, " ", error_string(err))
	root.free()


# ------------------------------------------------------------------ the gun

func _body(mats: Dictionary) -> ArrayMesh:
	_begin()
	# receiver: the full-length body, taller at the back where the action sits
	_box("WBody", Vector3(-0.035, -0.005, -0.30), Vector3(0.035, 0.09, 0.18))
	_box("WBody", Vector3(-0.036, -0.075, -0.33), Vector3(0.036, -0.005, -0.09))
	_box("WPanel", Vector3(-0.03, 0.09, -0.31), Vector3(0.03, 0.105, -0.13))          # cheek rest
	_box("WDark", Vector3(-0.038, -0.08, -0.345), Vector3(0.038, 0.1, -0.33))          # butt pad
	_box("WAccent", Vector3(0.035, 0.03, -0.24), Vector3(0.038, 0.06, -0.15))          # ejection port
	_box("WAccent", Vector3(-0.038, 0.03, -0.24), Vector3(-0.035, 0.06, -0.15))        # (ambidextrous)
	_box("WDark", Vector3(-0.031, -0.085, -0.215), Vector3(0.031, -0.075, -0.115))     # mag well lip
	# pistol grip and trigger
	_box("WDark", Vector3(-0.018, -0.14, -0.035), Vector3(0.018, 0.0, 0.025), Basis(Vector3.RIGHT, deg_to_rad(-14.0)), Vector3(0, -0.005, -0.005))
	_box("WDark", Vector3(-0.006, -0.065, 0.025), Vector3(0.006, -0.055, 0.115))        # trigger guard
	_box("WDark", Vector3(-0.006, -0.065, 0.105), Vector3(0.006, -0.005, 0.115))
	_box("WDark", Vector3(-0.004, -0.05, 0.045), Vector3(0.004, -0.01, 0.055))          # trigger
	# shroud over the short barrel, vented
	_box("WBody", Vector3(-0.036, -0.03, 0.18), Vector3(0.036, 0.08, 0.36))
	for i in 4:
		var z := 0.205 + i * 0.038
		for sx in [-1.0, 1.0]:
			var x0: float = sx * 0.036
			var x1: float = sx * 0.039
			_box("WDark", Vector3(minf(x0, x1), 0.02, z), Vector3(maxf(x0, x1), 0.055, z + 0.022))
	_box("WAccent", Vector3(-0.037, -0.031, 0.345), Vector3(0.037, 0.081, 0.36))       # front band
	_box("WDark", Vector3(-0.03, -0.045, 0.2), Vector3(0.03, -0.03, 0.34))             # hand stop rail
	_box("WDark", Vector3(-0.045, 0.05, 0.12), Vector3(-0.035, 0.07, 0.16))            # charging handle
	_cyl("WDark", Vector3(0, 0.05, 0.36), 0.012, 0.03)                                 # barrel
	_cyl("WDark", Vector3(0, 0.05, 0.375), 0.019, 0.045)                               # flash hider
	# top rail and a sight mount: viewmodel.gd puts its own holo sight on top of the mount
	# (on the Sight marker), as it does for every rifle, so the model has no sight of its own
	_box("WDark", Vector3(-0.015, 0.09, -0.12), Vector3(0.015, 0.103, 0.3))
	_box("WDark", Vector3(-0.022, 0.103, 0.0), Vector3(0.022, 0.12, 0.09))
	return _commit(mats)


func _mag(mats: Dictionary) -> ArrayMesh:
	_begin()
	_box("WPanel", Vector3(-0.02, -0.17, -0.034), Vector3(0.02, 0.0, 0.034))
	_box("WDark", Vector3(-0.022, -0.185, -0.037), Vector3(0.022, -0.17, 0.037))       # base plate
	return _commit(mats)


# ------------------------------------------------------------------ mesh helpers

func _begin() -> void:
	_st.clear()


func _tool(mat: String) -> SurfaceTool:
	if not _st.has(mat):
		var st := SurfaceTool.new()
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
		_st[mat] = st
	return _st[mat]


func _quad(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, d: Vector3) -> void:
	var n := (b - a).cross(c - a).normalized()          # outward; Godot's front faces wind clockwise
	for p in [a, c, b, a, d, c]:
		st.set_normal(n)
		st.add_vertex(p)


## An axis-aligned box from lo to hi, optionally turned by basis about pivot.
func _box(mat: String, lo: Vector3, hi: Vector3, basis := Basis.IDENTITY, pivot := Vector3.ZERO) -> void:
	var st := _tool(mat)
	var c := []
	for i in 8:
		var p := Vector3(hi.x if i & 1 else lo.x, hi.y if i & 2 else lo.y, hi.z if i & 4 else lo.z)
		c.append(basis * (p - pivot) + pivot)
	# each quad listed counter-clockwise seen from outside (_quad flips it)
	_quad(st, c[0], c[2], c[3], c[1])     # -z
	_quad(st, c[4], c[5], c[7], c[6])     # +z
	_quad(st, c[0], c[4], c[6], c[2])     # -x
	_quad(st, c[1], c[3], c[7], c[5])     # +x
	_quad(st, c[0], c[1], c[5], c[4])     # -y
	_quad(st, c[2], c[6], c[7], c[3])     # +y


## A cylinder along +z from start, with end caps.
func _cyl(mat: String, start: Vector3, r: float, length: float, seg := 12) -> void:
	var st := _tool(mat)
	var e := start + Vector3(0, 0, length)
	for i in seg:
		var a0 := TAU * i / seg
		var a1 := TAU * (i + 1) / seg
		var o0 := Vector3(cos(a0), sin(a0), 0) * r
		var o1 := Vector3(cos(a1), sin(a1), 0) * r
		_quad(st, start + o0, start + o1, e + o1, e + o0)
		for p in [[e, e + o0, e + o1], [start, start + o1, start + o0]]:
			var n: Vector3 = (p[1] - p[0]).cross(p[2] - p[0]).normalized()
			for v in [p[0], p[2], p[1]]:
				st.set_normal(n)
				st.add_vertex(v)


func _commit(mats: Dictionary) -> ArrayMesh:
	var mesh := ArrayMesh.new()
	for k in MATS:
		if _st.has(k):
			var st: SurfaceTool = _st[k]
			st.set_material(mats[k])
			st.commit(mesh)
	return mesh
