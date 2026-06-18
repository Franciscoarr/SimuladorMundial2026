import runpy
import collections
import io
import contextlib

TOTAL_SIMULACIONES = 10000

# Cargar el simulador
mod = runpy.run_path("simulador_mundial.py")

# Evitar guardar archivos en cada simulación
mod["guardar_resumen_torneo"] = lambda *a, **k: None

jugar_mundial = mod["jugar_mundial"]

counts = collections.Counter()

print(f"Simulando {TOTAL_SIMULACIONES:,} mundiales...")

for i in range(TOTAL_SIMULACIONES):
    buf = io.StringIO()

    with contextlib.redirect_stdout(buf):
        jugar_mundial()

    for line in reversed(buf.getvalue().splitlines()):
        if line.startswith("🏆 CAMPEÓN DEL MUNDO 2026: "):
            campeon = line.split(": ", 1)[1].replace(" 🏆", "").strip()
            counts[campeon] += 1
            break

    if (i + 1) % 500 == 0:
        print(f"⏳ {i + 1:,} simulaciones completadas...")

print("\nPAÍS                 | VECES  | PORCENTAJE")
print("-" * 45)

for pais, veces in counts.most_common():
    print(f"{pais:<20} | {veces:<6} | {(veces / TOTAL_SIMULACIONES) * 100:.2f}%")
