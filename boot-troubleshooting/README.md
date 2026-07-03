# Diagnóstico de Arranque y Solución de Pantalla Negra (Allwinner H313)

Este documento registra el problema de bloqueo visual encontrado durante el primer arranque de Armbian en la TV Box china Mortal T1 (SoC Allwinner H313) y la solución aplicada para restablecer el control del dispositivo.

---

## 1. El Problema (Síntomas)
Tras completar el asistente inicial de creación de usuario en el primer arranque de Armbian (MATE Desktop / Kernel 6.6.44), la pantalla del televisor/monitor se quedó en negro con un cursor de texto fijo (congelado) en la esquina superior izquierda. Las combinaciones de teclas tradicionales (`Ctrl + Alt + F2` a `F6`) para acceder a otras TTYs no respondieron.

### Conflicto Probable:
1. **Fallo en la Aceleración Gráfica (GPU/HDMI):** El servidor gráfico Xorg o el Display Manager (LightDM) intentó cargar el entorno de escritorio MATE usando controladores que no son compatibles con el motor de pantalla o la GPU Mali-G31 del chip Allwinner H313 bajo la configuración de pantalla HDMI genérica.
2. **Desajuste del Device Tree (DTB):** Al no especificar una versión exacta del DTB, el sistema cargó una configuración genérica que no inicializó de manera correcta las controladoras USB y de video de la placa, provocando que la interfaz fallara y el teclado dejara de funcionar.

---

## 2. Solución Temporal Aplicada
Para eludir el entorno gráfico problemático y poder configurar la red, el Wi-Fi y habilitar la administración remota (SSH), se configuró la TV Box para **arrancar directamente en modo texto (Consola)** y se forzó el uso del archivo **DTB adecuado** para el chip H313 de la X96Q.

Esto se logró modificando el archivo de configuración `/boot/armbianEnv.txt` de la partición de arranque de la tarjeta MicroSD.

---

## 3. Parámetros Modificados en `/boot/armbianEnv.txt`

| Parámetro | Valor Asignado | ¿Para qué sirve? | Propósito en esta solución |
| :--- | :--- | :--- | :--- |
| **`fdtfile`** | `allwinner/sun50i-h313-x96q-lpddr3.dtb` | Especifica el archivo Device Tree Blob (DTB) que describe la placa física. | Fuerza al sistema a usar la descripción de hardware correspondiente al chip Allwinner H313 (revisión LPDDR3), asegurando la compatibilidad de los buses e interfaces de la TV Box. |
| **`extraargs`** | `systemd.unit=multi-user.target` | Permite pasar argumentos adicionales al kernel de Linux en el arranque. | Modifica el nivel de ejecución predeterminado (Target de Systemd) al modo multiusuario sin interfaz gráfica. Evita que cargue LightDM y levanta directamente una consola de comandos interactiva. |

---

## 4. Configuración Relacionada en el Host (`udev` rules)
Durante la etapa de diagnóstico preliminar desde el sistema host, se detectó que el comando `adb devices` no listaba la TV Box debido a la falta de permisos de escritura del usuario de escritorio sobre los archivos USB del sistema (`/dev/bus/usb/...`).

### Solución de Permisos en el Host:
Se creó la regla de udev en `/etc/udev/rules.d/51-allwinner.rules` para otorgar permisos de lectura y escritura al grupo de dispositivos `plugdev` (al que pertenece tu usuario) sobre cualquier dispositivo Allwinner (`Vendor ID: 1f3a`):

```udev
# Allwinner Tech (Mortal T1 y otros) - Reglas para ADB y MTP
SUBSYSTEM=="usb", ATTR{idVendor}=="1f3a", MODE="0666", GROUP="plugdev"
```

---

## 5. Próximos Pasos tras Iniciar en Modo Consola
Una vez que el dispositivo inicie en modo texto y se pueda iniciar sesión como `root`:
1. **Conectar a Internet (Wi-Fi):**
   ```bash
   nmtui
   ```
   *(Seleccionar "Activate a connection" y seleccionar la red Wi-Fi).*
2. **Habilitar SSH para Acceso Remoto:**
   ```bash
   systemctl enable --now ssh
   ```
3. **Revisar Logs de Pantalla:**
   Analizar `/var/log/Xorg.0.log` o `journalctl -u lightdm` para descubrir por qué falló el inicio gráfico.
