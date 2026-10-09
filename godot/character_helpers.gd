extends Node3D
## Helpers for characters made by character_generator.py.
##
## Setup: import character_F1.glb (or F2) - the file with the whole wardrobe -
## put it in a scene, attach this script to its root, set `faction`, and copy
## data/weapons_and_armor.json into your project (path below).
##
##   $Trooper.apply_role("medic")                   # dress as a medic
##   $Trooper.attach_item("MedpenSlot_1", medpen_scene)
##   $Trooper.clear_slot("MagSlot_1")               # a magazine got used
##   var hit := $Trooper.damage_taken(26.0, 2)     # faction-2 plasma rifle hit
##
## Written for Godot 4.x and not yet run inside Godot: a starting point.

@export var faction: int = 1
@export var data_path: String = "res://data/weapons_and_armor.json"
@export var start_role: String = "rifleman"

var data: Dictionary = {}
var role: String = ""


func _ready() -> void:
	var text := FileAccess.get_file_as_string(data_path)
	var parsed = JSON.parse_string(text)
	if parsed is Dictionary:
		data = parsed
		apply_role(start_role)
	else:
		push_error("Couldn't read %s" % data_path)


## Show only the body plus the pieces this role wears.
func apply_role(new_role: String) -> void:
	var roles: Dictionary = data["roles"][str(faction)]
	if not roles.has(new_role):
		push_error("Unknown role: %s" % new_role)
		return
	role = new_role
	var wears: Array = roles[new_role]["pieces"]
	var owner_of: Dictionary = data["wardrobe_meshes"][str(faction)]
	for n in find_children("*", "MeshInstance3D", true, false):
		var key := String(n.name)
		if owner_of.has(key):
			var piece: String = owner_of[key]
			n.visible = piece == "" or wears.has(piece)


## The inventory a role starts with: { socket name: item name }.
func starting_inventory() -> Dictionary:
	return data["roles"][str(faction)][role]["inventory"]


## Put an item (a scene you instanced from item_*.glb) into a socket.
func attach_item(socket: String, item_scene: PackedScene) -> Node3D:
	var found := find_children("*" + socket + "*", "", true, false)
	if found.is_empty():
		push_error("No socket named %s" % socket)
		return null
	clear_slot(socket)
	var item := item_scene.instantiate() as Node3D
	found[0].add_child(item)
	return item


## Remove whatever sits in a socket (the magazine was loaded, the grenade thrown...).
func clear_slot(socket: String) -> void:
	for s in find_children("*" + socket + "*", "", true, false):
		for child in s.get_children():
			child.queue_free()


## Damage this character takes from one hit by a weapon of `attacker_faction`.
## raw_damage = the weapon's base damage (before faction bonus).
func damage_taken(raw_damage: float, attacker_faction: int) -> float:
	var mult: float = data["factions"][str(attacker_faction)]["damage_mult"]
	var dr: float = data["roles"][str(faction)][role]["damage_reduction"]
	return raw_damage * mult * (1.0 - dr)
