import pexpect
import sys

def upload_only_flasher():
    script_src = "manual-installation/raw_flash.py"
    
    print("Uploading the updated raw_flash.py script via SCP...")
    scp_script_cmd = f"scp -o StrictHostKeyChecking=no {script_src} dev12@192.168.1.67:/home/dev12/automatizacion/"
    child2 = pexpect.spawn(scp_script_cmd)
    
    try:
        child2.expect("password:", timeout=15)
        child2.sendline("dev")
        child2.expect(pexpect.EOF, timeout=30)
        print("Script uploaded successfully!")
    except Exception as e:
        print("Error during script upload:")
        print(child2.before.decode('utf-8', errors='ignore') if child2.before else "")
        sys.exit(1)
        
    print("Setting permissions on TV Box...")
    ssh_cmd = "ssh -o StrictHostKeyChecking=no dev12@192.168.1.67"
    child3 = pexpect.spawn(ssh_cmd)
    
    try:
        child3.expect("password:", timeout=15)
        child3.sendline("dev")
        child3.expect("dev12@x96q-v1-3:", timeout=15)
        
        # Give raw_flash.py root permissions
        child3.sendline("echo dev | sudo -S chown root:root /home/dev12/automatizacion/raw_flash.py")
        child3.expect("dev12@x96q-v1-3:", timeout=15)
        child3.sendline("echo dev | sudo -S chmod +x /home/dev12/automatizacion/raw_flash.py")
        child3.expect("dev12@x96q-v1-3:", timeout=15)
        
        child3.sendline("exit")
        child3.expect(pexpect.EOF)
        print("Permissions configured successfully!")
        
    except Exception as e:
        print("Error configuring permissions:")
        print(child3.before.decode('utf-8', errors='ignore') if child3.before else "")
        sys.exit(1)

if __name__ == "__main__":
    upload_only_flasher()
