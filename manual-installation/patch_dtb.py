import os
import sys
import re

dtb_path = "/media/dev-jonathan/armbi_root/boot/dtb/allwinner/sun50i-h313-x96q-lpddr3.dtb"
dts_path = "/tmp/temp.dts"

if not os.path.exists(dtb_path):
    print(f"Error: DTB file not found at {dtb_path}")
    print("Is the MicroSD card partition sdb1 mounted at /media/dev-jonathan/armbi_root?")
    sys.exit(1)

# Decompile
print("Decompiling DTB...")
exit_code = os.system(f"dtc -I dtb -O dts -o {dts_path} {dtb_path}")
if exit_code != 0:
    print("Error: Decompilation failed. Is 'device-tree-compiler' installed on the Host PC?")
    sys.exit(1)

# Read and patch
with open(dts_path, "r") as f:
    dts_content = f.read()

# Locate mmc@4022000 (eMMC)
print("Patching DTS...")
pattern = r"(mmc@4022000\s*\{[^}]*\})"
match = re.search(pattern, dts_content)
if match:
    node_block = match.group(1)
    # Remove hs200 and hs400 settings
    patched_block = node_block.replace("mmc-hs200-1.8v;", "")
    patched_block = patched_block.replace("mmc-hs400-1.8v;", "")
    dts_content = dts_content.replace(node_block, patched_block)
    print("Found mmc@4022000 and removed high-speed modes!")
else:
    print("Warning: mmc@4022000 node not found, doing generic replace for hs200/hs400...")
    dts_content = dts_content.replace("mmc-hs200-1.8v;", "")
    dts_content = dts_content.replace("mmc-hs400-1.8v;", "")

with open(dts_path, "w") as f:
    f.write(dts_content)

# Recompile
print("Recompiling back to DTB...")
exit_code = os.system(f"dtc -I dts -O dtb -o {dtb_path} {dts_path}")
if exit_code != 0:
    print("Error: Recompilation failed.")
    sys.exit(1)

print("DTB successfully patched and saved on MicroSD!")
