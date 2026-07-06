import pexpect

def upload():
    # Read local script
    with open("manual-installation/instalar_emmc.sh", "r") as f:
        content = f.read()
        
    # Replace the UBOOT check with the direct DD copy
    old_uboot_section = """# 7. Escribir cargador de arranque U-Boot
echo "[7/7] Escribiendo cargador de arranque U-Boot..."
UBOOT_BIN=$(find ${MOUNT_POINT}/usr/lib/linux-u-boot-* -name "u-boot.bin" | head -n 1)

if [ -n "${UBOOT_BIN}" ]; then
    echo "U-Boot binario encontrado en: ${UBOOT_BIN}"
    dd if="${UBOOT_BIN}" of=${TARGET_DEV} bs=1024 seek=8 conv=fsync,notrunc
    echo "¡U-Boot escrito correctamente!"
else
    echo "ERROR: No se encontró el binario de U-Boot. El sistema podría no arrancar solo."
    exit 1
fi"""

    new_uboot_section = """# 7. Escribir cargador de arranque U-Boot
echo "[7/7] Escribiendo cargador de arranque U-Boot desde la MicroSD (/dev/mmcblk0)..."
dd if=/dev/mmcblk0 of=${TARGET_DEV} bs=1024 skip=8 seek=8 count=1024 conv=fsync,notrunc
echo "¡U-Boot copiado correctamente desde la MicroSD!" """

    content = content.replace(old_uboot_section, new_uboot_section)
    
    # Save the updated script locally too
    with open("manual-installation/instalar_emmc.sh", "w") as f:
        f.write(content)
        
    # Now connect via SSH and write the file
    ssh_cmd = "ssh -o StrictHostKeyChecking=no dev12@192.168.1.67"
    child = pexpect.spawn(ssh_cmd)
    child.expect("password:", timeout=15)
    child.sendline("dev")
    child.expect("dev12@x96q-v1-3:", timeout=15)
    
    # Write the file using cat << 'EOF'
    child.sendline("cat << 'EOF' > /home/dev12/automatizacion/instalar_emmc.sh")
    child.sendline(content)
    child.sendline("EOF")
    child.expect("dev12@x96q-v1-3:", timeout=15)
    
    # Give execution permissions and make it owned by root (via sudo)
    child.sendline("echo dev | sudo -S chown root:root /home/dev12/automatizacion/instalar_emmc.sh")
    child.expect("dev12@x96q-v1-3:", timeout=15)
    child.sendline("echo dev | sudo -S chmod +x /home/dev12/automatizacion/instalar_emmc.sh")
    child.expect("dev12@x96q-v1-3:", timeout=15)
    
    child.sendline("exit")
    child.expect(pexpect.EOF)
    print("Script successfully updated and uploaded to TV Box!")

if __name__ == "__main__":
    upload()
