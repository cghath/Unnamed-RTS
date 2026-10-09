extends Control
## Campaign screens on top of the HUD:
##   the company chip (credits, stores, system) under the top bar
##   O  galaxy map: the systems, the lanes between them, who holds what, your jobs;
##      pick a neighbouring system and JUMP (your selected ships fly to the gate)
##   P  station services, at the station nearest your selected ship: trade, jobs,
##      repairs and resupply, hiring boarders; at your own station, move cargo to stores

const GALAXY := preload("res://scripts/campaign/galaxy.gd")
const BG := Color(0.03, 0.045, 0.07, 0.95)
const EDGE := Color(0.33, 0.52, 0.72, 0.55)
const TEXT := Color(0.88, 0.92, 0.96)
const DIM := Color(0.56, 0.63, 0.71)
const ACCENT := Color(0.45, 0.8, 1.0)
const GOOD := Color(0.45, 0.95, 0.55)
const WARN := Color(1.0, 0.45, 0.35)
const SERVICE_RANGE := 900.0
const REGION_COL := {"vanguard": Color(0.35, 0.6, 1.0), "ascendancy": Color(1.0, 0.35, 0.3), "free": Color(0.75, 0.75, 0.7),
	"infected": Color(0.8, 0.4, 1.0)}

var cmd: Node
var chip: Label
var map_panel: PanelContainer
var map_view: Control
var map_info: Label
var jump_btn: Button
var map_pick := -1
var svc_panel: PanelContainer
var svc_title: Label
var svc_sub: Label
var svc_body: VBoxContainer
var svc_tab := "trade"
var svc_msg: Label
var _ship: Node = null
var _station: Node = null
var _chip_t := 0.0
var base_panel: PanelContainer
var base_list: VBoxContainer
var ghost_yaw := 0.0
var menu_bar: Control
var crew_panel: PanelContainer
var crew_list: VBoxContainer
var zone_panel: PanelContainer
var zone_list: VBoxContainer


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	chip = Label.new()
	chip.position = Vector2(12, 40)
	chip.add_theme_font_size_override("font_size", 13)
	chip.add_theme_color_override("font_color", TEXT)
	chip.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.8))
	chip.add_theme_constant_override("outline_size", 4)
	add_child(chip)
	_build_map()
	_build_services()
	_build_build()
	base_panel = _panel(Vector2(760, 520))
	var bv := VBoxContainer.new()
	bv.add_theme_constant_override("separation", 6)
	base_panel.add_child(bv)
	_label(bv, "OUTPOSTS  ·  found and build your own bases on this world", 16)
	_label(bv, "Found one at an open base location or the landing zone, then place structures within 150 m of its command post. R rotates, Shift keeps placing, right-click cancels.", 12, DIM)
	var bsc := ScrollContainer.new()
	bsc.custom_minimum_size = Vector2(740, 400)
	bv.add_child(bsc)
	base_list = VBoxContainer.new()
	base_list.add_theme_constant_override("separation", 5)
	bsc.add_child(base_list)
	_button(bv, "CLOSE", func(): base_panel.visible = false)
	crew_panel = _panel(Vector2(900, 520))
	var cv := VBoxContainer.new()
	cv.add_theme_constant_override("separation", 6)
	crew_panel.add_child(cv)
	_label(cv, "CREW  ·  who's aboard each of your ships here", 16)
	_label(cv, "Hire specialists (%d cr each) or send people ashore. Changes stay with the ship." % CREW_COST, 12, DIM)
	var csc := ScrollContainer.new()
	csc.custom_minimum_size = Vector2(880, 420)
	cv.add_child(csc)
	crew_list = VBoxContainer.new()
	crew_list.add_theme_constant_override("separation", 8)
	csc.add_child(crew_list)
	_button(cv, "CLOSE", func(): crew_panel.visible = false)
	zone_panel = _panel(Vector2(620, 420))
	var zv := VBoxContainer.new()
	zv.add_theme_constant_override("separation", 6)
	zone_panel.add_child(zv)
	_label(zv, "ZONES  ·  where your ships, stations and ground forces are", 16)
	_label(zv, "Go to one to command there. Everywhere else waits as you left it.", 12, DIM)
	zone_list = VBoxContainer.new()
	zone_list.add_theme_constant_override("separation", 4)
	zv.add_child(zone_list)
	_button(zv, "CLOSE", func(): zone_panel.visible = false)
	var bar := HFlowContainer.new()                  # wraps onto a second row on a narrow window
	bar.position = Vector2(12, 62)
	bar.size = Vector2(get_viewport_rect().size.x - 24.0, 28)
	bar.add_theme_constant_override("h_separation", 4)
	bar.add_theme_constant_override("v_separation", 4)
	bar.mouse_filter = Control.MOUSE_FILTER_PASS
	add_child(bar)
	menu_bar = bar
	for b in [["SHIPS", func(): toggle_build("ships")], ["UNITS (I)", func(): toggle_build("units")],
			["STATION (G)", func(): toggle_build("station")], ["RESEARCH (Y)", func(): cmd.hud.toggle_research()],
			["MAP (O)", toggle_map], ["SERVICES (P)", toggle_services], ["ZONES (Z)", toggle_zones], ["CREW (C)", toggle_crew], ["OUTPOST (N)", toggle_base]]:
		_button(bar, b[0], b[1])


func _style(bg: Color = BG) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = bg
	sb.border_color = EDGE
	sb.set_border_width_all(1)
	sb.set_corner_radius_all(4)
	sb.content_margin_left = 14
	sb.content_margin_right = 14
	sb.content_margin_top = 10
	sb.content_margin_bottom = 10
	return sb


