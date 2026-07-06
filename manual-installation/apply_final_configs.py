import pexpect
import sys
import time

def apply_final_configs():
    target_ip = "192.168.1.67"
    print(f"\n>>> Connecting to {target_ip} to apply final stability configurations...")
    
    ssh_cmd = f"ssh -o StrictHostKeyChecking=no dev12@{target_ip}"
    child = pexpect.spawn(ssh_cmd)
    
    try:
        # Key connection
        i = child.expect(["password:", "dev12@x96q-v1-3:"], timeout=15)
        if i == 0:
            child.sendline("dev")
            child.expect("dev12@x96q-v1-3:", timeout=15)
            
        # 1. Configure permanent RAM cache limit for stability
        print("Configuring permanent sysctl limits for RAM stability...")
        sysctl_conf = """# Permanent RAM stability configurations to prevent false DRAM lockups
vm.dirty_background_bytes = 4194304
vm.dirty_bytes = 8388608
"""
        child.sendline(f"sudo tee /etc/sysctl.d/99-ram-stability.conf << 'EOF'\n{sysctl_conf}EOF")
        child.expect("dev12@x96q-v1-3:", timeout=15)
        
        # Apply the sysctl rules
        print("Applying sysctl rules...")
        child.sendline("sudo sysctl --system")
        child.expect("dev12@x96q-v1-3:", timeout=15)
        
        # 2. Ensure Wi-Fi drivers load automatically on boot
        print("Configuring automatic load of Wi-Fi drivers at boot...")
        modules_conf = """aic8800_bsp
aic8800_fdrv
"""
        child.sendline(f"sudo tee /etc/modules-load.d/aic8800.conf << 'EOF'\n{modules_conf}EOF")
        child.expect("dev12@x96q-v1-3:", timeout=15)
        
        # 3. Retrieve system status
        print("Retrieving final system status...")
        
        # Check RAM and Swap
        child.sendline("free -h")
        child.expect("dev12@x96q-v1-3:", timeout=15)
        ram_status = child.before.decode('utf-8', errors='ignore')
        print(f"Memory Status:\n{ram_status}")
        
        # Check active Wi-Fi interface status
        child.sendline("ip a show dev wlan0")
        child.expect("dev12@x96q-v1-3:", timeout=15)
        wifi_status = child.before.decode('utf-8', errors='ignore')
        print(f"Wi-Fi Status:\n{wifi_status}")
        
        child.sendline("exit")
        child.expect(pexpect.EOF)
        print("\n=== SYSTEM OPTIMIZATION COMPLETED SUCCESSFULLY ===")
        print("The eMMC installation is now fully optimized for memory stability and boot persistence!")
        
    except Exception as e:
        print(f"Error during final optimization: {e}")
        print(child.before.decode('utf-8', errors='ignore') if child.before else "")
        sys.exit(1)

if __name__ == "__main__":
    apply_final_configs()
