import os
import sys
import time
import lzma
import re
import subprocess

image_path_xz = "/home/dev12/Armbian-unofficial_26.02.0-trunk_X96q-v1-3_bookworm_current_6.12.64_minimal.img.xz"
image_path_raw = "/home/dev12/Armbian-unofficial_26.02.0-trunk_X96q-v1-3_bookworm_current_6.12.64_minimal.img"
target_dev = "/dev/mmcblk2"
target_part = "/dev/mmcblk2p1"
mount_point = "/mnt/emmc"

if os.path.exists(image_path_raw):
    image_path = image_path_raw
    print("Using uncompressed raw image.")
elif os.path.exists(image_path_xz):
    image_path = image_path_xz
    print("Using compressed xz image.")
else:
    print(f"Error: Source image not found. Checked both:\n  - {image_path_raw}\n  - {image_path_xz}")
    sys.exit(1)

# Ensure target is not mounted
subprocess.run(["umount", "-l", mount_point], capture_output=True)
subprocess.run(["umount", "-l", target_part], capture_output=True)

print("Starting raw flash of eMMC at 2.0 MB/s limit...")
chunk_size = 64 * 1024 # 64 KB
sleep_time = 0.03 # Paces it to ~2.0 MB/s

try:
    out_fd = os.open(target_dev, os.O_WRONLY | os.O_SYNC)
except Exception as e:
    print(f"Error opening target device: {e}")
    sys.exit(1)

bytes_written = 0
bytes_since_sync = 0
start_time = time.time()

try:
    is_xz = image_path.endswith(".xz")
    open_func = lzma.open if is_xz else open
    with open_func(image_path, "rb") as in_f:
        while True:
            chunk = in_f.read(chunk_size)
            if not chunk:
                break
            os.write(out_fd, chunk)
            bytes_written += len(chunk)
            bytes_since_sync += len(chunk)
            
            # Sync every 2 MB to prevent cache buildup
            if bytes_since_sync >= 2 * 1024 * 1024:
                os.fdatasync(out_fd)
                bytes_since_sync = 0
                
            time.sleep(sleep_time)
            
            # Progress print every 10 MB
            if bytes_written % (10 * 1024 * 1024) == 0:
                elapsed = time.time() - start_time
                speed = (bytes_written / (1024 * 1024)) / elapsed
                print(f"Written: {bytes_written / (1024 * 1024):.1f} MB | Speed: {speed:.2f} MB/s")
                
except Exception as e:
    print(f"Error during flashing: {e}")
    os.close(out_fd)
    sys.exit(1)

os.fdatasync(out_fd)
os.close(out_fd)
print("Raw block writing completed!")

# Partprobe to make kernel register the new partitions
print("Updating partition tables...")
subprocess.run(["partprobe", target_dev], check=True)
time.sleep(2)

# Generate a unique UUID for the new partition
print("Generating unique UUID for eMMC partition...")
subprocess.run(["tune2fs", "-U", "random", target_part], check=True)

# Get the new UUID
result = subprocess.run(["blkid", "-o", "value", "-s", "UUID", target_part], capture_output=True, text=True, check=True)
emmc_uuid = result.stdout.strip()
print(f"New eMMC UUID: {emmc_uuid}")

# Mount and update configuration files
os.makedirs(mount_point, exist_ok=True)
subprocess.run(["mount", target_part, mount_point], check=True)

# Update /etc/fstab on eMMC
fstab_path = os.path.join(mount_point, "etc", "fstab")
fstab_content = f"""# <file system>					<mount point>	<type>	<options>							<dump>	<pass>
UUID={emmc_uuid}		/		ext4	defaults,noatime,commit=600,errors=remount-ro		0	1
tmpfs						/tmp		tmpfs	defaults,nosuid							0	0
"""
with open(fstab_path, "w") as f:
    f.write(fstab_content)
print("Updated /etc/fstab on target.")

# Update /boot/armbianEnv.txt on eMMC
env_path = os.path.join(mount_point, "boot", "armbianEnv.txt")
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        env_content = f.read()
    env_content = re.sub(r"rootdev=UUID=\S+", f"rootdev=UUID={emmc_uuid}", env_content)
    with open(env_path, "w") as f:
        f.write(env_content)
    print("Updated /boot/armbianEnv.txt on target.")

# Unmount
subprocess.run(["umount", mount_point], check=True)
print("=== INSTALLATION COMPLETED SUCCESSFULLY ===")
