extends RefCounted
## Cargo you can see: a ship's hold carries one labelled crate per 10 units of each good,
## stacked in racks by the CargoStorage markers. Labels on all four sides, so a crate reads
## from the aisle and from either side whether it sits against a wall or in the middle.

const COLORS := {"ore": Color(0.45, 0.36, 0.3), "fuel": Color(0.75, 0.55, 0.2), "tritium": Color(0.3, 0.75, 0.85),
	"food": Color(0.45, 0.6, 0.35), "alloys": Color(0.55, 0.58, 0.62), "munitions": Color(0.5, 0.45, 0.25),
	"medical": Color(0.85, 0.85, 0.88), "electronics": Color(0.3, 0.4, 0.6), "luxuries": Color(0.6, 0.35, 0.6),
	"circuitry": Color(0.25, 0.5, 0.45)}


static func refresh(v: Node, cargo: Dictionary) -> void:
	var want := ""
	var keys: Array = cargo.keys()
	keys.sort()
	for g in keys:
		want += "%s:%d;" % [g, int(cargo[g]) / 10 + (1 if int(cargo[g]) % 10 > 0 else 0)]
	if v.get_meta("cargo_sig", "") == want:
		return
	v.set_meta("cargo_sig", want)
	var old: Node = v.get_node_or_null("CargoCrates")
	if old:
		old.free()
	var root := Node3D.new()
	root.name = "CargoCrates"
	v.add_child(root)
	var spots: Array = v.marks_like("CargoStorage_*")
	if spots.is_empty():
		return
	var i := 0
	for g in keys:
		var n: int = int(cargo[g]) / 10 + (1 if int(cargo[g]) % 10 > 0 else 0)
		for k in n:
			var base: Vector3 = v.local_of(spots[(i / 6) % spots.size()])
			var slot := i % 6
			var p := base + Vector3((slot % 3 - 1) * 1.3, 0.55 + float(slot / 3) * 1.12 + 1.15 * float(i / (6 * spots.size())), 0)
			_crate(root, p, g)
			i += 1
			if i >= 6 * spots.size() * 2:
				return                                 # the racks are full (the rest is stowed deeper)


static func _crate(root: Node3D, p: Vector3, good: String) -> void:
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(1.2, 1.05, 1.2)
	mi.mesh = bm
	var m := StandardMaterial3D.new()
	m.albedo_color = COLORS.get(good, Color(0.5, 0.5, 0.5))
	m.roughness = 0.7
	mi.material_override = m
	mi.position = p
	root.add_child(mi)
	for k in 4:
		var l := Label3D.new()
		l.text = good.to_upper()
		l.font_size = 48
		l.pixel_size = 0.004
		l.outline_size = 6
		l.modulate = Color(0.95, 0.95, 0.9)
		var ang := k * PI * 0.5
		l.position = Vector3(sin(ang), 0, cos(ang)) * 0.61
		l.rotation.y = ang
		mi.add_child(l)
