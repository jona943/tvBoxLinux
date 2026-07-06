import sys
import pexpect

def run_ssh(cmd):
    ssh_cmd = "ssh -o StrictHostKeyChecking=no dev12@192.168.1.67"
    child = pexpect.spawn(ssh_cmd)
    
    # Wait for password prompt
    i = child.expect(["password:", pexpect.EOF, pexpect.TIMEOUT], timeout=15)
    if i != 0:
        print("Error: Could not connect to host or prompt not found.")
        print(child.before.decode('utf-8', errors='ignore') if child.before else "")
        return
        
    child.sendline("dev")
    
    # Wait for shell prompt
    i = child.expect(["dev12@x96q-v1-3:", pexpect.EOF, pexpect.TIMEOUT], timeout=15)
    if i != 0:
        print("Error: Login failed or shell prompt not found.")
        print(child.before.decode('utf-8', errors='ignore') if child.before else "")
        return
        
    # Send our command
    child.sendline(cmd)
    
    # Send exit to close the shell
    child.sendline("exit")
    child.expect(pexpect.EOF)
    print(child.before.decode('utf-8', errors='ignore'))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 ssh_run.py <command>")
        sys.exit(1)
    run_ssh(" ".join(sys.argv[1:]))
