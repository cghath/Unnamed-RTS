extends RefCounted
## The campaign's galaxy: a handful of star systems joined by jump lanes, made from one seed.
##
##   generate(seed)      -> {seed, systems: [...], home}   the map: who holds what, planets,
##                          stations, asteroid fields; every system's details come from here
##   sector(galaxy, id)  -> the 3D layout of one system (positions of everything in it)
##
## Vanguard space is in the west (the player's company starts there), Ascendancy space in the
## east, pirates and free mining claims in between, and one or two worlds have been lost to
## the infection.

const NAMES := ["Kestrel", "Hale", "Morrow", "Ixion", "Seren", "Durrow", "Achen", "Vey", "Tamsin", "Calder",
	"Oris", "Varga", "Kepler", "Lumen", "Askari", "Brannoc", "Corvid", "Dace", "Elsin", "Falk", "Gyre", "Halcyon",
	"Isca", "Juno", "Karst", "Lyre", "Mire", "Nadir", "Orrin", "Pell", "Quill", "Rook", "Sabre", "Tarn", "Umber"]
const SUFFIX := ["Reach", "Drift", "Gate", "Deep", "Hollow", "Verge", "Narrows", "Crossing", "Belt", "Hold", "Rest", "Expanse"]

## Planet kinds: colours for the shader (deep / low / high / peak), and whether ships can put down there.
const BIOMES := {
	"barren": {"label": "Barren moon", "land": true, "cols": [Color(0.22, 0.21, 0.2), Color(0.38, 0.36, 0.33), Color(0.52, 0.5, 0.47), Color(0.7, 0.68, 0.65)], "sea": 0.0, "atmo": Color(0.6, 0.6, 0.65, 0.0)},
	"ice": {"label": "Ice world", "land": true, "cols": [Color(0.32, 0.45, 0.6), Color(0.62, 0.74, 0.84), Color(0.82, 0.88, 0.94), Color(0.96, 0.98, 1.0)], "sea": 0.25, "atmo": Color(0.6, 0.8, 1.0, 0.35)},
	"desert": {"label": "Desert world", "land": true, "cols": [Color(0.45, 0.3, 0.18), Color(0.7, 0.52, 0.32), Color(0.82, 0.66, 0.44), Color(0.9, 0.82, 0.66)], "sea": 0.0, "atmo": Color(1.0, 0.8, 0.55, 0.3)},
	"lava": {"label": "Volcanic world", "land": true, "cols": [Color(1.0, 0.35, 0.05), Color(0.16, 0.12, 0.11), Color(0.26, 0.2, 0.18), Color(0.35, 0.3, 0.28)], "sea": 0.32, "atmo": Color(1.0, 0.45, 0.2, 0.35)},
	"jungle": {"label": "Jungle world", "land": true, "cols": [Color(0.08, 0.2, 0.42), Color(0.16, 0.38, 0.16), Color(0.24, 0.48, 0.2), Color(0.5, 0.52, 0.4)], "sea": 0.42, "atmo": Color(0.55, 0.8, 1.0, 0.45)},
	"ocean": {"label": "Ocean world", "land": true, "cols": [Color(0.05, 0.16, 0.38), Color(0.75, 0.7, 0.55), Color(0.3, 0.5, 0.25), Color(0.85, 0.88, 0.9)], "sea": 0.68, "atmo": Color(0.5, 0.75, 1.0, 0.5)},
	"gas": {"label": "Gas giant", "land": false, "cols": [Color(0.55, 0.42, 0.3), Color(0.78, 0.65, 0.5), Color(0.62, 0.5, 0.42), Color(0.9, 0.82, 0.7)], "sea": 0.0, "atmo": Color(1.0, 0.9, 0.75, 0.4)},
	"infected": {"label": "Infected world", "land": true, "cols": [Color(0.12, 0.04, 0.16), Color(0.28, 0.12, 0.3), Color(0.42, 0.18, 0.4), Color(0.75, 0.3, 0.85)], "sea": 0.3, "atmo": Color(0.7, 0.3, 0.9, 0.45)},
}