func _label(parent: Node, text: String, size: int = 13, col: Color = TEXT) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", col)
	parent.add_child(l)
	return l


func _button(parent: Node, text: String, cb: Callable, w: float = 0.0) -> Button:
	var b := Button.new()
	b.text = text
	b.focus_mode = Control.FOCUS_NONE
	b.add_theme_font_size_override("font_size", 12)
	if w > 0.0:
		b.custom_minimum_size.x = w
	b.pressed.connect(cb)
	parent.add_child(b)
	return b


func _panel(sz: Vector2) -> PanelContainer:
	var p := PanelContainer.new()
	p.add_theme_stylebox_override("panel", _style())
	p.custom_minimum_size = sz
	p.set_anchors_preset(Control.PRESET_CENTER)
	p.position = -sz * 0.5
	p.visible = false
	p.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(p)
	return p


func _process(dt: float) -> void:
	_chip_t -= dt
	if _chip_t <= 0.0:
		_chip_t = 0.5
		_update_chip()
		if svc_panel.visible:
			_refresh_header()
		if map_panel.visible:
			map_view.queue_redraw()
	# keep the panels centred when the window changes
	if placing != "":
		_update_ghost()
	var vp := get_viewport_rect().size
	var top: float = menu_bar.position.y + menu_bar.size.y + 8.0 if menu_bar else 96.0
	for p in [map_panel, svc_panel, build_panel, crew_panel, base_panel]:
		if p.visible:
			p.position = Vector2(maxf(8.0, (vp.x - p.size.x) * 0.5), maxf(top, (vp.y - p.size.y) * 0.5))
	if zone_panel.visible:
		# against the left edge, in its upper middle
		zone_panel.position = Vector2(8.0, maxf(top, vp.y * 0.38 - zone_panel.size.y * 0.5))
	if menu_bar:
		menu_bar.size.x = maxf(200.0, vp.x - 24.0)


func _update_chip() -> void:
	var c = G.campaign
	if c == null:
		return
	var r: Dictionary = c.stores
	chip.text = "%s   ·   %s cr   ·   ore %d (+%d alloys/min)   crystal %d (+%d circuitry/min)   fuel %d   tritium %d   ·   %s   ·   jobs %d" % [c.company, _num(c.credits),
		int(r.get("ore", 0.0)), int(c.get_meta("alloy_rate", 0.0)), int(r.get("crystal", 0.0)), int(c.get_meta("circ_rate", 0.0)), int(r.get("fuel", 0.0)), int(r.get("tritium", 0.0)), c.system()["name"], c.jobs.size()]


func _num(n: int) -> String:
	var s := str(n)
	var out := ""
	while s.length() > 3:
		out = "," + s.substr(s.length() - 3) + out
		s = s.substr(0, s.length() - 3)
	return s + out


const OUTPOSTS := preload("res://scripts/campaign/outposts.gd")


func toggle_base() -> void:
	base_panel.visible = not base_panel.visible
	if not base_panel.visible:
		return
	map_panel.visible = false
	svc_panel.visible = false
	crew_panel.visible = false
	zone_panel.visible = false
	_refresh_base()


func _refresh_base() -> void:
	for ch in base_list.get_children():
		ch.queue_free()
	var m: Node = G.match_node
	if not m.on_surface or m.ground == null:
		_label(base_list, "Land on a world first: outposts are built on the ground.", 13, DIM)
		return
	_label(base_list, "LOCATIONS", 13, TEXT)
	for st in OUTPOSTS.sites(m):
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 8)
		base_list.add_child(row)
		_label(row, "%s   ·   %s" % [st["name"], {"open": "open", "ours": "YOUR OUTPOST", "held": "held by others (clear it first)"}[st["state"]]], 12,
			GOOD if st["state"] == "ours" else (TEXT if st["state"] == "open" else DIM))
		var sd: Dictionary = st
		if st["state"] == "open":
			_button(row, "FOUND OUTPOST (600 alloys, 150 circuitry)", func():
				cmd.log_event(OUTPOSTS.found(G.match_node, sd), 1)
				cmd.pivot = sd["pos"]
				_refresh_base())
		_button(row, "VIEW", func():
			var pp: Vector3 = sd["pos"]
			cmd.pivot = Vector3(pp.x, G.match_node.ground_y(pp.x, pp.z), pp.z))
	if OUTPOSTS.hqs(m).is_empty():
		return
	_label(base_list, "BUILD  (click one, then click the ground near a command post)", 13, TEXT)
	for type in OUTPOSTS.STRUCTS:
		if type == "hq":
			continue
		var spec: Dictionary = OUTPOSTS.STRUCTS[type]
		var tt: String = type
		_button(base_list, "%s   ·   %d alloys%s" % [spec["label"], spec["alloys"], "" if int(spec["circuitry"]) == 0 else ", %d circuitry" % spec["circuitry"]],
			func(): _start_ground_placing(tt), 720.0).alignment = HORIZONTAL_ALIGNMENT_LEFT


func _start_ground_placing(type: String) -> void:
	placing = "g:" + type
	base_panel.visible = false
	if _ghost == null:
		_ghost = MeshInstance3D.new()
		var gm := StandardMaterial3D.new()
		gm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		gm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		_ghost.material_override = gm
		G.match_node.add_child(_ghost)
	var bm := BoxMesh.new()
	bm.size = OUTPOSTS.STRUCTS[type]["size"]
	_ghost.mesh = bm
	_ghost.visible = true
	cmd.log_event("Placing: %s. Click the ground, R rotates, right-click cancels." % String(OUTPOSTS.STRUCTS[type]["label"]).get_slice(" (", 0), 1)


