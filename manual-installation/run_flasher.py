import pexpect
import sys

def run_flasher():
    ssh_cmd = "ssh -o StrictHostKeyChecking=no dev12@192.168.1.67"
    child = pexpect.spawn(ssh_cmd)
    
    # Send all child output directly to stdout in real-time
    child.logfile = sys.stdout.buffer
    
    try:
        # Wait for password prompt
        child.expect("password:", timeout=15)
        child.sendline("dev")
        
        # Wait for shell prompt
        child.expect("dev12@x96q-v1-3:", timeout=15)
        
        # Execute the raw flash script with sudo
        print("\n>>> Launching raw_flash.py on TV Box...")
        child.sendline("echo dev | sudo -S python3 /home/dev12/automatizacion/raw_flash.py")
        
        # Expect the completion message or EOF with a 15-minute timeout
        # 1316 MB / 2 MB/s = ~660 seconds. 900 seconds is safe.
        child.expect("=== INSTALLATION COMPLETED SUCCESSFULLY ===", timeout=1000)
        
        # Wait a bit and exit
        child.expect("dev12@x96q-v1-3:", timeout=30)
        child.sendline("exit")
        child.expect(pexpect.EOF, timeout=10)
        print("\n>>> Flashing finished successfully!")
        
    except pexpect.TIMEOUT:
        print("\n>>> Error: Timeout reached during process. Output so far:")
        sys.exit(1)
    except Exception as e:
        print(f"\n>>> Error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_flasher()