## What each kind of station trades: the goods it makes (cheap) and the goods it needs (dear).
const ECONOMIES := {
	"mining": {"make": ["ore", "fuel", "tritium"], "need": ["food", "medical", "munitions"]},
	"industrial": {"make": ["alloys", "electronics", "munitions"], "need": ["ore", "fuel", "food"]},
	"agri": {"make": ["food", "luxuries"], "need": ["electronics", "medical", "alloys"]},
	"military": {"make": ["munitions", "tritium"], "need": ["food", "fuel", "medical", "alloys"]},
	"hub": {"make": ["medical", "electronics"], "need": ["luxuries", "ore"]},
	"pirate": {"make": ["luxuries", "munitions"], "need": ["food", "medical", "fuel"]},
}
const GOODS := {"ore": 8, "fuel": 15, "tritium": 30, "food": 12, "alloys": 22, "munitions": 35, "medical": 40, "electronics": 55, "luxuries": 90}

## Every planet and system in the sandbox stays inside this radius (metres).
const SYSTEM_R := 3400.0


static func generate(seed_: int) -> Dictionary:
	var r := RandomNumberGenerator.new()
	r.seed = seed_ * 104729 + 7
	var n := 6                                     # fewer systems, each fuller
	# places on the map (x 0..1000 west to east, y 0..620), spread out
	var pos: Array = []
	var tries := 0
	while pos.size() < n and tries < 4000:
		tries += 1
		var p := Vector2(r.randf_range(40.0, 960.0), r.randf_range(40.0, 580.0))
		if pos.size() == 0:
			p.x = r.randf_range(40.0, 120.0)             # the player's home: the far west
		if pos.size() == 1:
			p.x = r.randf_range(880.0, 960.0)            # the Ascendancy heartland: the far east
		var ok := true
		for q in pos:
			if (q as Vector2).distance_to(p) < 230.0:
				ok = false
				break
		if ok:
			pos.append(p)
	n = pos.size()
	# lanes: a spanning tree of short hops, plus a few extra so there's more than one way round
	var lanes := {}
	for i in n:
		lanes[i] = []
	var inside := [0]
	while inside.size() < n:
		var best := [-1, -1]
		var bd := 1.0e9
		for a in inside:
			for b in n:
				if b in inside:
					continue
				var d: float = (pos[a] as Vector2).distance_to(pos[b])
				if d < bd:
					bd = d
					best = [a, b]
		inside.append(best[1])
		lanes[best[0]].append(best[1])
		lanes[best[1]].append(best[0])
	for i in n:
		for j in range(i + 1, n):
			if j in lanes[i] or lanes[i].size() >= 4 or lanes[j].size() >= 4:
				continue
			if (pos[i] as Vector2).distance_to(pos[j]) < 300.0 and r.randf() < 0.45:
				lanes[i].append(j)
				lanes[j].append(i)
	# who holds what: west Vanguard, east Ascendancy, the middle free (pirates, claims)
	var used_names := {}
	var systems: Array = []
	var infected_ids: Array = []
	var far: Array = range(2, n)
	far.sort_custom(func(a, b): return absf((pos[a] as Vector2).x - 500.0) < absf((pos[b] as Vector2).x - 500.0))
	infected_ids.append(far[0])                           # one infected world near the middle...
	if n > 5 and r.randf() < 0.4:
		infected_ids.append(far[far.size() - 1])         # ...and sometimes one on the fringe
	for i in n:
		var nm := ""
		while nm == "" or used_names.has(nm):
			nm = "%s %s" % [NAMES[r.randi() % NAMES.size()], SUFFIX[r.randi() % SUFFIX.size()]]
		used_names[nm] = true
		var x: float = (pos[i] as Vector2).x
		var region := "free"
		if i == 0 or x < 330.0:
			region = "vanguard"
		elif i == 1 or x > 670.0:
			region = "ascendancy"
		if i in infected_ids:
			region = "infected"
		systems.append(_make_system(r, i, nm, pos[i], region, lanes[i], i == 0))
	# at least one pirate den in free space
	var dens := systems.filter(func(s): return s["pirates"])
	if dens.is_empty():
		for s in systems:
			if s["region"] == "free":
				s["pirates"] = true
				s["stations"].append(_pirate_den(r, s))
				break
	return {"seed": seed_, "systems": systems, "home": 0}


