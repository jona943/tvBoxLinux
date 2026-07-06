import pexpect
import sys
import re
import time

def run_post_config():
    target_ip = "192.168.1.67"
    print("\n>>> Starting post-configuration of boot UUIDs on TV Box eMMC...")
    ssh_conn = f"ssh -o StrictHostKeyChecking=no dev12@{target_ip}"
    child = pexpect.spawn(ssh_conn)
    
    try:
        # Since keys are configured, it should log in immediately
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
        print("Retrieving new partition UUID...")
        child.sendline("sudo blkid -o value -s UUID /dev/mmcblk2p1")
        child.expect("dev12@x96q-v1-3:", timeout=15)
        
        output = child.before.decode('utf-8', errors='ignore')
        print(f"Blkid Output:\n{output}")
        
        # Parse UUID
        match = re.search(r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})", output)
        if not match:
            print("Error: Could not find valid UUID in blkid output.")
            sys.exit(1)
            
        emmc_uuid = match.group(1)
        print(f"New eMMC UUID: {emmc_uuid}")
        
        # Mount and edit configuration files
        print("Mounting eMMC mountpoint...")
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
        print("\n=== POST-CONFIGURATION COMPLETED SUCCESSFULLY ===")
        print("Installation is 100% complete! You can now shut down, remove MicroSD and boot from eMMC!")
        
    except Exception as e:
        print(f"\n>>> Error during post-configuration: {e}")
        print(child.before.decode('utf-8', errors='ignore') if child.before else "")
        sys.exit(1)

if __name__ == "__main__":
    run_post_config()
