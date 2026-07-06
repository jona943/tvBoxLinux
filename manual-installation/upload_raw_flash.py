import pexpect
import sys
import os

def upload_raw_flash():
    image_src = "downloads/Armbian-unofficial_26.02.0-trunk_X96q-v1-3_bookworm_current_6.12.64_minimal.img.xz"
    script_src = "manual-installation/raw_flash.py"
    
    if not os.path.exists(image_src):
        print(f"Error: {image_src} not found on Host PC.")
        sys.exit(1)
        
    print("Step 1: Uploading the 250MB raw image via SCP...")
    scp_img_cmd = f"scp -o StrictHostKeyChecking=no {image_src} dev12@192.168.1.67:/home/dev12/"
    child1 = pexpect.spawn(scp_img_cmd)
    
    try:
        child1.expect("password:", timeout=15)
        child1.sendline("dev")
        # Give it a long timeout for 250MB transfer
        child1.expect(pexpect.EOF, timeout=400)
        print("Raw image uploaded successfully!")
    except Exception as e:
        print("Error during raw image upload:")
        print(child1.before.decode('utf-8', errors='ignore') if child1.before else "")
        sys.exit(1)
        
    print("Step 2: Uploading the raw_flash.py script via SCP...")
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
        
    print("Step 3: Setting permissions on TV Box...")
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
        print("Permissions configured! All ready for raw flashing!")
        
    except Exception as e:
        print("Error configuring permissions:")
        print(child3.before.decode('utf-8', errors='ignore') if child3.before else "")
        sys.exit(1)

if __name__ == "__main__":
    upload_raw_flash()