static func _make_system(r: RandomNumberGenerator, id: int, nm: String, mp: Vector2, region: String, lanes: Array, home: bool) -> Dictionary:
	var s := {"id": id, "name": nm, "map": mp, "region": region, "lanes": lanes.duplicate(), "seed": r.randi(),
		"planets": [], "stations": [], "pirates": false, "fields": 1 + r.randi() % 3,
		"owner": {"vanguard": 5, "ascendancy": 2, "free": 0, "infected": 4}[region],
		"nebula": Color.from_hsv(r.randf(), r.randf_range(0.4, 0.8), 1.0)}
	# planets: one to three, scaled to fit inside the system; the infected system's main world is lost
	var kinds: Array = ["barren", "ice", "desert", "lava", "jungle", "ocean", "gas"]
	var np: int = 1 + r.randi() % 3
	var ang0 := r.randf() * TAU
	for k in np:
		var biome: String = kinds[r.randi() % kinds.size()]
		if home and k == 0:
			biome = ["jungle", "ocean", "desert"][r.randi() % 3]     # somewhere worth settling
		if region == "infected" and k == 0:
			biome = "infected"
		var rad: float = r.randf_range(1050.0, 1500.0) if biome == "gas" else r.randf_range(520.0, 900.0)
		var a: float = ang0 + k * (TAU / np) + r.randf_range(-0.4, 0.4)
		var dist: float = SYSTEM_R - rad * 0.45
		var pl := {"name": "%s %s" % [nm.get_slice(" ", 0), ["I", "II", "III", "IV"][k]], "biome": biome, "radius": rad,
			"pos": Vector3(cos(a) * dist, -rad * 0.55, sin(a) * dist), "seed": r.randi(), "sites": []}
		if BIOMES[biome]["land"]:
			# places on the surface you can put troops down (Phase 4 builds the ground maps)
			var ns: int = 1 + r.randi() % 3
			for j in ns:
				var kind: String = ["outpost_site", "ruins", "pirate_camp", "colony"][r.randi() % 4]
				if biome == "infected":
					kind = "hive"
				elif region == "ascendancy" and r.randf() < 0.4:
					kind = "asc_outpost"
				pl["sites"].append({"kind": kind, "lat": r.randf_range(-0.9, 0.9), "lon": r.randf() * TAU,
					"name": "%s %s" % [pl["name"], ["Landing", "Basin", "Ridge", "Flats", "Crater", "Delta"][r.randi() % 6]]})
		s["planets"].append(pl)
	# stations
	match region:
		"vanguard":
			if home:
				s["stations"].append({"key": "%d_guild" % id, "cls": "STATION_FUEL_HUB", "team": 6, "fac": 1,
					"name": "%s Trade Post" % nm.get_slice(" ", 0), "economy": "hub"})
			else:
				s["stations"].append({"key": "%d_navy" % id, "cls": "STATION_FORTRESS", "team": 5, "fac": 1,
					"name": "Navy Station %s" % nm.get_slice(" ", 0), "economy": "military"})
				s["stations"].append({"key": "%d_guild" % id, "cls": ["STATION_INDUSTRIAL", "STATION_FUEL_HUB"][r.randi() % 2], "team": 6, "fac": 1,
					"name": "%s %s" % [nm.get_slice(" ", 0), ["Exchange", "Yards", "Market", "Depot"][r.randi() % 4]],
					"economy": ["industrial", "agri", "hub"][r.randi() % 3]})
		"ascendancy":
			if id == 1:
				s["stations"].append({"key": "%d_spire" % id, "cls": "STATION_FORTRESS", "team": 2, "fac": 2,
					"name": "Ascendancy Spire", "economy": "military"})
			elif r.randf() < 0.6:
				s["stations"].append({"key": "%d_asc" % id, "cls": "STATION_FORTRESS", "team": 2, "fac": 2,
					"name": "%s Bastion" % nm.get_slice(" ", 0), "economy": "military"})
			s["stations"].append({"key": "%d_concord" % id, "cls": ["STATION_INDUSTRIAL", "STATION_FUEL_HUB"][r.randi() % 2], "team": 7, "fac": 2,
				"name": "Concord %s" % nm.get_slice(" ", 0), "economy": ["industrial", "agri", "hub"][r.randi() % 3]})
		"free":
			s["stations"].append({"key": "%d_claim" % id, "cls": "OUTPOST_MINING", "team": 6 if mp.x < 500.0 else 7, "fac": 1 if mp.x < 500.0 else 2,
				"name": "%s Claim" % nm.get_slice(" ", 0), "economy": "mining"})
			if r.randf() < 0.65:
				s["pirates"] = true
				s["stations"].append(_pirate_den(r, s))
		"infected":
			s["derelicts"] = 1 + r.randi() % 2
	return s