func _update_ground_ghost() -> void:
	var mp := get_viewport().get_mouse_position()
	var from: Vector3 = cmd.cam.project_ray_origin(mp)
	var dir: Vector3 = cmd.cam.project_ray_normal(mp)
	var h := G.ray(from, from + dir * 12000.0, [], G.LAYER_WORLD)
	if h.is_empty():
		return
	var p: Vector3 = h.position
	var type: String = placing.substr(2)
	_ghost_p = p
	_ghost_ok = OUTPOSTS.can_place(G.match_node, type, p) == ""
	var sz: Vector3 = OUTPOSTS.STRUCTS[type]["size"]
	_ghost.global_position = Vector3(p.x, G.match_node.ground_y(p.x, p.z) + sz.y * 0.5, p.z)
	_ghost.rotation.y = ghost_yaw
	(_ghost.material_override as StandardMaterial3D).albedo_color = Color(0.3, 1.0, 0.5, 0.45) if _ghost_ok else Color(1.0, 0.3, 0.25, 0.45)


const CREW_COST := 150
const CREW_ROLES := ["engineer", "scientist", "medic", "medical_officer", "security", "pilot", "cargo_handler"]


func toggle_crew() -> void:
	crew_panel.visible = not crew_panel.visible
	if crew_panel.visible:
		map_panel.visible = false
		svc_panel.visible = false
		zone_panel.visible = false
		_refresh_crew()


func _refresh_crew() -> void:
	for ch in crew_list.get_children():
		ch.queue_free()
	var any := false
	for v in G.vessels:
		if not is_instance_valid(v) or v.destroyed or v.team != 1 or v.kind != "ship" or not v.has_meta("fleet_id"):
			continue
		any = true
		var e: Dictionary = G.campaign.fleet_entry(int(v.get_meta("fleet_id")))
		var counts := {}
		var total := 0
		for o in v.occupants:
			if is_instance_valid(o) and o.team == 1 and o.state == "alive":
				counts[o.role] = int(counts.get(o.role, 0)) + 1
				total += 1
		var box := VBoxContainer.new()
		crew_list.add_child(box)
		_label(box, "%s   ·   %d aboard   ·   %d boarders in berths" % [v.display_name, total, v.troops], 14)
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 10)
		box.add_child(row)
		for role in CREW_ROLES:
			var cell := HBoxContainer.new()
			cell.add_theme_constant_override("separation", 2)
			row.add_child(cell)
			_label(cell, "%s %d" % [String(role).replace("_", " ").to_upper(), int(counts.get(role, 0))], 11, TEXT)
			var vv: Node = v
			var rr: String = role
			var ee: Dictionary = e
			_button(cell, "+", func(): _hire(vv, ee, rr))
			_button(cell, "−", func(): _dismiss(vv, ee, rr))
	if not any:
		_label(crew_list, "None of your ships are here.", 13, DIM)


func _hire(v: Node, e: Dictionary, role: String) -> void:
	var c = G.campaign
	if c.credits < CREW_COST:
		cmd.log_event("Not enough credits (%d needed)" % CREW_COST, 1)
		return
	if not is_instance_valid(v) or not v.nav_ok():
		return
	c.credits -= CREW_COST
	var who: Node = G.match_node.spawn_character(v, v.random_local(), 1, 1, role)
	if not e.is_empty():
		var cr: Array = load("res://scripts/campaign/sector.gd").crew_for(e)
		cr.append(role)
		e["crew"] = cr
	cmd.log_event("%s: a new %s came aboard" % [v.display_name, role.replace("_", " ")], 1)
	if who:
		_refresh_crew()


func _dismiss(v: Node, e: Dictionary, role: String) -> void:
	if not is_instance_valid(v):
		return
	for o in v.occupants:
		if is_instance_valid(o) and o.team == 1 and o.state == "alive" and o.role == role and o != G.possessed:
			G.match_node.logistics._remove_person(o)
			if not e.is_empty():
				var cr: Array = load("res://scripts/campaign/sector.gd").crew_for(e)
				cr.erase(role)
				e["crew"] = cr
			cmd.log_event("%s: a %s went ashore" % [v.display_name, role.replace("_", " ")], 1)
			_refresh_crew()
			return
	cmd.log_event("No %s aboard %s" % [role.replace("_", " "), v.display_name], 1)


## LAND: pick which of the planet's landing zones to come down at.
func toggle_landing(ships: Array) -> void:
	if zone_panel.visible:
		zone_panel.visible = false
		return
	var m: Node = G.match_node
	var ok: Array = ships.filter(func(x): return is_instance_valid(x) and x.get("kind") == "ship" and x.team == 1)
	var tgt: Array = m.landing_target(ok)
	if tgt.is_empty():
		cmd.log_event(m.land(ok) if not ok.is_empty() else "Select a ship to land", 1)
		return
	var pl: Dictionary = tgt[1]
	var c = G.campaign
	zone_panel.visible = true
	for ch in zone_list.get_children():
		ch.queue_free()
	_label(zone_list, "LAND ON %s  ·  choose a landing zone" % String(pl.get("name", "the planet")).to_upper(), 14)
	var sites: Array = pl.get("sites", [])
	for si in sites.size():
		var site: Dictionary = sites[si]
		var info := "unexplored"
		if c.world.get("seen_%d_%d_%d" % [c.current, int(tgt[0]), si], false):
			var bits: Array = []
			var keep: Dictionary = c.surface
			c.surface = {"planet": int(tgt[0]), "site": si}
			var L: Dictionary = load("res://scripts/campaign/surface.gd").layout(c)
			c.surface = keep
			for bs in L["bases"]:
				var w: Dictionary = c.world.get(bs["key"], {})
				if w.get("outpost", false):
					bits.append("your outpost")
				elif w.get("destroyed", false):
					bits.append("cleared base")
				elif int(w.get("team", {"pirate_camp": 3, "hive": 4}.get(bs["kind"], 0))) == 4:
					bits.append("infected hive")
				else:
					bits.append(String(bs["kind"]).replace("_", " ").replace("pirate camp", "outlaw camp"))
			info = ", ".join(bits)
		var nm: String = site.get("name", "Landing zone %d" % (si + 1))
		var idx: int = si
		var b := _button(zone_list, "%s   (%s)" % [nm, info], func():
			zone_panel.visible = false
			cmd.log_event(G.match_node.land(ok, idx), 1), 580.0)
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT


