import os
import sys
import time
import subprocess
import pexpect
import re

def remote_raw_flash():
    image_path = "downloads/Armbian-unofficial_26.02.0-trunk_X96q-v1-3_bookworm_current_6.12.64_minimal.img"
    target_ip = "192.168.1.67"
    
    if not os.path.exists(image_path):
        print(f"Error: Uncompressed image not found at {image_path}")
        print("Please ensure you ran the decompression on the Host PC first.")
        sys.exit(1)
        
    image_size = os.path.getsize(image_path)
    print(f"Image Size: {image_size / (1024*1024):.1f} MB")
    
    # 1. Start SSH pipeline with dd
    # We pipe data directly to dd on /dev/mmcblk2
    # We use conv=fsync to write directly to hardware, bypassing page cache.
    print(f"\n>>> Starting streaming raw flash to eMMC on {target_ip}...")
    ssh_cmd = [
        "ssh", "-o", "StrictHostKeyChecking=no", f"dev12@{target_ip}",
        "sudo dd of=/dev/mmcblk2 bs=256k oflag=direct"
    ]
    
    try:
        proc = subprocess.Popen(ssh_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        print(f"Error launching SSH subprocess: {e}")
        sys.exit(1)
        
    # We regulate rate to ~3.2 MB/s (using 80ms gaps for electrical stability and oflag=direct to bypass RAM cache)
    chunk_size = 256 * 1024 # 256 KB
    sleep_time = 0.08 # 80ms rest after every 256KB write
    
    bytes_sent = 0
    start_time = time.time()
    last_print_time = start_time
    
    try:
        with open(image_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                    
                # Write to SSH stdin
                proc.stdin.write(chunk)
                bytes_sent += len(chunk)
                
                # Pace the transfer
                time.sleep(sleep_time)
                
                # Print progress every 5 seconds
                current_time = time.time()
                if current_time - last_print_time >= 5.0:
                    elapsed = current_time - start_time
                    speed = (bytes_sent / (1024 * 1024)) / elapsed
                    progress_pct = (bytes_sent / image_size) * 100.0
                    print(f"Progress: {progress_pct:.1f}% | Sent: {bytes_sent / (1024 * 1024):.1f} MB / {image_size / (1024*1024):.1f} MB | Speed: {speed:.2f} MB/s")
                    last_print_time = current_time
                    
        # Close stdin to tell dd we are done
        proc.stdin.close()
        print("\n>>> Image transmission completed. Waiting for TV Box to finalize fsync writes...")
        stdout, stderr = proc.communicate(timeout=120)
        print("SSH dd output:")
        print(stderr.decode('utf-8', errors='ignore'))
    except Exception as e:
        print(f"\n>>> Error during streaming: {e}")
        proc.kill()
        sys.exit(1)
        
    if proc.returncode != 0:
        print(f"\n>>> Flashing command failed with return code {proc.returncode}")
        sys.exit(1)
        
    print("\n>>> Raw block writing completed successfully!")
    
    # 2. Configure partitions and UUIDs
    print("\n>>> Step 2: Configuring partitions and boot UUIDs on TV Box...")
    ssh_conn = "ssh -o StrictHostKeyChecking=no dev12@192.168.1.67"
    child = pexpect.spawn(ssh_conn)
    
    try:
        i = child.expect(["password:", "dev12@x96q-v1-3:"], timeout=15)
        if i == 0:
            child.sendline("dev")
            child.expect("dev12@x96q-v1-3:", timeout=15)
        
        print("Registering partitions...")
        child.sendline("sudo partprobe /dev/mmcblk2")
        child.expect("dev12@x96q-v1-3:", timeout=15)
        time.sleep(2)
        
        print("Generating random UUID for eMMC partition...")
        child.sendline("sudo tune2fs -U random /dev/mmcblk2p1")
        child.expect("dev12@x96q-v1-3:", timeout=20)
        
        # Get new UUID
        child.sendline("sudo blkid -o value -s UUID /dev/mmcblk2p1")
        child.expect("dev12@x96q-v1-3:", timeout=15)
        
        output = child.before.decode('utf-8', errors='ignore')
        # Parse UUID from output (UUID format: 8-4-4-4-12 hex chars)
        match = re.search(r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})", output)
        if not match:
            print(f"Error parsing UUID from output: {output}")
            sys.exit(1)
            
        emmc_uuid = match.group(1)
        print(f"New eMMC UUID: {emmc_uuid}")
        
        # Mount and edit configuration files
        print("Mounting eMMC to update configs...")
        child.sendline("sudo mkdir -p /mnt/emmc")
        child.expect("dev12@x96q-v1-3:", timeout=15)
        
        child.sendline("sudo mount /dev/mmcblk2p1 /mnt/emmc")
        child.expect("dev12@x96q-v1-3:", timeout=15)
        
        # Update /etc/fstab on eMMC
        print("Updating /etc/fstab on target...")
        fstab_content = f"""# <file system>					<mount point>	<type>	<options>							<dump>	<pass>
UUID={emmc_uuid}		/		ext4	defaults,noatime,commit=600,errors=remount-ro		0	1
tmpfs						/tmp		tmpfs	defaults,nosuid							0	0
"""
        child.sendline(f"sudo tee /mnt/emmc/etc/fstab << 'EOF'\n{fstab_content}EOF")
        child.expect("dev12@x96q-v1-3:", timeout=15)
        
        # Update /boot/armbianEnv.txt on eMMC
        print("Updating /boot/armbianEnv.txt on target...")
        child.sendline(f"sudo sed -i 's/^rootdev=UUID=.*/rootdev=UUID={emmc_uuid}/' /mnt/emmc/boot/armbianEnv.txt")
        child.expect("dev12@x96q-v1-3:", timeout=15)
        
        # Unmount
        print("Unmounting eMMC...")
        child.sendline("sudo umount /mnt/emmc")
        child.expect("dev12@x96q-v1-3:", timeout=15)
        
        child.sendline("exit")
        child.expect(pexpect.EOF)
        print("\n=== INSTALLATION COMPLETED SUCCESSFULLY ===")
        print("You can now safely shut down the TV Box, remove the MicroSD card, and power it back on!")
        
    except Exception as e:
        print(f"\n>>> Error during post-configuration: {e}")
        print(child.before.decode('utf-8', errors='ignore') if child.before else "")
        sys.exit(1)

if __name__ == "__main__":
    remote_raw_flash()
