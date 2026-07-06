import pexpect
import sys

def scp_all():
    files = [
        "manual-installation/instalar_emmc.sh",
        "manual-installation/instalar_usb.sh",
        "alternative-tests/instalar_emmc_tar.sh"
    ]
    
    # Upload via SCP
    print("Uploading files via SCP...")
    scp_cmd = f"scp -o StrictHostKeyChecking=no {' '.join(files)} dev12@192.168.1.67:/home/dev12/automatizacion/"
    child = pexpect.spawn(scp_cmd)
    
    try:
        child.expect("password:", timeout=15)
        child.sendline("dev")
        child.expect(pexpect.EOF, timeout=30)
        print("SCP transfer complete!")
    except Exception as e:
        print("Error during SCP transfer:")
        print(child.before.decode('utf-8', errors='ignore') if child.before else "")
        sys.exit(1)
        
    # Now connect via SSH to set permissions
    print("Connecting via SSH to set permissions...")
    ssh_cmd = "ssh -o StrictHostKeyChecking=no dev12@192.168.1.67"
    child_ssh = pexpect.spawn(ssh_cmd)
    
    try:
        child_ssh.expect("password:", timeout=15)
        child_ssh.sendline("dev")
        child_ssh.expect("dev12@x96q-v1-3:", timeout=15)
        
        # Sudo change owner and permissions for each file
        for f in files:
            name = f.split("/")[-1]
            dest = f"/home/dev12/automatizacion/{name}"
            
            # Change owner
            child_ssh.sendline(f"echo dev | sudo -S chown root:root {dest}")
            child_ssh.expect("dev12@x96q-v1-3:", timeout=15)
            
            # Change permissions
            child_ssh.sendline(f"echo dev | sudo -S chmod +x {dest}")
            child_ssh.expect("dev12@x96q-v1-3:", timeout=15)
            print(f"Configured root ownership and execution permissions for {name}")
            
        child_ssh.sendline("exit")
        child_ssh.expect(pexpect.EOF)
        print("All scripts uploaded and configured successfully!")
        
    except Exception as e:
        print("Error during SSH configuration:")
        print(child_ssh.before.decode('utf-8', errors='ignore') if child_ssh.before else "")
        sys.exit(1)

if __name__ == "__main__":
    scp_all()
