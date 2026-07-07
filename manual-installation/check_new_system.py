import pexpect
import sys

def check_new_system():
    target_ip = "192.168.1.68"
    user = "dev13"
    password = "dev"
    
    print(f"\n>>> Connecting to new system {user}@{target_ip}...")
    ssh_cmd = f"ssh -o StrictHostKeyChecking=no {user}@{target_ip}"
    child = pexpect.spawn(ssh_cmd)
    
    try:
        i = child.expect(["password:", "dev13@x96q-v1-3:"], timeout=15)
        if i == 0:
            child.sendline(password)
            child.expect("dev13@x96q-v1-3:", timeout=15)
            
        print("\n================ SYSTEM DIAGNOSTICS ================")
        
        # 1. Check kernel and OS
        print("\n--- Kernel Version ---")
        child.sendline("uname -a")
        child.expect("dev13@x96q-v1-3:", timeout=15)
        print(child.before.decode('utf-8', errors='ignore').strip())
        
        # 2. Check eMMC partition size and usage
        print("\n--- eMMC Storage Usage ---")
        child.sendline("df -h /")
        child.expect("dev13@x96q-v1-3:", timeout=15)
        print(child.before.decode('utf-8', errors='ignore').strip())
        
        # 3. Check memory
        print("\n--- RAM & Swap Status ---")
        child.sendline("free -h")
        child.expect("dev13@x96q-v1-3:", timeout=15)
        print(child.before.decode('utf-8', errors='ignore').strip())
        
        # 4. Check loaded modules
        print("\n--- Loaded Wi-Fi Modules ---")
        child.sendline("lsmod | grep aic")
        child.expect("dev13@x96q-v1-3:", timeout=15)
        print(child.before.decode('utf-8', errors='ignore').strip())
        
        # 5. Check network interfaces
        print("\n--- Network Interfaces ---")
        child.sendline("ip -4 a")
        child.expect("dev13@x96q-v1-3:", timeout=15)
        print(child.before.decode('utf-8', errors='ignore').strip())
        
        # 6. Check sysctl limits
        print("\n--- RAM sysctl Stability Config ---")
        child.sendline("cat /etc/sysctl.d/99-ram-stability.conf")
        child.expect("dev13@x96q-v1-3:", timeout=15)
        print(child.before.decode('utf-8', errors='ignore').strip())
        
        print("\n====================================================")
        
        child.sendline("exit")
        child.expect(pexpect.EOF)
        
    except Exception as e:
        print(f"Error checking system: {e}")
        print(child.before.decode('utf-8', errors='ignore') if child.before else "")
        sys.exit(1)

if __name__ == "__main__":
    check_new_system()
