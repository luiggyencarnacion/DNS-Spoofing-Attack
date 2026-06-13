# 🕵️ DNS Spoofing / DNS Poisoning

**Luiggy Habraham Encarnación Cabrera · Matrícula 2025-0663**

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Kali%20Linux-557C94?style=for-the-badge&logo=linux&logoColor=white)
![Library](https://img.shields.io/badge/Library-Scapy-FF6F00?style=for-the-badge)
![Emulator](https://img.shields.io/badge/Emulador-GNS3-009639?style=for-the-badge)
![Layer](https://img.shields.io/badge/Capa%20OSI-7%20(Aplicación)-E53935?style=for-the-badge)
![License](https://img.shields.io/badge/Uso-Educativo-blue?style=for-the-badge)

> Intercepción de consultas DNS mediante ARP MitM y respuesta con registros A falsificados, redirigiendo a la víctima hacia un servidor web controlado por el atacante sin que la URL en el navegador cambie.

---

## ⚠️ Aviso Legal

> [!CAUTION]
> Este repositorio tiene fines **exclusivamente académicos y educativos**.
> Todo el contenido fue ejecutado en un entorno de laboratorio virtualizado y controlado.
> La reproducción de estas técnicas en redes sin autorización expresa es **ilegal**.

---

## 📑 Tabla de Contenido

1. [Objetivo del Laboratorio](#-objetivo-del-laboratorio)
2. [Descripción de la Vulnerabilidad](#-descripción-de-la-vulnerabilidad)
3. [Requisitos](#-requisitos)
4. [Instalación](#️-instalación)
5. [Documentación de la Red](#️-documentación-de-la-red)
6. [Funcionamiento del Ataque](#-funcionamiento-del-ataque)
7. [Parámetros del Ataque](#-parámetros-del-ataque)
8. [Ejecución](#-ejecución)
9. [Impacto Demostrado](#-impacto-demostrado)
10. [Contramedidas](#-contramedidas)
11. [Capturas de Pantalla](#-capturas-de-pantalla)
12. [Video de Demostración](#-video-de-demostración)

---

## 🎯 Objetivo del Laboratorio

Interceptar las consultas DNS de la víctima hacia el registro `itla.edu.do` y responder con la dirección IP de un servidor web controlado por el atacante corriendo localmente en KaliLinux-1, redirigiendo al usuario a una página falsa sin que la dirección en el navegador cambie. El ataque combina envenenamiento ARP para posicionarse como intermediario (*Man-in-the-Middle*) con una respuesta DNS falsificada construida con Scapy que incluye el Transaction ID correcto de la consulta interceptada.

---

## 🔬 Descripción de la Vulnerabilidad

El protocolo **DNS** no implementa mecanismos de autenticación en su forma base (RFC 1034/1035). Las respuestas DNS son aceptadas por el cliente si:

1. Llegan **antes** que la respuesta legítima
2. El **Transaction ID** coincide con el de la consulta

Al combinarlo con un ataque ARP MitM previo, el atacante ya se encuentra en el camino del tráfico, garantizando que sus respuestas DNS falsas lleguen primero y con el Transaction ID correcto — ya que intercepta la consulta original antes de que salga hacia los servidores `8.8.8.8` o `1.1.1.1` configurados por DHCP en R-1.

---

## 📋 Requisitos

| Requisito | Detalle |
|---|---|
| Sistema operativo | Kali Linux 2023 o superior |
| Python | 3.10 o superior |
| Librería Scapy | `scapy >= 2.5.0` |
| Privilegios | `sudo` / `root` obligatorio (acceso a Capa 2) |
| Emulador de red | GNS3 con Cisco IOU |
| Servidor web | Python `http.server` o Apache2 en Kali |
| Conocimientos previos | DNS, ARP, modelos OSI/TCP-IP, redes IP |

---

## ⚙️ Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/luiggyencarnacion/DNS-Spoofing-Attack.git
cd DNS-Spoofing-Attack

# 2. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Verificar
python3 -c "from scapy.all import ARP, DNS, DNSRR; print('Scapy OK')"
```

**`requirements.txt`**
```
scapy>=2.5.0
```

---

## 🗺️ Documentación de la Red

### Topología — DNS Spoofing con ARP MitM

```
                        ┌──────────┐
              Internet  │  Cloud1  │  8.8.8.8 / 1.1.1.1
                        └────┬─────┘  (DNS legítimo)
                             │
                        ┌────┴─────┐
                        │   R-1    │  10.6.63.65 (GW VLAN 20)
                        └────┬─────┘
                             │
                        ┌────┴──────┐
                        │  SW-CORE  │
                        └───┬───────┘
                            │
                       ┌────┴──────┐
                       │   SW-1    │
                       └──┬────┬───┘
                  Gig1/0  │    │  Gig0/3
              ┌───────────┘    └──────────────┐
         ┌────┴──────┐                  ┌──────┴──────────┐
         │   PC1     │                  │  KaliLinux-1    │
         │  Víctima  │                  │  Atacante DNS   │
         │10.6.63.16 │                  │  10.6.63.13     │
         └───────────┘                  └─────────────────┘
                                         Servidor web falso
                                         itla.edu.do → 10.6.63.13

Flujo del ataque:
  PC1 ──ARP envenenado──► KaliLinux-1 ──► R-1 (forward legítimo)
  PC1 ──DNS query──► KaliLinux-1 ──[intercepta]──► respuesta falsa
  PC1 ──HTTP──► 10.6.63.13 (página falsa de ITLA)
```

### Parámetros Generales

| Parámetro | Valor |
|---|---|
| Red VLAN 10 (ADMIN) | 10.6.63.0/26 |
| Red VLAN 20 (VENTAS) | 10.6.63.64/26 |
| Red VLAN 99 (GESTION) | 10.6.63.128/26 |
| Gateway VLAN 20 | 10.6.63.65 |
| Emulador | GNS3 con Cisco IOU |
| Plataforma de ataque | Kali Linux |
| Herramientas | Scapy (Python), servidor web local |

### Tabla de Direccionamiento

| Dispositivo | Interfaz | Conectado a | Dirección IP | Rol |
|---|---|---|---|---|
| R-1 | g0/0 | SW-CORE Gig0/0 | 10.6.63.65 | Gateway VLAN 20 / DHCP |
| R-1 | g1/0 | Cloud1 eth0 | DHCP (ISP) | Enlace NAT |
| SW-CORE | Gig0/0 | R-1 g0/0 | 10.6.63.130/26 | Root Bridge / VTP Server |
| SW-1 | Gig0/0 | SW-CORE Gig0/1 | 10.6.63.131/26 | Troncal uplink |
| SW-1 | Gig1/0 | PC1 e0 | DHCP VLAN 10 | Puerto acceso VLAN 10 |
| SW-1 | Gig0/3 | KaliLinux-1 e0 | — | Puerto acceso VLAN 20 (Atacante DNS) |
| KaliLinux-1 | e0 | SW-1 Gig0/3 | 10.6.63.13/26 | Atacante DNS Spoofing |
| PC1 | e0 | SW-1 Gig1/0 | DHCP 10.6.63.x/26 | Víctima — VLAN 10 (ADMIN) |
| PC2 | e0 | SW-2 Gig1/0 | DHCP 10.6.63.x/26 | Víctima — VLAN 20 (VENTAS) |

---

## 🔬 Funcionamiento del Ataque

El ataque se ejecuta en tres fases secuenciales desde KaliLinux-1.

### Fase 1 — ARP Man-in-the-Middle

```
KaliLinux-1
    │
    ├─► ARP Reply a Víctima:
    │   "La MAC de R-1 (10.6.63.65) es: [MAC de Kali]"
    │
    └─► ARP Reply a R-1:
        "La MAC de Víctima (10.6.63.x) es: [MAC de Kali]"

Resultado:
  Todo el tráfico Víctima ↔ R-1 pasa por KaliLinux-1
  IP Forwarding habilitado → tráfico no DNS se reenvía normalmente
```

### Fase 2 — Servidor Web Falso

```bash
# Servir página falsa de ITLA en el puerto 80
cd /var/www/html
sudo python3 -m http.server 80
# o
sudo service apache2 start
```

### Fase 3 — Intercepción y Respuesta DNS Falsa

```
Víctima                  KaliLinux-1               Internet
   │                          │                        │
   │── DNS Query ─────────────►│                        │
   │   "itla.edu.do ?"        │                        │
   │                          │  [intercepta el paquete]
   │                          │  [construye respuesta con]
   │                          │  [Transaction ID correcto]
   │◄─ DNS Response ──────────│                        │
   │   "itla.edu.do = 10.6.63.13"                      │
   │                          │                        │
   │── HTTP GET / ────────────────────────────────────►│
   │   Host: itla.edu.do      │                        │
   │   → Resuelve a 10.6.63.13 → carga página de Kali  │
```

---

## ⚙️ Parámetros del Ataque

| Parámetro | Descripción |
|---|---|
| `target_ip` | IP de la víctima (DHCP VLAN 20 — 10.6.63.64/26) |
| `gateway_ip` | Gateway VLAN 20 (`10.6.63.65`) |
| `spoofed_domain` | Dominio a suplantar (`itla.edu.do`) |
| `fake_ip` | IP del servidor web falso (KaliLinux-1 — `10.6.63.13`) |
| `interface` | Interfaz del atacante (`e0`) — SW-1 Gig0/3 |
| `web_server_port` | Puerto del servidor web local (`80`) |

---

## 🚀 Ejecución

```bash
# 1. Habilitar IP Forwarding (para no interrumpir el tráfico legítimo)
echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward

# 2. Levantar el servidor web falso
sudo python3 -m http.server 80
# o en segundo plano:
sudo python3 -m http.server 80 &

# 3. Ejecutar el script de ARP MitM + DNS Spoofing
sudo python3 dns_spoofing.py
```

**Interacción esperada:**

```
DNS Spoofing / DNS Poisoning
──────────────────────────────────────────
Interfaz  : eth0
Víctima   : 10.6.63.16
Gateway   : 10.6.63.1
Dominio   : itla.edu.do
IP Falsa  : 10.6.63.13
TTL       : 60s

[*] Resolviendo MACs...
MAC Víctima  : 00:0c:29:db:f4:db
MAC Gateway  : ca:01:0c:f7:00:08
MAC Atacante : 00:0c:29:1b:ee:fc

[*] IP Forwarding habilitado
[*] Iniciando ARP Poisoning + DNS Spoofing...

Tiempo   Cliente        Dominio        IP Falsa       Estado
──────────────────────────────────────────────────────────────
00:17    10.6.63.16     itla.edu.do    10.6.63.13     ✓
```

### Comandos de verificación

```bash
# En la víctima — verificar resolución DNS incorrecta
PC> nslookup itla.edu.do
# Resultado esperado: Address: 10.6.63.13 (IP del atacante)

# En KaliLinux-1 — monitorear tráfico DNS interceptado
sudo tcpdump -i e0 udp port 53
sudo wireshark

# En KaliLinux-1 — verificar servidor web activo
sudo ss -tlnp | grep :80
```

---

## 💥 Impacto Demostrado

- La víctima resuelve `itla.edu.do` a la IP de KaliLinux-1 en lugar del servidor legítimo
- El navegador de la víctima carga la **página web falsa** alojada en Kali
- La **barra de direcciones** del navegador muestra `itla.edu.do` sin indicación de anomalía
- Interceptación visible en Wireshark: paquete DNS Response con **registro A falsificado**

---

## 🔐 Contramedidas

### 1. DHCP Snooping + Dynamic ARP Inspection (DAI)

El DNS Spoofing en este escenario depende completamente del ARP MitM como vector inicial. Sin la posición de intermediario, KaliLinux-1 no puede interceptar ni responder consultas DNS antes que los servidores legítimos.

```bash
! Habilitar DHCP Snooping en VLANs
ip dhcp snooping
ip dhcp snooping vlan 10,20,99
no ip dhcp snooping information option

! Habilitar DAI en VLANs
ip arp inspection vlan 10,20,99

! Marcar como trusted el uplink hacia R-1 en SW-CORE
interface GigabitEthernet0/0
 ip dhcp snooping trust
 ip arp inspection trust
exit

! Marcar como trusted los uplinks troncales en SW-1 y SW-2
interface GigabitEthernet0/0
 ip dhcp snooping trust
 ip arp inspection trust
exit
```

**DAI** valida cada respuesta ARP contra la binding table de DHCP Snooping, descartando respuestas cuya combinación IP-MAC no coincida con una asignación DHCP legítima.

### 2. DNSSEC (defensa en profundidad)

```bash
# Verificar si el dominio tiene DNSSEC habilitado
dig itla.edu.do +dnssec
dig itla.edu.do DS
```

DNSSEC permite a los clientes verificar criptográficamente la autenticidad de las respuestas DNS, rechazando registros falsificados incluso si el tráfico es interceptado.

### 3. DNS sobre HTTPS / DNS sobre TLS

Configurar los clientes para utilizar DoH (DNS over HTTPS) o DoT (DNS over TLS) hacia servidores de confianza, cifrando las consultas DNS y haciendo inviable la interceptación y manipulación en Capa 2.

```bash
# Ejemplo: configurar DoH en el resolver del sistema
# /etc/systemd/resolved.conf
[Resolve]
DNS=1.1.1.1
DNSOverTLS=yes
```

### Tabla Resumen

| Contramedida | Protege contra | Efectividad | Impacto operacional |
|---|---|---|---|
| DAI + DHCP Snooping | ARP MitM (vector inicial) | Muy alta | Bajo |
| DNSSEC | Respuestas DNS falsificadas | Alta | Medio |
| DoH / DoT | Intercepción DNS en tránsito | Alta | Bajo |
| HTTPS + HSTS | Phishing por redirección HTTP | Media | Ninguno |

---

## 📸 Capturas de Pantalla

```
images/
├── 01_topologia_gns3.png
├── 02_arp_poisoning_en_ejecucion.png
├── 03_dns_query_interceptada_wireshark.png
├── 04_dns_response_falsificada.png
├── 05_pagina_falsa_navegador.png
├── 06_nslookup_ip_atacante.png
└── 07_dai_dhcp_snooping_contramedida.png
```

---

## 🎬 Video de Demostración

> 📺 **[Ver demostración en YouTube →](#)**

---

*Documento elaborado con fines académicos en un entorno de laboratorio controlado.*
*El uso de estas técnicas fuera de entornos autorizados es ilegal.*
