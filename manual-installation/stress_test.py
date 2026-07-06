import os
import sys
import time
import multiprocessing
import hashlib

def get_cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return float(f.read().strip()) / 1000.0
    except:
        return 0.0

def get_cpu_times():
    try:
        with open("/proc/stat", "r") as f:
            fields = [float(column) for column in f.readline().strip().split()[1:]]
            idle = fields[3] + fields[4]
            total = sum(fields)
            return idle, total
    except:
        return 0.0, 0.0

def get_mem_info():
    try:
        meminfo = {}
        with open("/proc/meminfo", "r") as f:
            for line in f:
                parts = line.split()
                meminfo[parts[0].replace(":", "")] = int(parts[1])
        total = meminfo["MemTotal"] / 1024 # MB
        free = meminfo["MemFree"] / 1024
        avail = meminfo.get("MemAvailable", meminfo["MemFree"]) / 1024
        used = total - avail
        return total, used, avail
    except:
        return 0.0, 0.0, 0.0

def cpu_worker(duration, cpu_percent, stop_event):
    start = time.time()
    work_ratio = (cpu_percent / 100.0) * 0.1 # Active time out of 100ms
    sleep_ratio = 0.1 - work_ratio # Idle time out of 100ms
    
    while not stop_event.is_set():
        if time.time() - start > duration:
            break
        
        t_work_start = time.time()
        # Busy loop for work_ratio seconds
        while time.time() - t_work_start < work_ratio:
            # Simple CPU intensive work (hash generation)
            hashlib.md5(b"stress_data_load").hexdigest()
        
        # Sleep for the remaining fraction of 100ms
        if sleep_ratio > 0:
            time.sleep(sleep_ratio)

def run_test(duration=60, cpu_percent=10, ram_percent=10):
    output_dir = "/home/dev12/pruebas_de_estres"
    os.makedirs(output_dir, exist_ok=True)
    log_file = os.path.join(output_dir, "resultados_estres.txt")
    
    print(f"=== Controlled Stress Test Started ===")
    print(f"Duration: {duration}s | Target CPU: {cpu_percent}% | Target RAM: {ram_percent}%")
    print(f"Logging to: {log_file}")
    
    # 1. Stress RAM to target percentage
    total, used, avail = get_mem_info()
    target_used = total * (ram_percent / 100.0)
    alloc_mb = int(target_used - used)
    
    print(f"Total RAM: {total:.1f} MB | Currently Used: {used:.1f} MB ({ (used/total)*100.0:.1f}%)")
    
    memory_blocks = []
    if alloc_mb > 0:
        print(f"Target RAM usage: {target_used:.1f} MB ({ram_percent}%)")
        print(f"Allocating additional: {alloc_mb} MB to reach target...")
        try:
            # Allocate memory in 10MB chunks
            for i in range(alloc_mb // 10):
                # Create a 10MB string and fill it to force physical allocation
                block = bytearray(b'\x01' * (10 * 1024 * 1024))
                memory_blocks.append(block)
                if (len(memory_blocks) * 10) % 50 == 0:
                    print(f"Allocated {len(memory_blocks) * 10} MB...")
                time.sleep(0.05)
            
            # Allocate the remaining small chunk if any
            rem_mb = alloc_mb % 10
            if rem_mb > 0:
                block = bytearray(b'\x01' * (rem_mb * 1024 * 1024))
                memory_blocks.append(block)
                
            print(f"RAM Allocation completed! Total allocated: {alloc_mb} MB.")
        except MemoryError:
            print("Error: Out of memory during allocation!")
            sys.exit(1)
    else:
        print(f"Target RAM ({ram_percent}%) is less than or equal to current usage ({ (used/total)*100.0:.1f}%).")
        print("No additional RAM allocation is needed.")
        
    # 2. Stress CPU to target percentage
    stop_event = multiprocessing.Event()
    processes = []
    num_cores = multiprocessing.cpu_count()
    print(f"Spawning {num_cores} CPU workers targeting {cpu_percent}% CPU usage...")
    for _ in range(num_cores):
        p = multiprocessing.Process(target=cpu_worker, args=(duration, cpu_percent, stop_event))
        p.start()
        processes.append(p)
        
    # 3. Monitor and Log
    start_time = time.time()
    last_idle, last_total = get_cpu_times()
    
    with open(log_file, "w") as log:
        log.write("Seg,CPU_Uso_pct,RAM_Usada_MB,RAM_Disponible_MB,CPU_Temp_C\n")
        
        while time.time() - start_time < duration:
            time.sleep(5)
            elapsed = int(time.time() - start_time)
            
            # Calculate CPU percentage
            idle, total = get_cpu_times()
            diff_idle = idle - last_idle
            diff_total = total - last_total
            if diff_total > 0:
                cpu_use = 100.0 * (1.0 - (diff_idle / diff_total))
            else:
                cpu_use = 0.0
            last_idle, last_total = idle, total
            
            # Mem Info
            t_mem, u_mem, a_mem = get_mem_info()
            
            # Temp
            temp = get_cpu_temp()
            
            log_line = f"{elapsed},{cpu_use:.1f},{u_mem:.1f},{a_mem:.1f},{temp:.1f}"
            print(f"Time: {elapsed}s | CPU: {cpu_use:.1f}% | RAM Used: {u_mem:.1f}/{t_mem:.1f} MB | Temp: {temp:.1f}C")
            log.write(log_line + "\n")
            log.flush()
            
    # Stop workers
    stop_event.set()
    for p in processes:
        p.join()
        
    # Release memory
    memory_blocks.clear()
    print("=== Controlled Stress Test Completed successfully! ===")

if __name__ == "__main__":
    # Defaults
    dur = 60
    cpu = 10
    ram = 10
    
    if len(sys.argv) > 1:
        try:
            dur = int(sys.argv[1])
        except:
            pass
    if len(sys.argv) > 2:
        try:
            cpu = int(sys.argv[2])
        except:
            pass
    if len(sys.argv) > 3:
        try:
            ram = int(sys.argv[3])
        except:
            pass
            
    run_test(dur, cpu, ram)
