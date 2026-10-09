extends Node
## Loads every script so parse errors show up with file and line (autoloads active).
func _ready() -> void:
	for d in ["res://scripts", "res://scripts/campaign", "res://tests"]:
		for f in DirAccess.get_files_at(d):
			if f.ends_with(".gd"):
				var s = load(d + "/" + f)
				if s == null:
					print("COMPILE FAIL ", f)
	print("COMPILE DONE")
	get_tree().quit()