func toggle_zones() -> void:
	zone_panel.visible = not zone_panel.visible
	if not zone_panel.visible:
		return
	map_panel.visible = false
	svc_panel.visible = false
	for ch in zone_list.get_children():
		ch.queue_free()
	for z in G.campaign.zones():
		var bits: Array = []
		if int(z["ships"]) > 0:
			bits.append("%d ship%s" % [z["ships"], "" if int(z["ships"]) == 1 else "s"])
		if int(z["stations"]) > 0:
			bits.append("%d station%s" % [z["stations"], "" if int(z["stations"]) == 1 else "s"])
		if int(z["troops"]) > 0:
			bits.append("%d troops" % z["troops"])
		if int(z["vehicles"]) > 0:
			bits.append("%d vehicles" % z["vehicles"])
		var txt: String = "%s%s   (%s)" % ["▶ " if z["here"] else "", z["label"], ", ".join(bits)]
		var zz: Dictionary = z
		var b := _button(zone_list, txt, func():
			zone_panel.visible = false
			G.match_node.switch_zone(zz), 580.0)
		b.disabled = z["here"]
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT


func any_open() -> bool:
	return map_panel.visible or svc_panel.visible or build_panel.visible or placing != "" or (zone_panel != null and zone_panel.visible) or (crew_panel != null and crew_panel.visible) or (base_panel != null and base_panel.visible)


func close_all() -> void:
	base_panel.visible = false
	zone_panel.visible = false
	crew_panel.visible = false
	map_panel.visible = false
	svc_panel.visible = false
	build_panel.visible = false
	_stop_placing()


# ------------------------------------------------------------------ galaxy map

func _build_map() -> void:
	map_panel = _panel(Vector2(980, 640))
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 8)
	map_panel.add_child(v)
	var top := HBoxContainer.new()
	v.add_child(top)
	var t := _label(top, "GALAXY MAP", 18, ACCENT)
	t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_button(top, "CLOSE (O)", func(): map_panel.visible = false)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	v.add_child(row)
	map_view = Control.new()
	map_view.custom_minimum_size = Vector2(660, 540)
	map_view.mouse_filter = Control.MOUSE_FILTER_STOP
	map_view.draw.connect(_draw_map)
	map_view.gui_input.connect(_map_input)
	row.add_child(map_view)
	var side := VBoxContainer.new()
	side.custom_minimum_size.x = 270
	side.add_theme_constant_override("separation", 8)
	row.add_child(side)
	map_info = _label(side, "", 13)
	map_info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	map_info.custom_minimum_size.x = 270
	jump_btn = _button(side, "JUMP", _jump)
	jump_btn.visible = false


func toggle_map() -> void:
	map_panel.visible = not map_panel.visible
	svc_panel.visible = false
	if map_panel.visible:
		map_pick = G.campaign.current
		_map_text()
		map_view.queue_redraw()


func _map_xy(mp: Vector2) -> Vector2:
	var sz := map_view.size
	return Vector2(20 + mp.x / 1000.0 * (sz.x - 40), 20 + mp.y / 620.0 * (sz.y - 40))


func _draw_map() -> void:
	var c = G.campaign
	var f := get_theme_default_font()
	map_view.draw_rect(Rect2(Vector2.ZERO, map_view.size), Color(0.01, 0.015, 0.03, 0.9))
	var drawn := {}
	for s in c.galaxy["systems"]:
		for to in s["lanes"]:
			var key := "%d-%d" % [mini(s["id"], to), maxi(s["id"], to)]
			if drawn.has(key):
				continue
			drawn[key] = true
			var o: Dictionary = c.system_of(to)
			map_view.draw_line(_map_xy(s["map"]), _map_xy(o["map"]), Color(0.4, 0.55, 0.75, 0.45), 2.0)
	var job_sys := {}
	for j in c.jobs:
		if j.has("target_system"):
			job_sys[int(j["target_system"])] = true
		if j.has("to"):
			job_sys[int(String(j["to"]).get_slice("_", 0))] = true
	for s in c.galaxy["systems"]:
		var p := _map_xy(s["map"])
		var col: Color = REGION_COL[s["region"]]
		map_view.draw_circle(p, 9.0, col)
		if s["id"] == c.current:
			map_view.draw_arc(p, 15.0, 0, TAU, 32, Color(1, 1, 1, 0.9), 2.0)
		if s["id"] == map_pick:
			map_view.draw_arc(p, 20.0, 0, TAU, 32, ACCENT, 2.0)
		if job_sys.has(int(s["id"])):
			map_view.draw_rect(Rect2(p + Vector2(10, -16), Vector2(8, 8)), Color(1.0, 0.85, 0.3))
		var have := 0
		for e in c.fleet:
			if int(e["system"]) == int(s["id"]):
				have += 1
		var nm: String = s["name"] + ("  [%d ship%s]" % [have, "" if have == 1 else "s"] if have > 0 else "")
		map_view.draw_string(f, p + Vector2(-40, 26), nm, HORIZONTAL_ALIGNMENT_LEFT, -1, 12,
			TEXT if c.visited.has(int(s["id"])) else DIM)
	var y := map_view.size.y - 16
	var x := 16.0
	for k in ["vanguard", "ascendancy", "free", "infected"]:
		map_view.draw_circle(Vector2(x + 5, y - 4), 5.0, REGION_COL[k])
		map_view.draw_string(f, Vector2(x + 14, y), {"vanguard": "Vanguard", "ascendancy": "Ascendancy", "free": "Free space",
			"infected": "Infected"}[k], HORIZONTAL_ALIGNMENT_LEFT, -1, 11, DIM)
		x += 110.0
	map_view.draw_rect(Rect2(Vector2(x, y - 9), Vector2(8, 8)), Color(1.0, 0.85, 0.3))
	map_view.draw_string(f, Vector2(x + 14, y), "your jobs", HORIZONTAL_ALIGNMENT_LEFT, -1, 11, DIM)


