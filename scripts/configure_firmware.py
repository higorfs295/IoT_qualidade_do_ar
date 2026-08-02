#!/usr/bin/env python3
"""Gera firmware/include/secrets.h sem imprimir segredos no terminal."""

from __future__ import annotations

import argparse
import getpass
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESTINO = ROOT / "firmware" / "include" / "secrets.h"
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$")


def c_string(valor: str) -> str:
    return json.dumps(valor, ensure_ascii=True)


def ler_opcional(caminho: str | None) -> str:
    return Path(caminho).read_text(encoding="utf-8") if caminho else ""


def argumentos() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Configura Wi-Fi, MQTT e identidade do firmware.")
    p.add_argument("--ssid", required=True)
    p.add_argument("--wifi-password", help="Omitir para digitar sem eco no terminal")
    p.add_argument("--mqtt-host", required=True)
    p.add_argument("--mqtt-port", type=int, default=1883)
    p.add_argument("--mqtt-user", default="")
    p.add_argument("--mqtt-password", help="Omitir para digitar sem eco quando houver usuário")
    p.add_argument("--device-id", default="esp32-proto-01")
    p.add_argument("--site-id", default="campus-ufg")
    p.add_argument("--interval-seconds", type=int, default=60)
    p.add_argument("--ca-file")
    p.add_argument("--client-cert-file")
    p.add_argument("--private-key-file")
    p.add_argument("--aws", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--output", default=str(DESTINO), help=argparse.SUPPRESS)
    return p.parse_args()


def main() -> int:
    a = argumentos()
    destino = Path(a.output).resolve()
    wifi_password = a.wifi_password
    if wifi_password is None: wifi_password = getpass.getpass("Senha do Wi-Fi: ")
    mqtt_password = a.mqtt_password
    if a.mqtt_user and mqtt_password is None: mqtt_password = getpass.getpass("Senha MQTT: ")
    if mqtt_password is None: mqtt_password = ""
    for nome, valor in (("device-id", a.device_id), ("site-id", a.site_id)):
        if not ID_RE.fullmatch(valor): raise SystemExit(f"{nome} inválido")
    if not 1 <= a.mqtt_port <= 65535: raise SystemExit("mqtt-port inválida")
    if not 1 <= a.interval_seconds <= 86400: raise SystemExit("interval-seconds deve estar entre 1 e 86400")
    if a.aws:
        if a.mqtt_port != 8883: raise SystemExit("--aws exige --mqtt-port 8883")
        if not (a.ca_file and a.client_cert_file and a.private_key_file):
            raise SystemExit("--aws exige CA, certificado do cliente e chave privada")
    if destino.exists() and not a.force:
        raise SystemExit(f"{destino} já existe; use --force para substituir conscientemente")

    valores = {
        "WIFI_SSID": a.ssid, "WIFI_PASS": wifi_password,
        "MQTT_HOST": a.mqtt_host, "MQTT_USER": a.mqtt_user,
        "MQTT_PASS": mqtt_password, "DEVICE_ID": a.device_id,
        "SITE_ID": a.site_id, "MQTT_CA_CERT": ler_opcional(a.ca_file),
        "MQTT_CLIENT_CERT": ler_opcional(a.client_cert_file),
        "MQTT_PRIVATE_KEY": ler_opcional(a.private_key_file),
    }
    linhas = ["#pragma once", "", "// Gerado por scripts/configure_firmware.py; não versionar."]
    for nome, valor in valores.items(): linhas.append(f"#define {nome} {c_string(valor)}")
    linhas.extend([
        f"#define MQTT_PORT {a.mqtt_port}",
        f"#define INTERVALO_PUBLICACAO_MS {a.interval_seconds * 1000}UL",
        "",
    ])
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text("\n".join(linhas), encoding="utf-8")
    destino.chmod(0o600)
    try: exibicao = destino.relative_to(ROOT)
    except ValueError: exibicao = destino
    print(f"Configuração gravada em {exibicao}.")
    print("Compile com: pio run -d firmware -e esp32-hil")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
