import requests
from datetime import datetime
from sys import argv
from msvcrt import getch as wait

mod_line_starter = "[Info   :   BepInEx] TS Manifest: "
SOTS_update = datetime.fromtimestamp(1724779800)
filepath = "LogOutput.log" if len(argv) <= 1 else argv[1]
if filepath != "LogOutput.log":
	print(f"Got file path {filepath}")

print("Getting modlist from log...")
provided_mods = set()
found_mods = 0
with open(filepath,"r") as file:
	lines = file.read().split("\n")
	for line in lines:
		if mod_line_starter in line:
			found_mods += 1
			mod_string = line[line.index(mod_line_starter) + len(mod_line_starter):]
			provided_mods.add(mod_string)
			print("- " + mod_string)
print(f"{found_mods} mods found in log.")
#print(provided_mods)
print()

print("Getting packages...")
package_list = requests.get("https://thunderstore.io/c/riskofrain2/api/v1/package/").json()
print(f"{len(package_list)} packages found on TS.\n")

print("Collecting package timestamps...")
package_timestamps = dict()
for package in package_list:
	for v in package['versions']:
		name = v['full_name']
		converted_timestamp = datetime.strptime(v['date_created'],"%Y-%m-%dT%H:%M:%S.%fZ")
		if name not in package_timestamps or package_timestamps[name] < converted_timestamp:
			package_timestamps[name] = converted_timestamp
print(f"Collected {len(package_timestamps)} timestamps.\n")

out_of_date_stuff = set()

print("Searching for out of date packages...")
for mod in provided_mods:
	if 'R2API' in mod.upper():
		continue
	if package_timestamps[mod] < SOTS_update:
		out_of_date_stuff.add(mod)

if len(out_of_date_stuff) > 0:
	print(f"Out of date mods found ({len(out_of_date_stuff)}):")
	counter = 0
	for mod in sorted(list(out_of_date_stuff)):
		diff = SOTS_update - package_timestamps[mod]
		counter += 1
		print(f"{counter}) {mod} (Out of date by {diff})")
else:
	print("No outdated mods found.")

print("\nPress any key to close...")
wait()