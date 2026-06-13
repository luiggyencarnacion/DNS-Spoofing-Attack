# 🕵️ DNS Spoofing / DNS Poisoning

**Luiggy Habraham Encarnación Cabrera · Matrícula 2025-0663**

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Kali%20Linux-557C94?style=for-the-badge&logo=linux&logoColor=white)
![Library](https://img.shields.io/badge/Library-Scapy-FF6F00?style=for-the-badge)
![Emulator](https://img.shields.io/badge/Emulador-GNS3-009639?style=for-the-badge)
![Layer](https://img.shields.io/badge/Capa%20OSI-7%20(Aplicación)-E53935?style=for-the-badge)
![License](https://img.shields.io/badge/Uso-Educativo-blue?style=for-the-badge)

> Intercepción de consultas DNS mediante ARP MitM y respuesta con registros A falsificados, redirigiendo a la víctima hacia un servidor web controlado por el atacante (`itla-fake-website-1`) sin que la URL en el navegador cambie.

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
7. [Parámetros del Script](#-parámetros-del-script)
8. [Ejecución](#-ejecución)
9. [Impacto Demostrado](#-impacto-demostrado)
10. [Contramedidas](#-contramedidas)
11. [Capturas de Pantalla](#-capturas-de-pantalla)
12. [Video de Demostración](#-video-de-demostración)

---

## 🎯 Objetivo del Laboratorio

Demostrar cómo un atacante posicionado en la misma VLAN que la víctima puede interceptar sus consultas DNS hacia `itla.edu.do` mediante envenenamiento ARP y responder con un registro A falsificado que apunta al servidor web controlado por el atacante (`itla-fake-website-1`), cargando una página falsa en el navegador de la víctima (`UbuntuDesktop-1`) sin que la barra de direcciones muestre ninguna anomalía. El ataque combina ARP poisoning bidireccional con sniffing y construcción de respuestas DNS usando la librería Scapy.

---

## 🔬 Descripción de la Vulnerabilidad

El protocolo **DNS** no implementa mecanismos de autenticación en su forma base (RFC 1034/1035). Las respuestas DNS son aceptadas por el cliente si:

1. Llegan **antes** que la respuesta legítima
2. El **Transaction ID** coincide con el de la consulta original

Al combinarlo con un ataque ARP MitM previo, el atacante ya se encuentra en el camino del tráfico, garantizando que sus respuestas DNS falsas lleguen primero y con el Transaction ID correcto — ya que intercepta la consulta original antes de que salga hacia los servidores DNS configurados por DHCP en R-1.

---

## 📋 Requisitos

| Requisito | Detalle |
|---|---|
| Sistema operativo | Kali Linux 2023 o superior |
| Python | 3.10 o superior |
| Librería Scapy | `scapy >= 2.5.0` |
| Privilegios | `sudo` / `root` obligatorio (acceso a Capa 2) |
| Emulador de red | GNS3 con Cisco IOU |
| Servidor web | `itla-fake-website-1` corriendo en la red |
| Víctima | `UbuntuDesktop-1` (con navegador web) |
| Conocimientos previos | DNS, ARP, modelos OSI/TCP-IP, redes IP |

---

## ⚙️ Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/luiggyencarnacion/DNS-Spoofing-Attack.git
cd DNS-Spoofing-Attack

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Verificar Scapy
python3 -c "from scapy.all import ARP, DNS, DNSRR; print('Scapy OK')"

# 4. Ejecutar con privilegios root
sudo python3 dns_spoofing.py
```

**`requirements.txt`**
```
scapy>=2.5.0
```

---

## 🗺️ Documentación de la Red

### Topología

```
                              Cloud1
                                │ eth0
                                │ g1/0
                           ┌────┴─────┐
                           │   R-1    │  Gateway / DHCP
                           └────┬─────┘
                                │ g0/0
                                │ Gig0/0
                           ┌────┴──────┐
                           │  SW-CORE  │  Root Bridge / VTP Server
                           └───┬───┬───┘
                      Gig0/1   │   │  Gig0/2
             ┌─────────────────┘   └──────────────────┐
        ┌────┴──────┐                          ┌───────┴───┐
        │   SW-1    │                          │   SW-2    │
        └─┬──┬──┬───┘                          └──┬──┬──┬──┘
     Gig1/0│  │Gig1/1  Gig1/2           Gig1/0   │  │  │Gig2/0
           │  │         │                         │  │  │
      ┌────┘  └───┐  ┌──┴──────────┐         ┌───┘  │  └──────┐
 ┌────┴────┐ ┌────┴──┴──┐  ┌───────┴──────┐ ┌┴────┐ │   ┌────┴─┐
 │KaliLinux│ │UbuntuDesk│  │itla-fake-    │ │ PC2 │ │   │ PC3  │
 │   -1    │ │   top-1  │  │website-1     │ │     │ │   │      │
 │Atacante │ │  Víctima │  │Servidor Web  │ │VL20 │ │   │VL10  │
 └─────────┘ └──────────┘  │Falso         │ └─────┘ │   └──────┘
  [ARP MitM]  [DNS query]  └──────────────┘
  [DNS resp]  [carga pág]   [sirve página
                             itla.edu.do]

Flujo:
  UbuntuDesktop-1 ──ARP envenenado──► KaliLinux-1 ──► R-1
  UbuntuDesktop-1 ──DNS query──► KaliLinux-1
                                      │ intercepta + responde
                                      ▼
  UbuntuDesktop-1 ◄── DNS resp: itla.edu.do = IP itla-fake-website-1
  UbuntuDesktop-1 ──HTTP GET──► itla-fake-website-1 (página falsa)
```

### Parámetros Generales

| Parámetro | Valor |
|---|---|
| Red VLAN 10 (ADMIN) | 10.6.63.0/26 |
| Red VLAN 20 (VENTAS) | 10.6.63.64/26 |
| Red VLAN 99 (GESTION) | 10.6.63.128/26 |
| Emulador | GNS3 con Cisco IOU |
| Plataforma de ataque | Kali Linux |
| Librería | Scapy |

### Tabla de Direccionamiento

| Dispositivo | Interfaz | Conectado a | Dirección IP | Rol |
|---|---|---|---|---|
| R-1 | g0/0 | SW-CORE Gig0/0 | Gateway VLAN 10/20/99 | Gateway / DHCP |
| R-1 | g1/0 | Cloud1 eth0 | DHCP (ISP) | Enlace NAT |
| SW-CORE | Gig0/0 | R-1 g0/0 | — | Root Bridge / VTP Server |
| SW-CORE | Gig0/1 | SW-1 Gig0/0 | — | Troncal |
| SW-CORE | Gig0/2 | SW-2 Gig0/0 | — | Troncal |
| SW-1 | Gig0/0 | SW-CORE Gig0/1 | — | Troncal uplink |
| SW-1 | Gig0/1 | SW-2 Gig0/1 | — | Troncal inter-switches |
| SW-1 | Gig1/0 | KaliLinux-1 e0 | — | **Atacante DNS Spoofing** |
| SW-1 | Gig1/1 | UbuntuDesktop-1 e0 | DHCP | **Víctima** |
| SW-1 | Gig1/2 | itla-fake-website-1 eth0 | — | **Servidor Web Falso** |
| SW-2 | Gig0/0 | SW-CORE Gig0/2 | — | Troncal uplink |
| SW-2 | Gig0/1 | SW-1 Gig0/1 | — | Troncal inter-switches |
| SW-2 | Gig1/0 | PC2 e0 | DHCP VLAN 20 | Víctima — VLAN 20 |
| SW-2 | Gig2/0 | PC3 e0 | DHCP VLAN 10 | Víctima — VLAN 10 |
| KaliLinux-1 | e0 | SW-1 Gig1/0 | DHCP / estática | Atacante ARP + DNS |
| UbuntuDesktop-1 | e0 | SW-1 Gig1/1 | DHCP | Víctima principal |
| itla-fake-website-1 | eth0 | SW-1 Gig1/2 | estática | Servidor web falso |

---

## 🔬 Funcionamiento del Ataque

El ataque opera en **tres fases** ejecutadas simultáneamente por el script `dns_spoofing.py`.

### Fase 1 — ARP Man-in-the-Middle (hilo paralelo)

El script lanza un hilo en background que envía paquetes ARP Reply cada 2 segundos de forma bidireccional:

```
KaliLinux-1
    │
    ├─► ARP Reply → UbuntuDesktop-1:
    │   "La MAC del Gateway es: [MAC de Kali]"
    │
    └─► ARP Reply → R-1 (Gateway):
        "La MAC de UbuntuDesktop-1 es: [MAC de Kali]"

Resultado:
  Todo el tráfico UbuntuDesktop-1 ↔ Gateway pasa por KaliLinux-1
  IP Forwarding ON → el tráfico no-DNS se reenvía normalmente
  UbuntuDesktop-1 mantiene conectividad → ataque silencioso
```

### Fase 2 — Sniffing de consultas DNS

```python
sniff(iface=iface, filter="udp port 53", prn=dns_spoof_handler)
```

El script escucha todo el tráfico UDP en el puerto 53 que ya atraviesa la interfaz del atacante gracias al ARP MitM.

### Fase 3 — Construcción y envío de respuesta DNS falsa

```
UbuntuDesktop-1              KaliLinux-1            DNS legítimo
       │                          │                      │
       │── DNS Query ─────────────►│                      │
       │   id=0xAB12              │                      │
       │   "itla.edu.do A ?"      │                      │
       │                          │  [detecta dominio]   │
       │                          │  [extrae id=0xAB12]  │
       │                          │  [construye respuesta]│
       │◄─ DNS Response ──────────│                      │
       │   id=0xAB12  (mismo ID)  │                      │
       │   itla.edu.do A <IP fake>│                      │
       │                          │                      │
       │── HTTP GET / ────────────────────────────────────────►
       │   → resuelve a itla-fake-website-1
       │   → carga página falsa de ITLA
```

### Restauración al terminar (Ctrl+C)

Al interrumpir el script, se restauran automáticamente las tablas ARP de la víctima y del gateway enviando 5 paquetes ARP Reply correctos, dejando la red en su estado original.

---

## ⚙️ Parámetros del Script

El script solicita todos los parámetros de forma **interactiva** al ejecutarse:

| Campo solicitado | Descripción | Ejemplo |
|---|---|---|
| Interfaz | Selección de lista de interfaces disponibles | `e0` / `eth0` |
| IP de la víctima | Dirección IP de `UbuntuDesktop-1` | `10.6.63.x` |
| IP del gateway | Gateway de la VLAN de la víctima | `10.6.63.1` |
| Dominio a spoof | Dominio DNS a interceptar | `itla.edu.do` (default) |
| IP falsa | IP de `itla-fake-website-1` | `10.6.63.x` |

### Variables internas del script

| Variable | Descripción |
|---|---|
| `arp_count` | Contador de envenenamientos ARP enviados |
| `dns_count` | Contador de respuestas DNS falsificadas enviadas |
| `start_time` | Tiempo de inicio para el resumen final |
| `iface` | Interfaz de red del atacante |

---

## 🚀 Ejecución

```bash
# Ejecutar el script con privilegios root
sudo python3 dns_spoofing_attack.py
```

### Interacción esperada al iniciar

```
  ╔════════════════════════════════════════╗
  ║        DNS Spoofing + ARP MitM         ║
  ╚════════════════════════════════════════╝

  Interfaces de red disponibles:
    [1] lo
    [2] e0
    [3] eth1

  Seleccione interfaz (número o nombre): 2

  Ingrese la IP de la víctima            : 10.6.63.16
  Ingrese la IP del gateway              : 10.6.63.1
  Dominio a spoof (default: itla.edu.do) :
  IP falsa del dominio (web server)      : 10.6.63.13
```

### Salida durante el ataque

```
  ╔════════════════════════════════════════╗
  ║        DNS Spoofing + ARP MitM         ║
  ╚════════════════════════════════════════╝
  Interfaz  : e0
  Víctima   : 10.6.63.16
  Gateway   : 10.6.63.1
  Dominio   : itla.edu.do
  IP Falsa  : 10.6.63.13
  ──────────────────────────────────────────
  [*] Resolviendo MACs...
  ──────────────────────────────────────────
  MAC Víctima  : 00:0c:29:db:f4:db
  MAC Gateway  : ca:01:0c:f7:00:08
  MAC Atacante : 00:0c:29:1b:ee:fc
  ──────────────────────────────────────────
  [*] IP Forwarding habilitado
  [*] Iniciando ARP Poisoning...
  [*] Ctrl+C para detener y restaurar

  Tiempo     ARP       DNS Spoofed   Query
  ──────────────────────────────────────────
  00:17      ARP:  45   DNS Spoofed:  3   [itla.edu.do => 10.6.63.13]
```

### Resumen al detener (Ctrl+C)

```
  ╔════════════════════════════════════════╗
  ║             Resumen Final              ║
  ╚════════════════════════════════════════╝
  Envenenamientos ARP      : 134
  DNS Spoofed              : 7
  Tiempo activo            : 04:28
  ──────────────────────────────────────────
  [*] Restaurando tablas ARP...
  [+] Tablas ARP restauradas.
  [+] Saliendo.
```

### Comandos de verificación

#### En UbuntuDesktop-1 (víctima)

Antes de verificar, es **obligatorio forzar una nueva consulta DNS** limpiando el caché del resolver del sistema:

```bash
# Paso 1 — Limpiar el caché DNS local
sudo resolvectl flush-caches
```

> **¿Por qué forzamos esto para la demostración?**
> `systemd-resolved`, el resolver DNS de Ubuntu, guarda en caché las respuestas DNS durante el tiempo indicado en el campo TTL del registro. Si la víctima ya resolvió `itla.edu.do` antes de que el ataque comenzara, seguirá usando la IP legítima cacheada aunque el script ya esté envenenando el tráfico — el sistema simplemente no volvería a preguntar. Al ejecutar `resolvectl flush-caches` eliminamos esa respuesta guardada, obligando al sistema a emitir una nueva consulta DNS en frío que sí pasará por el atacante y recibirá el registro A falsificado.

```bash
# Paso 2 — Resolver el dominio y observar la IP retornada
nslookup itla.edu.do
```

Resultado esperado **con el ataque activo:**
```
Server:   127.0.0.53
Address:  127.0.0.53#53

Non-authoritative answer:
Name:     itla.edu.do
Address:  <IP de itla-fake-website-1>   ← IP del atacante, no la legítima
```

Resultado esperado **sin el ataque (o después de restaurar):**
```
Name:     itla.edu.do
Address:  <IP real del servidor de ITLA>
```

#### En KaliLinux-1 (atacante)

```bash
# Monitorear consultas DNS interceptadas en tiempo real
sudo tcpdump -i e0 udp port 53

# Verificar tablas ARP envenenadas en la víctima
arp -n
```

#### En itla-fake-website-1

```bash
# Verificar que el servidor web está escuchando
sudo ss -tlnp | grep :80
```

---

## 💥 Impacto Demostrado

- `UbuntuDesktop-1` resuelve `itla.edu.do` a la IP de **`itla-fake-website-1`** en lugar del servidor legítimo
- El navegador de la víctima carga la **página web falsa** alojada en `itla-fake-website-1`
- La **barra de direcciones** muestra `itla.edu.do` sin indicación de anomalía
- La víctima **mantiene conectividad** con el resto de la red (IP Forwarding activo)
- Interceptación visible en Wireshark: paquete DNS Response con **registro A falsificado** y Transaction ID coincidente
- El contador en tiempo real muestra cada consulta DNS interceptada y resuelta hacia la IP falsa

---

## 🔐 Contramedidas

### 1. DHCP Snooping + Dynamic ARP Inspection (DAI)

El DNS Spoofing en este escenario depende completamente del ARP MitM como vector inicial. DAI elimina el envenenamiento ARP validando cada respuesta contra la binding table de DHCP Snooping, descartando respuestas ARP cuya combinación IP-MAC no coincida con una asignación DHCP legítima.

```bash
! ── SW-CORE / SW-1 / SW-2 ──────────────────────────────

! Habilitar DHCP Snooping
ip dhcp snooping
ip dhcp snooping vlan 10,20,99
no ip dhcp snooping information option

! Habilitar Dynamic ARP Inspection
ip arp inspection vlan 10,20,99

! Marcar uplinks troncales como trusted (no validar puertos de switches)
interface GigabitEthernet0/0
 ip dhcp snooping trust
 ip arp inspection trust
exit
```

### 2. DNSSEC (defensa en profundidad)

DNSSEC permite a los clientes verificar criptográficamente la autenticidad de las respuestas DNS, rechazando registros falsificados incluso si el tráfico fuera interceptado.

```bash
# Verificar si el dominio tiene DNSSEC habilitado
dig itla.edu.do +dnssec
dig itla.edu.do DS
```

### 3. DNS sobre HTTPS / DNS sobre TLS

Cifrar las consultas DNS hace inviable la interceptación y manipulación en Capa 2, ya que el atacante no puede leer ni modificar el contenido del tráfico DNS.

```ini
# /etc/systemd/resolved.conf
[Resolve]
DNS=1.1.1.1
DNSOverTLS=yes
```

### 4. HTTPS + HSTS en el servidor legítimo

Aunque el DNS sea redirigido, HSTS impide que el navegador cargue la página sin un certificado TLS válido para `itla.edu.do`, alertando al usuario.

### Tabla Resumen

| Contramedida | Protege contra | Efectividad | Impacto operacional |
|---|---|---|---|
| DAI + DHCP Snooping | ARP MitM (vector inicial) | Muy alta | Bajo |
| DNSSEC | Respuestas DNS falsificadas | Alta | Medio |
| DoH / DoT | Intercepción DNS en tránsito | Alta | Bajo |
| HTTPS + HSTS | Phishing por redirección HTTP | Media | Ninguno |

---

## 📁 Estructura del Repositorio

```
DNS-Spoofing-Attack/
├── dns_spoofing.py          # Script principal (ARP MitM + DNS Spoof)
├── requirements.txt         # Dependencias Python
├── README.md
└── images/
    ├── 01_topologia_gns3.png
    ├── 02_script_parametros.png
    ├── 03_arp_poisoning_activo.png
    ├── 04_dns_query_interceptada_wireshark.png
    ├── 05_dns_response_falsificada.png
    ├── 06_pagina_falsa_navegador.png
    ├── 07_nslookup_ip_atacante.png
    └── 08_dai_contramedida.png
```

---

## 🎬 Video de Demostración

> 📺 **[Ver demostración en YouTube →](#)**

---

*Documento elaborado con fines académicos en un entorno de laboratorio controlado.*
*El uso de estas técnicas fuera de entornos autorizados es ilegal.*
