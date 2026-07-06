import pexpect
import sys

def upload():
    scp_cmd = "scp -o StrictHostKeyChecking=no manual-installation/stress_test.py dev12@192.168.1.67:/home/dev12/pruebas_de_estres/"
    child = pexpect.spawn(scp_cmd)
    
    try:
        child.expect("password:", timeout=15)
        child.sendline("dev")
        child.expect(pexpect.EOF, timeout=30)
        print("stress_test.py uploaded successfully!")
    except Exception as e:
        print("Error during script upload:")
        print(child.before.decode('utf-8', errors='ignore') if child.before else "")
        sys.exit(1)
        
    # Make it executable
    ssh_cmd = "ssh -o StrictHostKeyChecking=no dev12@192.168.1.67"
    child2 = pexpect.spawn(ssh_cmd)
    try:
        child2.expect("password:", timeout=15)
        child2.sendline("dev")
        child2.expect("dev12@x96q-v1-3:", timeout=15)
        child2.sendline("chmod +x /home/dev12/pruebas_de_estres/stress_test.py")
        child2.expect("dev12@x96q-v1-3:", timeout=15)
        child2.sendline("exit")
        child2.expect(pexpect.EOF)
        print("Permissions set on TV Box!")
    except Exception as e:
        print("Error setting permissions:")
        print(child2.before.decode('utf-8', errors='ignore') if child2.before else "")
        sys.exit(1)

if __name__ == "__main__":
    upload()