func _map_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_LEFT:
		var best := -1
		var bd := 26.0
		for s in G.campaign.galaxy["systems"]:
			var d: float = _map_xy(s["map"]).distance_to(ev.position)
			if d < bd:
				bd = d
				best = s["id"]
		if best >= 0:
			map_pick = best
			_map_text()
			map_view.queue_redraw()


func _map_text() -> void:
	var c = G.campaign
	var s: Dictionary = c.system_of(map_pick)
	var lines: Array = [s["name"].to_upper(), {"vanguard": "Vanguard space", "ascendancy": "Ascendancy space",
		"free": "Free space (lawless)", "infected": "Quarantine: an infected world"}[s["region"]], ""]
	lines.append("Worlds:")
	for pl in s["planets"]:
		lines.append("  %s  (%s)%s" % [pl["name"], GALAXY.BIOMES[pl["biome"]]["label"],
			"  · %d landing site%s" % [pl["sites"].size(), "" if pl["sites"].size() == 1 else "s"] if not pl["sites"].is_empty() else ""])
	lines.append("Stations:")
	for st in c.stations_in(map_pick):
		lines.append("  %s  (%s)" % [st["name"], G.team_name(int(st["team"]))])
	for st in c.stations:
		if int(st["system"]) == map_pick:
			lines.append("  %s  (yours)" % st["name"])
	if s.get("pirates", false):
		lines.append("Pirates are active here.")
	var jl: Array = []
	for j in c.jobs:
		if int(j.get("target_system", -2)) == map_pick or (j.has("to") and int(String(j["to"]).get_slice("_", 0)) == map_pick):
			jl.append("  • " + j["title"])
	if not jl.is_empty():
		lines.append("")
		lines.append("Your jobs here:")
		lines += jl
	lines.append("")
	if map_pick == c.current:
		lines.append("You are here.")
		jump_btn.visible = false
	elif map_pick in c.neighbours():
		lines.append("A jump lane leads here. Select ships (or none for the whole fleet in this system), then JUMP: they fly to the gate and go through together.")
		jump_btn.visible = true
	else:
		lines.append("No direct lane: jump through the systems between.")
		jump_btn.visible = false
	map_info.text = "\n".join(lines)


func _jump() -> void:
	var ships: Array = cmd.selection.filter(func(u): return is_instance_valid(u) and u.get("kind") == "ship" and u.team == 1)
	if ships.is_empty():
		ships = G.vessels.filter(func(v): return v.kind == "ship" and v.team == 1 and not v.destroyed)
	if ships.is_empty():
		cmd.log_event("No ships to jump", 1)
		return
	if G.match_node.order_jump(ships, map_pick):
		cmd.log_event("%d ship%s heading for the gate to %s" % [ships.size(), "" if ships.size() == 1 else "s",
			G.campaign.system_of(map_pick)["name"]], 1)
		map_panel.visible = false


# ------------------------------------------------------------------ station services

func _build_services() -> void:
	svc_panel = _panel(Vector2(900, 600))
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 8)
	svc_panel.add_child(v)
	var top := HBoxContainer.new()
	v.add_child(top)
	var tv := VBoxContainer.new()
	tv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(tv)
	svc_title = _label(tv, "", 18, ACCENT)
	svc_sub = _label(tv, "", 12, DIM)
	_button(top, "CLOSE (P)", func(): svc_panel.visible = false)
	var tabs := HBoxContainer.new()
	tabs.add_theme_constant_override("separation", 6)
	v.add_child(tabs)
	for t in [["trade", "TRADE"], ["jobs", "JOBS ON OFFER"], ["mine", "YOUR JOBS"], ["services", "SERVICES"]]:
		var tt: String = t[0]
		_button(tabs, t[1], func(): svc_tab = tt; _refresh(), 150)
	svc_msg = _label(v, "", 12, GOOD)
	var sc := ScrollContainer.new()
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sc.custom_minimum_size.y = 430
	v.add_child(sc)
	svc_body = VBoxContainer.new()
	svc_body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	svc_body.add_theme_constant_override("separation", 4)
	sc.add_child(svc_body)


## Which of our ships is at which station: the selected ship, else any of ours near a station.
func _find_pair() -> bool:
	_ship = null
	_station = null
	var cands: Array = cmd.selection.filter(func(u): return is_instance_valid(u) and u.get("kind") == "ship" and u.team == 1 and not u.destroyed)
	if cands.is_empty():
		cands = G.vessels.filter(func(v): return v.kind == "ship" and v.team == 1 and not v.destroyed)
	var bd := SERVICE_RANGE
	for s in cands:
		for st in G.vessels:
			if st.kind != "station" or st.destroyed or not st.has_meta("key") or G.enemies(1, st.team):
				continue
			var d: float = s.global_position.distance_to(st.global_position)
			if d < bd:
				bd = d
				_ship = s
				_station = st
	return _ship != null


