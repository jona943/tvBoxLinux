import pexpect
import sys

def run_stress():
    # Extract arguments from command line or default to 90s, 10% CPU, 10% RAM
    dur = sys.argv[1] if len(sys.argv) > 1 else "90"
    cpu = sys.argv[2] if len(sys.argv) > 2 else "10"
    ram = sys.argv[3] if len(sys.argv) > 3 else "10"

    ssh_cmd = "ssh -o StrictHostKeyChecking=no dev12@192.168.1.67"
    child = pexpect.spawn(ssh_cmd)
    
    # Stream output to stdout in real-time
    child.logfile = sys.stdout.buffer
    
    try:
        child.expect("password:", timeout=15)
        child.sendline("dev")
        child.expect("dev12@x96q-v1-3:", timeout=15)
        
        print(f"\n>>> Launching stress_test.py (duration={dur}s, cpu={cpu}%, ram={ram}%) on TV Box...")
        child.sendline(f"python3 /home/dev12/pruebas_de_estres/stress_test.py {dur} {cpu} {ram}")
        
        # Expect the completion message or EOF with a 3-minute timeout
        child.expect("=== Controlled Stress Test Completed successfully! ===", timeout=180)
        
        child.expect("dev12@x96q-v1-3:", timeout=15)
        child.sendline("exit")
        child.expect(pexpect.EOF, timeout=10)
        print("\n>>> Stress test finished successfully!")
        
    except pexpect.TIMEOUT:
        print("\n>>> Error: Timeout reached during stress test. TV Box might have frozen.")
        sys.exit(1)
    except Exception as e:
        print(f"\n>>> Error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_stress()
