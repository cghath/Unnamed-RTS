extends Node3D
## Small helpers for ships made by ship_generator.py.
##
## How to use: in Godot, drag a ship .glb into a scene, right-click it and choose
## "Make Local" (or open it as an inherited scene), then attach this script to
## the ship's root node. Call the functions from your game code, e.g.
##     $Ship_LARGE.breach("*BreachPanel_1*")
##     $Ship_LARGE.set_shields("*HangarShield*", false)
##
## Name patterns use * as a wildcard, so they still match if Godot shortens the
## names on import (it may drop the "-col" ending, for example).
##
## Axes: Blender's X stays X in Godot, Blender's Y (ship forward) becomes -Z,
## and Blender's Z (up) becomes Y. So a door that slides "+2.1 m on Y" in the
## generator notes slides Vector3(0, 0, -2.1) here.
##
## Written for Godot 4.x and not yet run inside Godot, so treat it as a
## starting point.


## Every node whose name matches the pattern, anywhere under this ship.
func find_parts(pattern: String) -> Array[Node]:
	return find_children(pattern, "", true, false)


## First marker (Node3D) matching the pattern, or null. Markers are the empties
## the generator places: spawns, seats, pads, muster points, charge points...
func marker(pattern: String) -> Node3D:
	var found := find_parts(pattern)
	if found.is_empty():
		return null
	return found[0] as Node3D


## Blow open a breach panel, breachable wall, locked door, pod hatch, etc.
## Removes the mesh and the collision Godot generated under it.
func breach(pattern: String) -> void:
	for n in find_parts(pattern):
		n.queue_free()


## Show or hide energy shields (hangar and cargo bay). The shield meshes have
## no collision; add an Area3D/StaticBody3D of your own if ships should bounce off.
func set_shields(pattern: String, on: bool) -> void:
	for n in find_parts(pattern):
		if n is Node3D:
			n.visible = on


## Slide doors (blast doors, airlock doors, elevator doors) by an offset.
## Example: close a blast door  -> slide("*BlastDoor_C2_C3_D0*", Vector3(-1.65, 0, 0))
##          open an airlock     -> slide("*Airlock_1_OuterDoor*", Vector3(0, 0, -2.1))
func slide(pattern: String, offset: Vector3, seconds: float = 0.6) -> void:
	for n in find_parts(pattern):
		if n is Node3D:
			var t := create_tween()
			t.tween_property(n, "position", n.position + offset, seconds)


## Move the elevator car to a deck (deck 0 = bottom). Decks are 4 m apart.
func move_elevator(index: int, deck: int, seconds: float = 2.0) -> void:
	for n in find_parts("*Elevator_%d*" % index):
		if n is Node3D and not String(n.name).contains("Door") and not String(n.name).contains("Stop"):
			var t := create_tween()
			t.tween_property(n, "position:y", deck * 4.0, seconds)


## Open or close a station door (connector doors between modules, side airlocks).
## Station doors are modeled CLOSED. Opening hides the door and switches off the
## collision Godot generated for it; closing brings both back.
## Example: $STATION_HOME.set_door("*M04REF_Connector_Back_Door*", true)
func set_door(pattern: String, open: bool) -> void:
	for n in find_parts(pattern):
		if n is Node3D:
			n.visible = not open
			for c in n.find_children("*", "CollisionShape3D", true, false):
				c.set_deferred("disabled", open)


## Colors for a station module's roof light, one per state in economy_data.MODULE_STATES.
const MODULE_STATE_COLORS := {
	"online": Color(0.3, 1.0, 0.5),
	"offline": Color(0.35, 0.45, 0.6),
	"sabotaged": Color(1.0, 0.45, 0.1),
	"disabled": Color(1.0, 0.15, 0.1),
	"infected": Color(0.75, 0.2, 1.0),
	"destroyed": Color(0.1, 0.1, 0.1),
}


## Recolor a module's roof StatusLight to show its state. `code` is the module's
## code from the object names, e.g. "M04REF" (module 4, refinery).
## Example: $STATION_HOME.show_module_state("M04REF", "sabotaged")
func show_module_state(code: String, state: String) -> void:
	var mat := StandardMaterial3D.new()
	var col: Color = MODULE_STATE_COLORS.get(state, Color.WHITE)
	mat.albedo_color = col
	mat.emission_enabled = true
	mat.emission = col
	mat.emission_energy_multiplier = 3.0
	for n in find_parts("*%s_StatusLight*" % code):
		if n is MeshInstance3D:
			n.material_override = mat


## All sabotage points of one module, as markers (where an engineer stands).
## The matching "_ChargeA" markers are where the charge / tool goes on the wall.
func sabotage_points(code: String) -> Array[Node3D]:
	var out: Array[Node3D] = []
	for n in find_parts("*%s_SabotagePoint_*" % code):
		if n is Node3D and not String(n.name).contains("ChargeA"):
			out.append(n)
	return out