func toggle_services() -> void:
	if svc_panel.visible:
		svc_panel.visible = false
		return
	map_panel.visible = false
	if not _find_pair():
		cmd.log_event("No station close enough: bring a ship within %d m of a friendly or neutral station" % int(SERVICE_RANGE), 1)
		return
	svc_panel.visible = true
	svc_msg.text = ""
	var e := _entry()
	if not e.is_empty():
		var got: String = G.campaign.deliver(_station.get_meta("key"), e)
		if got != "":
			svc_msg.text = got.strip_edges()
	svc_tab = "trade" if G.campaign.has_market(_station.get_meta("key")) else "services"
	_refresh()


func _entry() -> Dictionary:
	if _ship == null or not is_instance_valid(_ship):
		return {}
	return G.campaign.fleet_entry(int(_ship.get_meta("fleet_id", -1)))


func _refresh_header() -> void:
	if _ship == null or not is_instance_valid(_ship) or _station == null or not is_instance_valid(_station) \
			or _ship.global_position.distance_to(_station.global_position) > SERVICE_RANGE * 1.3:
		svc_panel.visible = false
		return
	var c = G.campaign
	var e := _entry()
	svc_title.text = "%s  ·  %s" % [_station.display_name, G.team_name(_station.team)]
	svc_sub.text = "%s  ·  hold %d / %d  ·  %s cr  ·  standing %+d" % [_ship.display_name, c.cargo_used(e) if not e.is_empty() else 0,
		c.cargo_cap(e) if not e.is_empty() else 0, _num(c.credits), int(G.standing.get(_station.team, 0.0))]


func _clear() -> void:
	for ch in svc_body.get_children():
		ch.queue_free()


func _refresh() -> void:
	_refresh_header()
	_clear()
	match svc_tab:
		"trade":
			_trade_tab()
		"jobs":
			_jobs_tab()
		"mine":
			_my_jobs_tab()
		"services":
			_services_tab()


func _row() -> HBoxContainer:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 8)
	svc_body.add_child(h)
	return h


func _cell(h: Node, text: String, w: float, col: Color = TEXT) -> Label:
	var l := _label(h, text, 13, col)
	l.custom_minimum_size.x = w
	return l


func _trade_tab() -> void:
	var c = G.campaign
	var key: String = _station.get_meta("key")
	if not c.has_market(key):
		_label(svc_body, "No market here. (Your own station: see SERVICES to move cargo into its stores.)", 13, DIM)
		return
	var e := _entry()
	var h := _row()
	for t in [["GOOD", 110], ["STOCK", 70], ["BUY AT", 70], ["SELL AT", 70], ["IN HOLD", 70]]:
		_cell(h, t[0], t[1], DIM)
	for g in GALAXY.GOODS:
		var r := _row()
		var held: int = int(e.get("cargo", {}).get(g, 0))
		_cell(r, g.capitalize(), 110)
		_cell(r, str(int(c.market(key)[g])), 70, DIM)
		_cell(r, "%d" % c.price(key, g, true), 70)
		_cell(r, "%d" % c.price(key, g, false), 70, GOOD if c.price(key, g, false) > GALAXY.GOODS[g] else TEXT)
		_cell(r, str(held), 70, ACCENT if held > 0 else DIM)
		var gg: String = g
		_button(r, "Buy 1", func(): _say(c.buy(key, _entry(), gg, 1)))
		_button(r, "Buy 10", func(): _say(c.buy(key, _entry(), gg, 10)))
		_button(r, "Sell 1", func(): _say(c.sell(key, _entry(), gg, 1)))
		_button(r, "Sell all", func(): _say(c.sell(key, _entry(), gg, 9999)))


func _say(msg: String) -> void:
	svc_msg.text = msg
	svc_msg.add_theme_color_override("font_color", WARN if msg.begins_with("Can't") or msg.begins_with("No ") else GOOD)
	_refresh()


func _jobs_tab() -> void:
	var c = G.campaign
	var key: String = _station.get_meta("key")
	var offers: Array = c.offers_at(key) if c.has_market(key) else []
	if offers.is_empty():
		_label(svc_body, "Nobody here has work for you right now.", 13, DIM)
		return
	for j in offers:
		var r := _row()
		var l := _cell(r, j["title"], 600)
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		_cell(r, "%s cr" % _num(int(j["reward"])), 90, GOOD)
		var jj: Dictionary = j
		_button(r, "Accept", func(): _say(c.accept(jj)))


func _my_jobs_tab() -> void:
	var c = G.campaign
	if c.jobs.is_empty():
		_label(svc_body, "No jobs taken. Stations with a market post work on the JOBS ON OFFER tab.", 13, DIM)
		return
	for j in c.jobs:
		var r := _row()
		var extra := ""
		if j["kind"] == "patrol":
			extra = "  (%d / %d)" % [int(j.get("got", 0)), int(j["kills"])]
		var l := _cell(r, j["title"] + extra, 600)
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		_cell(r, "%s cr" % _num(int(j["reward"])), 90, GOOD)
		var jj: Dictionary = j
		_button(r, "Drop", func(): c.drop_job(jj); _say("Job dropped"))


