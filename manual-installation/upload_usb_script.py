import pexpect

def upload():
    # Read local script
    with open("manual-installation/instalar_usb.sh", "r") as f:
        content = f.read()
        
    # Now connect via SSH and write the file
    ssh_cmd = "ssh -o StrictHostKeyChecking=no dev12@192.168.1.67"
    child = pexpect.spawn(ssh_cmd)
    child.expect("password:", timeout=15)
    child.sendline("dev")
    child.expect("dev12@x96q-v1-3:", timeout=15)
    
    # Write the file using cat << 'EOF'
    child.sendline("cat << 'EOF' > /home/dev12/automatizacion/instalar_usb.sh")
    child.sendline(content)
    child.sendline("EOF")
    child.expect("dev12@x96q-v1-3:", timeout=15)
    
    # Give execution permissions and make it owned by root (via sudo)
    child.sendline("echo dev | sudo -S chown root:root /home/dev12/automatizacion/instalar_usb.sh")
    child.expect("dev12@x96q-v1-3:", timeout=15)
    child.sendline("echo dev | sudo -S chmod +x /home/dev12/automatizacion/instalar_usb.sh")
    child.expect("dev12@x96q-v1-3:", timeout=15)
    
    # Also let's upload the updated instalar_emmc.sh script (with ECO mode!)
    with open("manual-installation/instalar_emmc.sh", "r") as f:
        emmc_content = f.read()
        
    child.sendline("cat << 'EOF' > /home/dev12/automatizacion/instalar_emmc.sh")
    child.sendline(emmc_content)
    child.sendline("EOF")
    child.expect("dev12@x96q-v1-3:", timeout=15)
    
    child.sendline("echo dev | sudo -S chown root:root /home/dev12/automatizacion/instalar_emmc.sh")
    child.expect("dev12@x96q-v1-3:", timeout=15)
    child.sendline("echo dev | sudo -S chmod +x /home/dev12/automatizacion/instalar_emmc.sh")
    child.expect("dev12@x96q-v1-3:", timeout=15)
    
    child.sendline("exit")
    child.expect(pexpect.EOF)
    print("Both scripts (USB and EMMC with ECO mode) successfully uploaded to TV Box!")

if __name__ == "__main__":
    upload()
