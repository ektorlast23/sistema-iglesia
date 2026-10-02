import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = r"C:\Users\EktoR\Documents\MySQLprject"

tables = [
    ("FAMILIAS", (0.4, 8.8), ["PK id INT AI", "nombre_familia VARCHAR(100) UQ", "direccion VARCHAR(255)", "telefono VARCHAR(20)", "fecha_registro DATE"]),
    ("MINISTERIOS", (6.6, 8.8), ["PK id INT AI", "nombre VARCHAR(100) UQ", "descripcion TEXT", "activo BOOL DEF 1"]),
    ("MIEMBROS", (0.4, 6.2), ["PK id INT AI", "nombres + apellidos", "fecha_nac / sexo / contacto", "FK familia_id -> familias.id", "fecha_ingreso DATE", "estado ENUM"]),
    ("MIEMBROS_MINISTERIOS", (6.6, 6.2), ["PK/FK miembro_id -> miembros.id", "PK/FK ministerio_id -> ministerios.id", "fecha_asignacion DATE", "rol VARCHAR(50)"]),
    ("EVENTOS", (0.4, 3.3), ["PK id INT AI", "nombre / fecha / horas", "lugar / tipo", "FK responsable_id -> miembros.id"]),
    ("ASISTENCIAS", (6.6, 3.3), ["PK id INT AI", "FK miembro_id -> miembros.id", "FK evento_id -> eventos.id", "fecha / presente / observ.", "UQ(miembro_id, evento_id)"]),
]

fig, ax = plt.subplots(figsize=(12, 9))
ax.set_xlim(0, 12)
ax.set_ylim(0, 9.6)
ax.axis("off")
ax.set_title("Sistema Iglesia - Modelo EER Semana 2 (cursor_demo / iglesia_db)  |  Django + MySQL",
             fontsize=11, pad=12)

centers = {}
for name, (x, y_top), cols in tables:
    w = 5.0
    row_h = 0.32
    h = 0.55 + len(cols) * row_h
    y_bot = y_top - h
    box = FancyBboxPatch((x, y_bot), w, h, boxstyle="round,pad=0.02",
                         facecolor="#EAF2FF", edgecolor="#1F4E79", linewidth=1.6)
    ax.add_patch(box)
    ax.text(x + w/2, y_top - 0.25, name, ha="center", va="center",
            fontsize=10, weight="bold", color="#1F4E79")
    for i, c in enumerate(cols):
        ax.text(x + 0.15, y_top - 0.62 - i*row_h, c, ha="left", va="center",
                fontsize=7.5, family="monospace")
    centers[name] = (x, y_bot, w, h)

def edge(name, side):
    x, y_bot, w, h = centers[name]
    if side == "right":
        return (x + w, y_bot + h/2)
    if side == "left":
        return (x, y_bot + h/2)
    if side == "top":
        return (x + w/2, y_bot + h)
    if side == "bottom":
        return (x + w/2, y_bot)
    return (x + w/2, y_bot)

links = [
    ("FAMILIAS", "right", "MIEMBROS", "left", "1 - N"),
    ("MINISTERIOS", "left", "MIEMBROS_MINISTERIOS", "right", "1 - N"),
    ("MIEMBROS", "right", "MIEMBROS_MINISTERIOS", "left", "1 - N (N-M)"),
    ("MIEMBROS", "bottom", "EVENTOS", "top", "1 - N resp."),
    ("MIEMBROS", "right", "ASISTENCIAS", "right", "1 - N"),
    ("EVENTOS", "right", "ASISTENCIAS", "left", "1 - N"),
]
for a, sa, b, sb, label in links:
    x1, y1 = edge(a, sa)
    x2, y2 = edge(b, sb)
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="<->", color="#C00000", lw=1.5, shrinkA=1, shrinkB=1))
    ax.text((x1+x2)/2, (y1+y2)/2 + 0.12, label, fontsize=7, color="white", ha="center", va="center",
            bbox=dict(facecolor="#C00000", edgecolor="none", pad=2, boxstyle="round,pad=0.3"))

fig.tight_layout()
fig.savefig(f"{OUT}/diagrama_EER.png", dpi=150)
fig.savefig(f"{OUT}/diagrama_EER.pdf")
print("OK v2")
