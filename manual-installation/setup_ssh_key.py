import os
import pexpect
import sys

def setup_ssh_key():
    target_ip = "192.168.1.67"
    ssh_dir = os.path.expanduser("~/.ssh")
    pub_key_path = os.path.join(ssh_dir, "id_rsa.pub")
    priv_key_path = os.path.join(ssh_dir, "id_rsa")
    
    # 1. Generate SSH key if it doesn't exist
    if not os.path.exists(pub_key_path):
        print("SSH key not found on Host PC. Generating one...")
        os.makedirs(ssh_dir, exist_ok=True)
        gen_cmd = f'ssh-keygen -t rsa -N "" -f {priv_key_path}'
        os.system(gen_cmd)
        print("SSH key generated successfully.")
        
    # Read the public key
    with open(pub_key_path, "r") as f:
        pub_key = f.read().strip()
        
    print(f"\n>>> Connecting to {target_ip} to authorize key...")
    ssh_cmd = f"ssh -o StrictHostKeyChecking=no dev12@{target_ip}"
    child = pexpect.spawn(ssh_cmd)
    
    try:
        # Expect password prompt
        child.expect("password:", timeout=15)
        child.sendline("dev")
        child.expect("dev12@x96q-v1-3:", timeout=15)
        
        # Create directories and append key
        child.sendline("mkdir -p ~/.ssh && chmod 700 ~/.ssh")
        child.expect("dev12@x96q-v1-3:", timeout=15)
        
        # Append the key using echo
        # We escape single quotes if any (should not be in pub key)
        child.sendline(f"echo '{pub_key}' >> ~/.ssh/authorized_keys")
        child.expect("dev12@x96q-v1-3:", timeout=15)
        
        child.sendline("chmod 600 ~/.ssh/authorized_keys")
        child.expect("dev12@x96q-v1-3:", timeout=15)
        
        child.sendline("exit")
        child.expect(pexpect.EOF)
        print("Public key authorized successfully on TV Box!")
        
    except Exception as e:
        print(f"Error authorizing SSH key: {e}")
        print(child.before.decode('utf-8', errors='ignore') if child.before else "")
        sys.exit(1)
        
    # 2. Test passwordless login
    print("\n>>> Testing passwordless connection...")
    test_cmd = f"ssh -o StrictHostKeyChecking=no -o PasswordAuthentication=no dev12@{target_ip} 'echo Connection successful!'"
    child2 = pexpect.spawn(test_cmd)
    try:
        i = child2.expect(["Connection successful!", pexpect.TIMEOUT, pexpect.EOF], timeout=15)
        if i == 0:
            print("Passwordless SSH connection is fully working!")
        else:
            print("Passwordless connection test failed!")
            print(child2.before.decode('utf-8', errors='ignore') if child2.before else "")
            sys.exit(1)
    except Exception as e:
        print(f"Error testing passwordless connection: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_ssh_key()