func _services_tab() -> void:
	var c = G.campaign
	var s: Node = _ship
	var own: bool = _station.team == 1
	var missing_hull: float = s.max_hull - s.hull
	var repair_cost := int(missing_hull * (0.0 if own else 0.6))
	var r1 := _row()
	_cell(r1, "Hull %d / %d" % [int(s.hull), int(s.max_hull)], 260)
	_button(r1, "Repair (%d cr)" % repair_cost, func():
		if missing_hull <= 0.0:
			_say("No damage to repair")
		elif c.credits < repair_cost:
			_say("Can't afford the repair")
		else:
			c.credits -= repair_cost
			s.hull = s.max_hull
			s.repairs.clear()
			_say("Repaired for %d cr" % repair_cost))
	var need_sup: float = s.supply_cap - s.supplies
	var sup_cost := int(need_sup * (0.0 if own else 1.0))
	var r2 := _row()
	_cell(r2, "Supplies %d / %d" % [int(s.supplies), int(s.supply_cap)], 260)
	_button(r2, "Restock (%d cr)" % sup_cost, func():
		if c.credits < sup_cost:
			_say("Can't afford the stores")
		else:
			c.credits -= sup_cost
			s.supplies = s.supply_cap
			_say("Restocked for %d cr" % sup_cost))
	var r3 := _row()
	_cell(r3, "Boarders %d / %d" % [s.troops, s.berth_cap], 260)
	var hire := 60 if not own else 0
	_button(r3, "Hire 4 boarders (%d cr)" % (hire * 4), func():
		var n: int = mini(4, s.berth_cap - s.troops)
		if n <= 0:
			_say("The berths are full")
		elif own and _station.reserve < n:
			_say("Can't: the station's barracks has only %d ready" % _station.reserve)
		elif c.credits < hire * n:
			_say("Can't afford them")
		else:
			c.credits -= hire * n
			s.troops += n
			if own:
				_station.reserve -= n
			_say("%d boarders came aboard" % n))
	if own:
		_label(svc_body, "", 6)
		_label(svc_body, "YOUR STATION", 14, ACCENT)
		var e := _entry()
		var r4 := _row()
		_cell(r4, "Unload ore, alloys and fuel from the hold into the station's stores", 520)
		_button(r4, "Unload", func():
			var moved := 0
			for g in ["ore", "alloys", "fuel", "tritium"]:
				var n2: int = int(e.get("cargo", {}).get(g, 0))
				if n2 > 0:
					c.stores[g] = float(c.stores.get(g, 0.0)) + n2
					e["cargo"].erase(g)
					moved += n2
			_say("Moved %d units into the stores" % moved if moved > 0 else "Nothing to unload"))
		var r5 := _row()
		_cell(r5, "Load 20 refined alloys into the hold (to sell)", 520)
		_button(r5, "Load", func():
			var room: int = c.cargo_cap(e) - c.cargo_used(e)
			var n3: int = mini(20, mini(room, int(c.stores.get("alloys", 0.0))))
			if n3 <= 0:
				_say("No room or no alloys")
			else:
				c.stores["alloys"] = float(c.stores["alloys"]) - n3
				var cg: Dictionary = e.get("cargo", {})
				cg["alloys"] = int(cg.get("alloys", 0)) + n3
				e["cargo"] = cg
				_say("Loaded %d alloys" % n3))
		_label(svc_body, "Stores: %d ore · %d alloys · %d fuel · %d circuitry · %d cores" % [int(c.stores.get("ore", 0)),
			int(c.stores.get("alloys", 0)), int(c.stores.get("fuel", 0)), int(c.stores.get("circuitry", 0)), int(c.stores.get("cores", 0))], 12, DIM)
	_label(svc_body, "", 6)
	var r6 := _row()
	_cell(r6, "Save the campaign", 520)
	_button(r6, "Save", func():
		c.snapshot()
		_say("Saved" if c.save() else "Couldn't save"))


# ------------------------------------------------------------------ build (I)

const BUILDER := preload("res://scripts/campaign/builder.gd")
var build_panel: PanelContainer
var build_body: VBoxContainer
var build_msg: Label
var build_tab := "ships"
var placing := ""                   # a station segment type being placed
var _ghost: MeshInstance3D
var _ghost_ok := false
var _ghost_p := Vector3.ZERO


func _build_build() -> void:
	build_panel = _panel(Vector2(760, 560))
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 8)
	build_panel.add_child(v)
	var top := HBoxContainer.new()
	v.add_child(top)
	build_title = _label(top, "BUILD", 18, ACCENT)
	build_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_button(top, "CLOSE", func(): build_panel.visible = false)
	var tabs := HBoxContainer.new()
	tabs.add_theme_constant_override("separation", 6)
	v.add_child(tabs)
	tabs.visible = false                              # (each list is its own menu now: see the menu bar)
	build_msg = _label(v, "", 12, GOOD)
	var sc := ScrollContainer.new()
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sc.custom_minimum_size.y = 400
	v.add_child(sc)
	build_body = VBoxContainer.new()
	build_body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	build_body.add_theme_constant_override("separation", 5)
	sc.add_child(build_body)


func toggle_build(tab: String = "units") -> void:
	if build_panel.visible and build_tab == tab:
		build_panel.visible = false
		return
	build_tab = tab
	build_panel.visible = true
	map_panel.visible = false
	svc_panel.visible = false
	if build_panel.visible:
		build_msg.text = ""
		_refresh_build()


## The player's station in this system (where things get built), and its record.
func _my_station() -> Array:
	var c = G.campaign
	for e in c.stations:
		if int(e["system"]) == c.current:
			for v in G.vessels:
				if v.kind == "station" and v.get_meta("key", "") == e["key"] and not v.destroyed:
					return [v, e]
	return []


func _bmsg(m: String) -> void:
	build_msg.text = m
	build_msg.add_theme_color_override("font_color", WARN if m.begins_with("Not") or m.begins_with("Needs") or m.begins_with("The build") or m.begins_with("No ") or m.begins_with("Segments") else GOOD)
	_refresh_build()


var build_title: Label


