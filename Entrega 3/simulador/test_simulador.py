#!/usr/bin/env python
"""
test_simulador.py — Tests del simulador (simular.py y la pagina web).

Oraculos independientes:
  - cada venta del dataset analitico, pasada por simular(), contra las
    columnas que calcularon kpis.py y decision.py en el pipeline
  - P2 del simulador (cuantas del universo la superan) contra p2_no_dominada,
    que decision.py calcula comparando todos los pares
  - P3 contra la ocupacion de equilibrio de temporal.py
  - el modelo exportado como coeficientes (lo que usa motor.js) contra el
    predict() de scikit-learn
  - motor.js, corrido en Chrome sin ventana, contra simular() en Python
    (se saltea si no hay Chrome)
con NEGATIVOS: otra vacancia tiene que cambiar la neta, una propiedad fuera
del soporte o del presupuesto nunca pasa P1, y fuera de rango se rechaza.

Uso:
    py simulador/test_simulador.py      # necesita parametros.json (--actualizar)
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", message=".*Trying to unpickle.*")

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import simular as SIM  # noqa: E402

ANALITICO = os.path.join(SIM.ENTREGA_3, "data", "processed", "dataset_analitico.csv")

fallos = []
corridos = 0


def check(descripcion: str, condicion: bool, detalle: str = "") -> None:
    global corridos
    corridos += 1
    if not condicion:
        fallos.append(descripcion + (f"\n      {detalle}" if detalle else ""))


def iguales(a: pd.Series, b: pd.Series) -> tuple[bool, str]:
    """Iguales donde el oraculo tiene dato (el dataset deja vacio lo que no evalua)."""
    a, b = a.reset_index(drop=True), b.reset_index(drop=True)
    msk = b.notna()
    if pd.api.types.is_numeric_dtype(b) or pd.api.types.is_bool_dtype(b):
        x, y = a[msk].astype(float).to_numpy(), b[msk].astype(float).to_numpy()
        dif = np.abs(x - y)
        mal = ~((dif <= 1e-9) | (np.isnan(x) & np.isnan(y)))
        return (not mal.any(), f"{int(mal.sum())} de {int(msk.sum())} filas distintas, max dif {np.nanmax(dif):g}")
    mal = a[msk].astype(str) != b[msk].astype(str)
    return (not mal.any(), f"{int(mal.sum())} de {int(msk.sum())} filas distintas")


if not (os.path.exists(SIM.RUTA_MODELO) and os.path.exists(SIM.RUTA_PARAMETROS) and os.path.exists(ANALITICO)):
    print("(faltan el modelo, parametros.json o el dataset analitico: correr el pipeline y --actualizar)")
    sys.exit(1)

m, P = SIM.cargar()
df = pd.read_csv(ANALITICO, encoding="utf-8-sig", low_memory=False)
ventas = df[df["operacion"] == "venta"].dropna(subset=["venta_usd", "sup_total_m2", "barrio"]).reset_index(drop=True)
vac = P["supuestos"]["vacancia_pct"]
r = SIM.simular(ventas, m, P, vac)

# --- 1. Cada columna compartida, contra el pipeline -------------------------------
comunes = [c for c in r.columns if c in ventas.columns]
check("comparte al menos 30 columnas con el dataset", len(comunes) >= 30, f"comparte {len(comunes)}")
for c in comunes:
    ok, det = iguales(r[c], ventas[c])
    check(f"{c} igual que en el dataset analitico", ok, det)

# --- 2. Las cifras de referencia de la decision ----------------------------------
u = r["universo_decision"].astype(bool)
check("universo de la decision: 4.484", int(u.sum()) == 4484, f"da {int(u.sum())}")
check("pasan P1: 18", int(r["p1_comprar"].sum()) == 18, f"da {int(r['p1_comprar'].sum())}")
check("pasan P1 con costos de entrada: 4", int(r["p1_comprar_con_entrada"].sum()) == 4,
      f"da {int(r['p1_comprar_con_entrada'].sum())}")

# P2: dentro del universo, ninguna la supera <=> no dominada (decision.py, todos los pares)
ok, det = iguales(r.loc[u, "p2_la_superan"] == 0, ventas.loc[u, "p2_no_dominada"].astype(bool))
check("P2: 'ninguna la supera' coincide con p2_no_dominada", ok, det)
check("frontera de P2: 140", int((r.loc[u, "p2_la_superan"] == 0).sum()) == 140)

# P3: el equilibrio tercerizado es el de temporal.py
ok, det = iguales(r["p3_equilibrio_tercerizada_pct"], ventas["p3_ocupacion_equilibrio_pct"].round(1))
check("P3: equilibrio tercerizado igual que temporal.py", ok, det)

# --- 3. Negativos -------------------------------------------------------------------
r_otra = SIM.simular(ventas.head(200), m, P, vac + 10)
check("NEG: con 10 puntos mas de vacancia la neta cambia",
      not iguales(r_otra["rent_neta_pct"], ventas.head(200)["rent_neta_pct"])[0])

base = {"barrio": "caballito", "tipo_familia": "casa", "sup_total_m2": 400.0, "ambientes": 8.0,
        "dormitorios": 5.0, "banos": 3.0, "antiguedad_anios": 40.0, "venta_usd": 30000.0}
fuera = SIM.simular(pd.DataFrame([base]), m, P, vac).iloc[0]
check("NEG: casa grande regalada, fuera del soporte, no pasa P1",
      not fuera["en_soporte_modelo"] and not fuera["p1_comprar"] and fuera["neta_min_pct"] > 7.6,
      f"soporte {fuera['en_soporte_modelo']}, neta pesimista {fuera['neta_min_pct']}")
cara = SIM.simular(pd.DataFrame([{**base, "tipo_familia": "departamento", "sup_total_m2": 50.0,
                                  "ambientes": 2.0, "dormitorios": 1.0, "venta_usd": 500000.0}]), m, P, vac).iloc[0]
check("NEG: fuera del presupuesto no entra al universo", not cara["universo_decision"] and not cara["p1_comprar"])
check("NEG: 5 m2 se rechaza por fuera de rango", len(SIM.fuera_de_rango({"sup_total_m2": 5})) == 1)
check("NEG: 50 m2 no se rechaza", SIM.fuera_de_rango({"sup_total_m2": 50}) == [])

# --- 4. El modelo como coeficientes (motor.js) contra scikit-learn ------------------
X = ventas[m["columnas"]]
L = SIM.exportar_modelo(m, P)
for nombre, pipe in (("central", m["pipeline"]), ("p10", m["banda"]["modelo_p10"]), ("p90", m["banda"]["modelo_p90"])):
    d = np.abs(SIM.predecir_lineal(L[nombre], X) - pipe.predict(X))
    check(f"coeficientes del modelo {nombre} = predict()", d.max() < 1e-9, f"max dif {d.max():g}")

# --- 5. motor.js en Chrome contra simular() -----------------------------------------
CHROME = next((c for c in (
    shutil.which("chrome"), shutil.which("google-chrome"),
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
) if c and os.path.exists(c)), None)
PAGINA = os.path.join(AQUI, "simulador.html")

if CHROME is None or not os.path.exists(PAGINA):
    print("(sin Chrome o sin simulador.html: se saltea motor.js)")
else:
    campos = ["barrio", "tipo_familia", "sup_total_m2", "ambientes", "dormitorios", "banos",
              "antiguedad_anios", "venta_usd"] + list(SIM.CARACTERISTICAS)
    casos = ventas[campos].copy()
    for c in SIM.CARACTERISTICAS:
        casos[c] = casos[c].fillna(0).astype(int)
    casos = json.loads(casos.to_json(orient="records"))
    with open(PAGINA, encoding="utf-8") as f:
        html = f.read()
    # Corre Motor.simular para cada venta y deja el resultado en la pagina
    prueba = ("<script>\nconst CASOS = " + json.dumps(casos).replace("</", "<\\/") + ";\n"
              "const NUMS = ['sup_total_m2','ambientes','dormitorios','banos','antiguedad_anios','venta_usd'];\n"
              "const SAL = CASOS.map(c => { for (const k of NUMS) if (c[k] === null) c[k] = NaN;\n"
              "  const r = Motor.simular(c, DATOS.modelo, DATOS.parametros, null);\n"
              "  for (const k in r) if (typeof r[k] === 'number' && !Number.isFinite(r[k])) r[k] = null;\n"
              "  return r; });\n"
              "document.body.innerHTML = '<pre id=\"salida\">' + JSON.stringify(SAL).replace(/</g, '\\\\u003c') + '</pre>';\n"
              "</script>\n</body>")
    tmp = tempfile.mkdtemp()
    try:
        ruta = os.path.join(tmp, "prueba.html")
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(html.replace("</body>", prueba, 1))
        p = subprocess.run([CHROME, "--headless=new", "--disable-gpu", f"--user-data-dir={os.path.join(tmp, 'perfil')}",
                            "--virtual-time-budget=20000", "--dump-dom", "file:///" + ruta.replace(os.sep, "/")],
                           capture_output=True, timeout=180)
        dom = p.stdout.decode("utf-8", errors="replace")
        hallado = re.search(r'<pre id="salida">(.*?)</pre>', dom, re.S)
        check("motor.js corre en Chrome", hallado is not None, dom[:200])
        if hallado:
            texto = hallado.group(1).replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
            js = pd.DataFrame(json.loads(texto))
            check("motor.js evalua todas las ventas", len(js) == len(r), f"{len(js)} de {len(r)}")
            for c in r.columns:
                if c not in js.columns:
                    check(f"motor.js calcula {c}", False)
                    continue
                ok, det = iguales(js[c], r[c].where(r[c].notna(), np.nan))
                # donde Python no tiene dato, JS tampoco
                vacio_py, vacio_js = r[c].isna().to_numpy(), js[c].isna().to_numpy()
                check(f"motor.js {c} igual que simular()", ok and (vacio_py == vacio_js).all(), det)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

print(f"Tests corridos : {corridos}")
print(f"Fallos         : {len(fallos)}")
if fallos:
    print()
    for f in fallos:
        print(f"  FALLO: {f}")
    sys.exit(1)
print("OK")
