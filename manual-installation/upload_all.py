import pexpect
import os

def upload_all():
    # Make sure we are in tvBoxLinux directory
    scripts = {
        "instalar_emmc.sh": "manual-installation/instalar_emmc.sh",
        "instalar_emmc_tar.sh": "alternative-tests/instalar_emmc_tar.sh",
        "instalar_usb.sh": "manual-installation/instalar_usb.sh"
    }
    
    # Read files
    content_map = {}
    for name, path in scripts.items():
        if os.path.exists(path):
            with open(path, "r") as f:
                content_map[name] = f.read()
        else:
            print(f"Warning: {path} not found.")

    # Connect via SSH
    ssh_cmd = "ssh -o StrictHostKeyChecking=no dev12@192.168.1.67"
    child = pexpect.spawn(ssh_cmd)
    child.expect("password:", timeout=15)
    child.sendline("dev")
    child.expect("dev12@x96q-v1-3:", timeout=15)
    
    # Create directory ~/automatizacion
    child.sendline("mkdir -p /home/dev12/automatizacion")
    child.expect("dev12@x96q-v1-3:", timeout=15)
    
    # Upload each file
    for name, content in content_map.items():
        dest = f"/home/dev12/automatizacion/{name}"
        child.sendline(f"cat << 'EOF' > {dest}")
        child.sendline(content)
        child.sendline("EOF")
        child.expect("dev12@x96q-v1-3:", timeout=15)
        
        # Sudo permissions
        child.sendline(f"echo dev | sudo -S chown root:root {dest}")
        child.expect("dev12@x96q-v1-3:", timeout=15)
        child.sendline(f"echo dev | sudo -S chmod +x {dest}")
        child.expect("dev12@x96q-v1-3:", timeout=15)
        print(f"Uploaded and configured: {name}")
        
    child.sendline("exit")
    child.expect(pexpect.EOF)
    print("All scripts uploaded successfully to the new TV Box system!")

if __name__ == "__main__":
    upload_all()
