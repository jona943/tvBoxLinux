import pexpect
import sys

def configure_sudo():
    target_ip = "192.168.1.67"
    
    print(f"\n>>> Connecting to {target_ip} to configure passwordless sudo...")
    ssh_cmd = f"ssh -o StrictHostKeyChecking=no dev12@{target_ip}"
    child = pexpect.spawn(ssh_cmd)
    
    try:
        i = child.expect(["password:", "dev12@x96q-v1-3:"], timeout=15)
        if i == 0:
            child.sendline("dev")
            child.expect("dev12@x96q-v1-3:", timeout=15)
        
        # Write passwordless sudo config
        print("Writing sudoers exception...")
        cmd = 'echo dev | sudo -S sh -c \'echo "dev12 ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/90-dev12 && chmod 440 /etc/sudoers.d/90-dev12\''
        child.sendline(cmd)
        child.expect("dev12@x96q-v1-3:", timeout=15)
        
        child.sendline("exit")
        child.expect(pexpect.EOF)
        print("Passwordless sudo configured successfully!")
        
    except Exception as e:
        print(f"Error configuring sudo: {e}")
        print(child.before.decode('utf-8', errors='ignore') if child.before else "")
        sys.exit(1)
        
    # Test it
    print("\n>>> Testing passwordless sudo...")
    test_child = pexpect.spawn(f"ssh -o StrictHostKeyChecking=no dev12@{target_ip}")
    try:
        test_child.expect("dev12@x96q-v1-3:", timeout=15)
        # sudo -n true checks if sudo can run without prompting
        test_child.sendline("sudo -n true")
        i = test_child.expect(["dev12@x96q-v1-3:", "password"], timeout=15)
        if i == 0:
            print("Passwordless sudo is fully working!")
        else:
            print("Passwordless sudo test failed (prompted for password)!")
            sys.exit(1)
        test_child.sendline("exit")
        test_child.expect(pexpect.EOF)
    except Exception as e:
        print(f"Error testing sudo: {e}")
        sys.exit(1)

if __name__ == "__main__":
    configure_sudo()