func _refresh_build() -> void:
	build_title.text = {"ships": "SHIPYARD", "units": "UNITS: CRAFT, FIGHTERS & TROOPS", "station": "STATION CONSTRUCTION"}[build_tab]
	for ch in build_body.get_children():
		ch.queue_free()
	var ms := _my_station()
	if ms.is_empty():
		_label(build_body, "You have no station in this system. Build at your home station.", 13, DIM)
		return
	var st: Node = ms[0]
	var e: Dictionary = ms[1]
	var r: Dictionary = G.campaign.stores
	_label(build_body, "%s  ·  stores: %d alloys · %d circuitry · %d cores  ·  shipyards %d  ·  barracks %d/%d" % [e["name"],
		int(r.get("alloys", 0)), int(r.get("circuitry", 0)), int(r.get("cores", 0)), BUILDER.count_segments(e, "shipyard"),
		st.reserve, st.reserve_cap], 12, DIM)
	match build_tab:
		"ships", "units":
			for item in BUILDER.ITEMS:
				var it: Dictionary = BUILDER.ITEMS[item]
				if (it["kind"] == "ship") != (build_tab == "ships"):
					continue
				var h := HBoxContainer.new()
				h.add_theme_constant_override("separation", 8)
				build_body.add_child(h)
				var l := _label(h, it["label"], 13)
				l.custom_minimum_size.x = 260
				var cost := _label(h, "%d alloys  %d circ%s  ·  %ds%s" % [it["alloys"], it["circuitry"],
					"  %d cores" % it["cores"] if it.has("cores") else "", int(it["time"]),
					"  ·  needs %d shipyard%s" % [it["yards"], "" if it["yards"] == 1 else "s"] if it["yards"] > 0 else ""], 12, DIM)
				cost.custom_minimum_size.x = 330
				var key: String = item
				_button(h, "Build", func(): _bmsg(BUILDER.order(e, key)))
			var q: Array = e.get("queue", [])
			_label(build_body, "", 6)
			_label(build_body, "QUEUE" if not q.is_empty() else "Queue empty", 13, ACCENT)
			for qi in q:
				_label(build_body, "  %s  ·  %ds left" % [BUILDER.ITEMS[qi["item"]]["label"], int(qi["left"])], 12)
		"station":
			_label(build_body, "Pick a segment, then click next to the station or another segment: it snaps to the grid. Right-click or Esc cancels.", 12, DIM)
			for type in BUILDER.SEGMENTS:
				var sp: Dictionary = BUILDER.SEGMENTS[type]
				var h2 := HBoxContainer.new()
				h2.add_theme_constant_override("separation", 8)
				build_body.add_child(h2)
				var l2 := _label(h2, sp["label"], 13)
				l2.custom_minimum_size.x = 330
				var c2 := _label(h2, "%d alloys  %d circ  ·  built: %d" % [sp["alloys"], sp["circuitry"], BUILDER.count_segments(e, type)], 12, DIM)
				c2.custom_minimum_size.x = 230
				var tkey: String = type
				_button(h2, "Place", func(): _start_placing(tkey))


func _start_placing(type: String) -> void:
	placing = type
	build_panel.visible = false
	if _ghost == null:
		_ghost = MeshInstance3D.new()
		var m := StandardMaterial3D.new()
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		_ghost.material_override = m
		G.match_node.add_child(_ghost)
	var bm := BoxMesh.new()
	bm.size = BUILDER.SEGMENTS[type]["size"]
	_ghost.mesh = bm
	_ghost.visible = true
	cmd.log_event("Placing: %s. Click to build, right-click to cancel." % BUILDER.SEGMENTS[type]["label"], 1)


func _stop_placing() -> void:
	placing = ""
	if _ghost:
		_ghost.visible = false


func _update_ghost() -> void:
	if placing.begins_with("g:"):
		_update_ground_ghost()
		return
	var ms := _my_station()
	if ms.is_empty():
		_stop_placing()
		return
	var st: Node3D = ms[0]
	var mp := get_viewport().get_mouse_position()
	var from: Vector3 = cmd.cam.project_ray_origin(mp)
	var dir: Vector3 = cmd.cam.project_ray_normal(mp)
	var y: float = st.global_position.y
	if absf(dir.y) < 0.001:
		return
	var k: float = (y - from.y) / dir.y
	if k < 0.0:
		return
	var local: Vector3 = st.to_local(from + dir * k)
	_ghost_p = BUILDER.snap(local)
	_ghost_ok = BUILDER.spot_ok(st, ms[1], _ghost_p)
	_ghost.global_position = st.to_global(_ghost_p + Vector3(0, st.aabb.get_center().y - st.aabb.size.y * 0.25, 0))
	(_ghost.material_override as StandardMaterial3D).albedo_color = Color(0.3, 1.0, 0.5, 0.45) if _ghost_ok else Color(1.0, 0.3, 0.25, 0.45)


func place_click(ev: InputEventMouseButton) -> void:
	if ev.button_index == MOUSE_BUTTON_RIGHT:
		_stop_placing()
		return
	if ev.button_index != MOUSE_BUTTON_LEFT:
		return
	if placing.begins_with("g:"):
		cmd.log_event(OUTPOSTS.place(G.match_node, placing.substr(2), _ghost_p, ghost_yaw), 1)
		if not Input.is_key_pressed(KEY_SHIFT):
			_stop_placing()
		return
	var ms := _my_station()
	if ms.is_empty():
		_stop_placing()
		return
	var msg: String = BUILDER.place(ms[0], ms[1], placing, _ghost_p)
	cmd.log_event(msg, 1)
	if not Input.is_key_pressed(KEY_SHIFT):
		_stop_placing()                              # (hold Shift to keep placing)
