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
os.system("rm -f /tmp/temp.dts") # Clean up first
exit_code = os.system(f"dtc -I dtb -O dts -o {dts_path} {dtb_path}")
if exit_code != 0:
    print("Error: Decompilation failed. Is 'device-tree-compiler' installed?")
    sys.exit(1)

# Read
with open(dts_path, "r") as f:
    content = f.read()

# Locate mmc@4022000 block (eMMC)
print("Patching DTS...")
pattern = r"(mmc@4022000\s*\{[^}]*\})"
match = re.search(pattern, content)
if match:
    node_block = match.group(1)
    
    # Remove HS200 and HS400 modes
    patched_block = node_block.replace("mmc-hs200-1.8v;", "")
    patched_block = patched_block.replace("mmc-hs400-1.8v;", "")
    
    # Check if max-frequency exists in this block
    if "max-frequency" in patched_block:
        patched_block = re.sub(r"max-frequency\s*=\s*<[^>]*>;", "max-frequency = <25000000>;", patched_block)
    else:
        patched_block = patched_block.replace("mmc@4022000 {", "mmc@4022000 {\n\t\tmax-frequency = <25000000>;")
        
    content = content.replace(node_block, patched_block)
    print("Patched mmc@4022000 node successfully: removed HS modes and limited to 25 MHz!")
else:
    print("Warning: mmc@4022000 node not found. Applying generic replacements...")
    content = content.replace("mmc-hs200-1.8v;", "")
    content = content.replace("mmc-hs400-1.8v;", "")

with open(dts_path, "w") as f:
    f.write(content)

# Recompile
print("Recompiling back to DTB...")
exit_code = os.system(f"dtc -I dts -O dtb -o {dtb_path} {dts_path}")
if exit_code != 0:
    print("Error: Recompilation failed.")
    sys.exit(1)

print("DTB successfully compiled and saved with 25 MHz eMMC frequency limit!")