static func _pirate_den(r: RandomNumberGenerator, s: Dictionary) -> Dictionary:
	return {"key": "%d_den" % s["id"], "cls": "GROUND_FORT", "team": 3, "fac": 3, "rock": true,
		"name": "%s Den" % ["Rust", "Blackwater", "Scrapper", "Red Hand", "Gutter"][r.randi() % 5], "economy": "pirate"}


static func system_of(gal: Dictionary, id: int) -> Dictionary:
	for s in gal["systems"]:
		if s["id"] == id:
			return s
	return {}


static func station_def(gal: Dictionary, key: String) -> Dictionary:
	for s in gal["systems"]:
		for st in s["stations"]:
			if st["key"] == key:
				return st
	return {}


## The 3D layout of one system: where its stations, gates, fields and planets go.
## Same seed, same answer: every visit to a system finds it as it was.
static func sector(gal: Dictionary, id: int) -> Dictionary:
	var s := system_of(gal, id)
	var r := RandomNumberGenerator.new()
	r.seed = int(s["seed"])
	var L := {"name": s["name"], "nebula": s["nebula"], "planet": {}, "fields": [], "field_mine": -1}
	L["sun_rot"] = Vector3(r.randf_range(-55.0, -25.0), r.randf_range(0.0, 360.0), 0)
	var warm := r.randf()
	L["sun_color"] = Color(1.0, lerpf(0.85, 1.0, warm), lerpf(0.7, 1.0, warm))
	var keep: Array = []
	# jump gates on the rim, toward the system they lead to
	var gates: Array = []
	for to in s["lanes"]:
		var o := system_of(gal, to)
		var d: Vector2 = (o["map"] as Vector2) - (s["map"] as Vector2)
		var dir := Vector3(d.x, 0, d.y).normalized()
		var gp: Vector3 = dir * (SYSTEM_R - 650.0)
		# keep the gate well clear of the planets (ships can't fly through worlds)
		for k in 24:
			var clear := true
			for pl in s["planets"]:
				if Vector2(gp.x - pl["pos"].x, gp.z - pl["pos"].z).length() < float(pl["radius"]) + 600.0:
					clear = false
			if clear:
				break
			gp = gp.rotated(Vector3.UP, 0.26 * (1 if k % 2 == 0 else -1) * (k / 2 + 1)) * 0.97
		gates.append({"to": to, "pos": gp, "name": o["name"]})
		keep.append(gp)
	L["gates"] = gates
	for pl in s["planets"]:
		keep.append(pl["pos"])
	# stations: spread around the middle, clear of the gates and the planets
	var placed: Array = []
	for st in s["stations"]:
		var p := Vector3.ZERO
		for t in 200:
			var a := r.randf() * TAU
			var dist := r.randf_range(700.0, 2100.0)
			p = Vector3(cos(a) * dist, 0, sin(a) * dist)
			var ok := true
			for k in keep + placed:
				if Vector2(p.x - k.x, p.z - k.z).length() < 950.0:
					ok = false
					break
			for pl in s["planets"]:
				if Vector2(p.x - pl["pos"].x, p.z - pl["pos"].z).length() < pl["radius"] + 700.0:
					ok = false
			if ok:
				break
		placed.append(p)
		L["st_" + st["key"]] = p
		if st.get("rock", false):
			L["rock_" + st["key"]] = r.randf_range(170.0, 230.0)
	L["home_spot"] = Vector3.ZERO
	if id == gal["home"]:
		# the player's own starter station
		for t in 200:
			var a := r.randf() * TAU
			var p := Vector3(cos(a), 0, sin(a)) * r.randf_range(500.0, 1500.0)
			var ok := true
			for k in keep + placed:
				if Vector2(p.x - k.x, p.z - k.z).length() < 1000.0:
					ok = false
			if ok:
				L["home_spot"] = p
				break
		placed.append(L["home_spot"])
	# asteroid fields (each with its ore and a few huge rocks to fight around)
	var fields: Array = []
	var tries := 0
	while fields.size() < int(s["fields"]) and tries < 120:
		tries += 1
		var c := Vector3(r.randf_range(-2500.0, 2500.0), r.randf_range(-60.0, 60.0), r.randf_range(-2500.0, 2500.0))
		if c.length() > SYSTEM_R - 600.0:
			continue
		var rad := r.randf_range(300.0, 560.0)
		var ok := true
		for k in keep + placed:
			if Vector2(c.x - k.x, c.z - k.z).length() < rad + 380.0:
				ok = false
		for f in fields:
			if Vector2(c.x - f["center"].x, c.z - f["center"].z).length() < rad + f["radius"] + 150.0:
				ok = false
		for pl in s["planets"]:
			if Vector2(c.x - pl["pos"].x, c.z - pl["pos"].z).length() < rad + pl["radius"] + 200.0:
				ok = false
		if not ok:
			continue
		var ore: String = ["iron", "iron", "ice", "crystal", "core"][r.randi() % 5]
		var big: Array = []
		for i in 3 + r.randi() % 4:
			var d := Vector3(r.randfn(), r.randfn() * 0.15, r.randfn()).normalized() * r.randf_range(0.0, 0.85) * rad
			big.append({"pos": c + d, "radius": r.randf_range(35.0, 110.0), "seed": r.randi()})
		fields.append({"center": c, "radius": rad, "count": int(rad * 0.6), "seed": r.randi(), "ore": ore,
			"resource": {"iron": "alloys", "ice": "fuel", "crystal": "circuitry", "core": "cores"}[ore],
			"amount": r.randf_range(3000.0, 9000.0), "big": big})
	if fields.is_empty() and id == int(gal["home"]):
		# the home system always has a field for the starting miners
		var hs: Vector3 = L["home_spot"]
		var c2: Vector3 = hs + (hs if hs.length() > 1.0 else Vector3.RIGHT).normalized() * 900.0
		fields.append({"center": c2, "radius": 380.0, "count": 220, "seed": r.randi(), "ore": "iron", "resource": "alloys",
			"amount": 8000.0, "big": [{"pos": c2, "radius": 80.0, "seed": r.randi()}]})
	L["fields"] = fields
	return L
