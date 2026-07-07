import pexpect
import sys

def apply_sysctl():
    target_ip = "192.168.1.68"
    user = "dev13"
    password = "dev"
    
    print(f"\n>>> Connecting to {user}@{target_ip} to configure RAM stability...")
    ssh_cmd = f"ssh -o StrictHostKeyChecking=no {user}@{target_ip}"
    child = pexpect.spawn(ssh_cmd)
    
    try:
        i = child.expect(["password:", f"{user}@x96q-v1-3:"], timeout=15)
        if i == 0:
            child.sendline(password)
            child.expect(f"{user}@x96q-v1-3:", timeout=15)
            
        print("Writing permanent sysctl config for DRAM stability...")
        sysctl_conf = """# Permanent RAM stability configurations to prevent false DRAM lockups
vm.dirty_background_bytes = 4194304
vm.dirty_bytes = 8388608
"""
        child.sendline(f"sudo tee /etc/sysctl.d/99-ram-stability.conf << 'EOF'\n{sysctl_conf}EOF")
        i = child.expect([f"{user}@x96q-v1-3:", "contrase", "password"], timeout=15)
        if i > 0:
            child.sendline(password)
            child.expect(f"{user}@x96q-v1-3:", timeout=15)
        
        # Apply the new sysctl rules
        print("Applying sysctl rules...")
        child.sendline("sudo sysctl --system")
        i = child.expect([f"{user}@x96q-v1-3:", "contrase", "password"], timeout=15)
        if i > 0:
            child.sendline(password)
            child.expect(f"{user}@x96q-v1-3:", timeout=15)
        
        child.sendline("exit")
        child.expect(pexpect.EOF)
        print("\n>>> sysctl configurations applied successfully!")
        
    except Exception as e:
        print(f"Error applying sysctl: {e}")
        sys.exit(1)

if __name__ == "__main__":
    apply_sysctl()
