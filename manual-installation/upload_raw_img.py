import pexpect
import sys
import os

def upload_raw_img():
    image_src = "downloads/Armbian-unofficial_26.02.0-trunk_X96q-v1-3_bookworm_current_6.12.64_minimal.img"
    
    if not os.path.exists(image_src):
        print(f"Error: {image_src} not found on Host PC.")
        sys.exit(1)
        
    print("Uploading the 1.3 GB uncompressed image via SCP (this will take 10-15 minutes)...")
    scp_cmd = f"scp -o StrictHostKeyChecking=no {image_src} dev12@192.168.1.67:/home/dev12/"
    child = pexpect.spawn(scp_cmd)
    
    # Stream SCP progress to stdout in real-time
    child.logfile = sys.stdout.buffer
    
    try:
        child.expect("password:", timeout=15)
        child.sendline("dev")
        
        # 1500 seconds (25 minutes) timeout for the 1.3 GB transfer
        child.expect(pexpect.EOF, timeout=1500)
        print("\n>>> Uncompressed image uploaded successfully!")
    except Exception as e:
        print("\n>>> Error during image upload:")
        print(child.before.decode('utf-8', errors='ignore') if child.before else "")
        sys.exit(1)

if __name__ == "__main__":
    upload_raw_img()
