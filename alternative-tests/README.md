# Pruebas Alternativas para Resolver Bloqueos (DRAM / IO Hangs)

Esta carpeta contiene la documentación y herramientas para probar dos hipótesis críticas que explican el congelamiento del sistema durante operaciones sostenidas de escritura:

*   **Hipótesis A:** Sobrecarga de la controladora de memoria RAM (DRAM Hang) debido al uso de `rsync` (accesos aleatorios intensivos y caché masiva).
*   **Hipótesis B:** Inestabilidad física por timings de memoria LPDDR3 incorrectos (placa con chips DDR3 corriendo firmware LPDDR3).

---

## Opción A: Copiado por Streaming Secuencial (`tar`)

`rsync` realiza búsquedas aleatorias en disco y construye árboles de metadatos en RAM, lo que genera alta carga de CPU e inestabilidad de bus. 
Para mitigar esto, usaremos **`tar`**, que lee el disco origen secuencialmente y lo escribe de forma directa en el destino, con consumo de RAM y CPU insignificante.

### Script de Prueba: `instalar_emmc_tar.sh`
Se ha creado un script especializado en esta carpeta que realiza exactamente los mismos pasos de particionado, formateo y escritura de U-Boot, pero reemplaza `rsync` con:

```bash
cd /
tar --one-file-system --exclude='./home/dev12/automatizacion' -cf - . | tar -xf - -C /mnt/emmc
```

### Instrucciones de uso:
1. Inicia la TV Box desde la MicroSD.
2. Copia este script a la TV Box o ejecútalo directamente.
3. Comando a ejecutar:
   ```bash
   sudo ./instalar_emmc_tar.sh
   ```

---

## Opción B: Probar la Imagen con Configuración DDR3 (`X96q-v5-1`)

Si el método `tar` de la Opción A también se congela con el cursor estático, es casi seguro que tu TV Box tiene chips físicos **DDR3** y los timings de la imagen `X96q-v1-3` (LPDDR3) están provocando corrupción de memoria bajo cualquier flujo de datos.

### Instrucciones para probar:
1. Descarga la imagen minimalista de DDR3 en tu PC Host:
   ```bash
   wget -P /home/dev-jonathan/Escritorio/entorno-prueba/tvBoxLinux/downloads/ https://github.com/sicXnull/armbian-build/releases/download/v24.8.0-trunk.425/Armbian-unofficial_26.02.0-trunk_X96q-v5-1_bookworm_current_6.12.64_minimal.img.xz
   ```
2. Flashea la imagen descargada en tu tarjeta MicroSD usando BalenaEtcher.
3. Inserta la MicroSD en la TV Box y enciéndela.
   *   **Resultado 1 (No arranca):** Si la TV Box no inicia o se queda en pantalla negra, tu placa sí es LPDDR3 (v1.3) y la causa sigue siendo eléctrica/PMIC.
   *   **Resultado 2 (Inicia y es estable):** Si inicia, procede a ejecutar el script de instalación en la eMMC. Al tener los timings correctos, la copia no se colgará y completará con éxito.
