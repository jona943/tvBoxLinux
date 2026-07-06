import pexpect
import sys

def download_results(local_name):
    remote_path = "/home/dev12/pruebas_de_estres/resultados_estres.txt"
    local_path = f"stress-tests-reports/{local_name}"
    
    scp_cmd = f"scp -o StrictHostKeyChecking=no dev12@192.168.1.67:{remote_path} {local_path}"
    child = pexpect.spawn(scp_cmd)
    
    try:
        child.expect("password:", timeout=15)
        child.sendline("dev")
        child.expect(pexpect.EOF, timeout=30)
        print(f"Results downloaded successfully to {local_path}!")
    except Exception as e:
        print("Error downloading results:")
        print(child.before.decode('utf-8', errors='ignore') if child.before else "")
        sys.exit(1)

if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "resultados_estres_10pct.csv"
    download_results(name)
