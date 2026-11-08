"""Medicion de rendimiento contra la base real (Semana 9).

Recorre las pantallas principales con el cliente de pruebas de Django, contra
MySQL (``cursor_demo``) y sin escribir nada: solo peticiones GET. Para cada
pantalla informa el codigo de respuesta, cuantas consultas SQL ejecuta y cuanto
tarda (mejor de varias pasadas, para reducir el ruido del equipo).

Uso:
    .\\venv\\Scripts\\python.exe medir_rendimiento.py

Las credenciales se toman del entorno (MYSQL_USER, MYSQL_PASS, MYSQL_DB...). Si
MYSQL_PASS no esta definida, se lee la configuracion local del MCP de MySQL,
que es donde el proyecto guarda la clave de desarrollo.
"""

from __future__ import annotations

import json
import os
import statistics
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
SISTEMA = BASE / "sistema_iglesia"
sys.path.insert(0, str(SISTEMA))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


def _credenciales_desde_config() -> None:
    """Completa MYSQL_* desde la config del MCP si el entorno no las trae."""
    if os.environ.get("MYSQL_PASS"):
        return
    candidatos = [
        Path.home() / ".config" / "opencode" / "opencode.json",
        Path.home() / ".cursor" / "mcp.json",
    ]
    for ruta in candidatos:
        if not ruta.exists():
            continue
        try:
            datos = json.loads(ruta.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        entorno = (
            datos.get("mcp", {}).get("mysql", {}).get("environment")
            or datos.get("mcpServers", {}).get("mysql", {}).get("env")
            or {}
        )
        for clave, valor in entorno.items():
            if clave.startswith("MYSQL_"):
                os.environ.setdefault(clave, str(valor))
        if os.environ.get("MYSQL_PASS"):
            return


_credenciales_desde_config()

import django  # noqa: E402  (despues de preparar el entorno)

django.setup()

from django.db import connection  # noqa: E402
from django.test import Client  # noqa: E402
from django.test.utils import CaptureQueriesContext  # noqa: E402
from django.urls import reverse  # noqa: E402

REPETICIONES = 3

PANTALLAS = [
    ("Portada", reverse("home")),
    ("Miembros: lista", reverse("miembros:lista")),
    ("Miembros: alta", reverse("miembros:registrar")),
    ("Eventos: lista", reverse("eventos:lista")),
    ("Eventos: alta", reverse("eventos:registrar")),
    ("Inventario: lista", reverse("inventario:lista")),
    ("Inventario: prestamos", reverse("inventario:prestamos")),
    ("Inventario: devoluciones", reverse("inventario:devoluciones")),
    ("Reportes: indice", reverse("reportes:indice")),
    ("Reporte: asistencia", reverse("reportes:detalle", args=["asistencia"])),
    ("Reporte: crecimiento", reverse("reportes:detalle", args=["crecimiento"])),
    ("Reporte: inventario", reverse("reportes:detalle", args=["inventario"])),
    ("Reporte: demografia", reverse("reportes:detalle", args=["demografia"])),
]


def medir(cliente: Client, url: str) -> tuple[int, int, float, float]:
    """Devuelve (estado, consultas, mejor ms, mediana ms) de varias pasadas."""
    tiempos: list[float] = []
    consultas = 0
    estado = 0
    for _ in range(REPETICIONES):
        with CaptureQueriesContext(connection) as capturadas:
            inicio = time.perf_counter()
            respuesta = cliente.get(url)
            tiempos.append((time.perf_counter() - inicio) * 1000)
        estado = respuesta.status_code
        consultas = len(capturadas)
        if estado != 200:
            break
    return estado, consultas, min(tiempos), statistics.median(tiempos)


def main() -> int:
    cliente = Client()
    with connection.cursor() as cursor:
        cursor.execute("SELECT DATABASE(), VERSION()")
        base, servidor = cursor.fetchone()

    print("Medicion de rendimiento - Sistema Iglesia (Semana 9)")
    print(f"Motor      : {connection.vendor} {servidor}")
    print(f"Base       : {base}")
    print(f"Repeticiones: {REPETICIONES} por pantalla (se informa el mejor tiempo)")
    print("Modo       : solo GET (lectura), sin escrituras")
    print()
    print(f"{'Pantalla':26} {'Cod':>3} {'Cons.':>5} {'Mejor ms':>9} {'Mediana ms':>11}  URL")
    print("-" * 100)

    total_consultas = 0
    peor = ("", 0.0)
    for nombre, url in PANTALLAS:
        estado, consultas, mejor, mediana = medir(cliente, url)
        total_consultas += consultas
        if mejor > peor[1]:
            peor = (nombre, mejor)
        print(f"{nombre:26} {estado:3d} {consultas:5d} {mejor:9.1f} {mediana:11.1f}  {url}")

    print("-" * 100)
    print(f"Pantallas medidas: {len(PANTALLAS)} | Consultas totales: {total_consultas}")
    print(f"Pantalla mas lenta: {peor[0]} ({peor[1]:.1f} ms)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
