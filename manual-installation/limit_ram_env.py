import pexpect
import sys

def limit_ram():
    target_ip = "192.168.1.68"
    user = "dev13"
    password = "dev"
    
    print(f"\n>>> Connecting to {user}@{target_ip} to limit reported RAM to 1GB...")
    ssh_cmd = f"ssh -o StrictHostKeyChecking=no {user}@{target_ip}"
    child = pexpect.spawn(ssh_cmd)
    
    try:
        i = child.expect(["password:", f"{user}@x96q-v1-3:"], timeout=15)
        if i == 0:
            child.sendline(password)
            child.expect(f"{user}@x96q-v1-3:", timeout=15)
            
        print("Reading /boot/armbianEnv.txt...")
        child.sendline("cat /boot/armbianEnv.txt")
        child.expect(f"{user}@x96q-v1-3:", timeout=15)
        
        content = child.before.decode('utf-8', errors='ignore')
        
        # Check if extraargs is already present
        if "extraargs=" in content:
            print("extraargs found. Modifying existing line...")
            # We append mem=1024M to the existing extraargs line
            cmd = "sudo sed -i 's/^extraargs=\\(.*\\)/extraargs=\\1 mem=1024M/' /boot/armbianEnv.txt"
        else:
            print("extraargs not found. Appending to file...")
            # We append a new line at the end
            cmd = "echo 'extraargs=mem=1024M' | sudo tee -a /boot/armbianEnv.txt"
            
        child.sendline(cmd)
        i = child.expect([f"{user}@x96q-v1-3:", "contrase", "password"], timeout=15)
        if i > 0:
            child.sendline(password)
            child.expect(f"{user}@x96q-v1-3:", timeout=15)
            
        print("RAM limit configured in /boot/armbianEnv.txt. Rebooting system...")
        child.sendline("sudo reboot")
        i = child.expect([f"{user}@x96q-v1-3:", "contrase", "password"], timeout=15)
        if i > 0:
            child.sendline(password)
            child.expect(pexpect.EOF, timeout=15)
        else:
            child.expect(pexpect.EOF, timeout=15)
            
        print("\n>>> System reboot initiated. RAM is now limited to 1GB!")
        
    except Exception as e:
        print(f"Error configuring RAM limit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    limit_ram()
