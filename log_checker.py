import requests
from datetime import datetime
from sys import argv
from msvcrt import getch
from io import BytesIO
import zipfile

mod_line_starter = "[Info   :   BepInEx] TS Manifest: "
SOTS_update = datetime.fromtimestamp(1724779800)
filepath = "LogOutput.log" if len(argv) <= 1 else argv[1]
if filepath != "LogOutput.log":
	print(f"Got file path {filepath}")

print("Getting modlist from log...")
provided_mods = set()
found_mods = 0
with open(filepath,"r",encoding='utf-8') as file:
	lines = file.read().split("\n")
	for line in lines:
		if mod_line_starter in line:
			found_mods += 1
			mod_string = line[line.index(mod_line_starter) + len(mod_line_starter):]
			provided_mods.add(mod_string)
			print("- " + mod_string)
print(f"{found_mods} mods found in log.")
print()

print("Getting packages...")
package_list = requests.get("https://thunderstore.io/c/riskofrain2/api/v1/package/").json()
print(f"{len(package_list)} packages found on TS.\n")

print("Collecting package metadata...")
package_timestamps = dict()
package_tags = dict()
for package in package_list:
	tags = set(package['categories'])
	for v in package['versions']:
		name = v['full_name']
		converted_timestamp = datetime.strptime(v['date_created'],"%Y-%m-%dT%H:%M:%S.%fZ")
		if name not in package_timestamps or package_timestamps[name] < converted_timestamp:
			package_timestamps[name] = converted_timestamp
			package_tags[name] = tags
print(f"Collected {len(package_timestamps)} metadata pieces.\n")

out_of_date_stuff = set()

print("Searching for out of date packages...")
for mod in provided_mods:
	if 'R2API' in mod.upper():
		# out of date R2API packages are fine and generally expected in most cases
		continue
	if package_timestamps[mod] < SOTS_update:
		out_of_date_stuff.add(mod)

safe_package_types = {"Skins","Mods","Client-side","NSFW","Survivors of the Void","Seekers of the Storm Update"}
ood_safer_mods = set()
print("Checking which mods are probably safe...")
for ood_mod in out_of_date_stuff:
	tags = package_tags[ood_mod]
	if "Skins" in tags and tags.issubset(safe_package_types):
		ood_safer_mods.add(ood_mod)

for ood_safe_mod in ood_safer_mods:
	out_of_date_stuff.remove(ood_safe_mod)

if len(out_of_date_stuff) > 0:
	print(f"\nOut of date mods found ({len(out_of_date_stuff)}):")
	counter = 0
	for mod in sorted(list(out_of_date_stuff)):
		diff = SOTS_update - package_timestamps[mod]
		counter += 1
		print(f"{counter}) {mod} (Out of date by {diff.days} days)")
		
else:
	print("No outdated mods found.")

if len(ood_safer_mods) > 0:
	print(f"\nBelow is a list of {len(ood_safer_mods)} skin mods that are technically out of date, but are unlikely to cause problems.")
	print(f"Disable them if things are still broken after removing everything in the above list.")
	counter = 0
	for mod in sorted(list(ood_safer_mods)):
		diff = SOTS_update - package_timestamps[mod]
		counter += 1
		print(f"{counter}) {mod} (Out of date by {diff.days} days)")

mod_profile_string = "profileName: LatestTSLogCheckerExport"
mod_profile_string += "\nmods:"

for mod in provided_mods:
	mj,mn,pt = mod.split('-')[-1].split('.')
	package = '-'.join(mod.split('-')[:-1])

	mod_profile_string += f"\n- name: {package}"
	mod_profile_string += f"\n  version:"
	mod_profile_string += f"\n    major: {mj}"
	mod_profile_string += f"\n    minor: {mn}"
	mod_profile_string += f"\n    patch: {pt}"
	mod_profile_string += f"\n  enabled: true"

mod_profile_string += "\nsource: r2"
mod_profile_string += "\nignoredUpdates: []\n"

export_filename = 'latest_log_profile.r2z'

zip_buffer = BytesIO()
with zipfile.ZipFile(zip_buffer,'w',zipfile.ZIP_DEFLATED) as zipf:
	zipf.writestr('export.r2x',mod_profile_string)
zip_buffer.seek(0)
with open(export_filename,'wb') as bin_file:
	bin_file.write(zip_buffer.getbuffer())

print(f"\n- Created r2modman profile for this log, saved as {export_filename}.")

print("\nPress any key to close...")
getch()