#!/usr/bin/env python
"""
simular.py — Simula una propiedad y la evalua como lo hace el analisis vigente
(3ra pre-entrega): alquiler estimado con su banda, ABL de la propiedad, neta,
costos de entrada, TIR a 5 anios y la funcion de decision (P1, P2 y P3).

DE DONDE SALEN LOS NUMEROS
--------------------------
De dos archivos de esta entrega:
    ../data/processed/modelo_alquiler.joblib   el Ridge, el smearing y la banda
                                               cuantilica calibrada (lo guarda kpis.py)
    parametros.json    supuestos (vacancia, gastos, ABL, costos, banda de
                       retorno), tablas por barrio y celda, y referencias del
                       mercado. Lo arma --actualizar con las funciones de src/
                       (supuestos, costos, decision), asi cada tabla sale igual
                       que en el pipeline
Si se corre de nuevo el pipeline (por ejemplo, si se reentrena el modelo):
    py simulador/simular.py --actualizar
    py simulador/simular.py --html
--actualizar solo LEE el resto de la entrega; escribe unicamente parametros.json.

MODO INTERACTIVO (te va preguntando):
    py simulador/simular.py

MODO DIRECTO (todo por argumentos):
    py simulador/simular.py --barrio palermo --m2 65 --ambientes 3 --antiguedad 20
    py simulador/simular.py --barrio caballito --m2 45 --ambientes 2 --cochera --balcon
    py simulador/simular.py --barrio constitucion --m2 50 --ambientes 2 --venta 85000

Si pasas --venta, ademas calcula la rentabilidad, la TIR y la decision.
Con --json imprime el resultado como JSON, sin formato.

PAGINA WEB INTERACTIVA:
    py simulador/simular.py --html       # escribe simulador/simulador.html
Arma una pagina autocontenida (se abre con doble clic, sin Python ni
servidor) a partir de web/plantilla.html y web/motor.js, con el modelo
exportado como coeficientes y los parametros de parametros.json.
motor.js repite el calculo de simular(): si se cambia una formula, va en los
dos lados. Despues de --actualizar, volver a correr --html.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import unicodedata
from datetime import datetime

import joblib
import numpy as np
import pandas as pd


AQUI = os.path.dirname(os.path.abspath(__file__))
ENTREGA_3 = os.path.dirname(AQUI)
RUTA_MODELO = os.path.join(ENTREGA_3, "data", "processed", "modelo_alquiler.joblib")
RUTA_PARAMETROS = os.path.join(AQUI, "parametros.json")

# Caracteristicas que se pueden activar. Cada una es una dummy del modelo.
CARACTERISTICAS = {
    "balcon": "balcón",
    "cochera_txt": "cochera",
    "amenities": "amenities",
    "ascensor": "ascensor",
    "aire_acondicionado": "aire acondicionado",
    "pileta": "pileta",
    "amoblado": "amoblado",
    "parrilla": "parrilla",
    "seguridad": "seguridad 24h",
    "baulera": "baulera",
    "luminoso": "luminoso",
    "patio_jardin": "patio o jardín",
    "a_reciclar": "a reciclar",
    "reciclado": "reciclado",
}
TIPOS = ["departamento", "ph", "casa"]

# Rangos aceptados: los del dataset (superficie_rango llega a 2.000 m2). Fuera
# de ellos el modelo extrapola sin control y puede dar cualquier cosa.
RANGOS = {
    "sup_total_m2": (10, 2000, "Superficie total (m²)"),
    "ambientes": (1, 15, "Ambientes"),
    "dormitorios": (0, 10, "Dormitorios"),
    "banos": (1, 10, "Baños"),
    "antiguedad_anios": (0, 150, "Antigüedad"),
    "venta_usd": (1_000, 20_000_000, "Precio de venta"),
}


def fuera_de_rango(prop: dict) -> list[str]:
    errores = []
    for k, (lo, hi, nombre) in RANGOS.items():
        x = prop.get(k)
        if x is not None and not pd.isna(x) and not lo <= x <= hi:
            errores.append(f"{nombre}: {x:g} está fuera del rango aceptado ({num(lo)} a {num(hi)})")
    return errores


# ==========================================================================
# ACTUALIZAR parametros.json DESDE ESTA ENTREGA (solo lectura)
# ==========================================================================

def _commit(ruta: str) -> str | None:
    try:
        r = subprocess.run(["git", "-C", ruta, "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def actualizar(entrega: str = ENTREGA_3) -> int:
    """
    Arma parametros.json. Usa las funciones de src/ (supuestos, costos,
    decision) para que cada tabla salga igual que en el pipeline. No escribe
    nada mas que parametros.json; el modelo se lee de data/processed/.
    """
    entrega = os.path.abspath(entrega)
    src = os.path.join(entrega, "src")
    analitico = os.path.join(entrega, "data", "processed", "dataset_analitico.csv")
    modelo = os.path.join(entrega, "data", "processed", "modelo_alquiler.joblib")
    temporal = os.path.join(entrega, "data", "processed", "temporal_vs_tradicional.csv")
    for p in (src, analitico, modelo, temporal):
        if not os.path.exists(p):
            print(f"No encuentro {p}")
            print("Corré antes el pipeline (ver Reproducir en el README).")
            return 1

    # Los modulos de src/ resuelven sus rutas desde la carpeta de la entrega.
    sys.path.insert(0, src)
    cwd = os.getcwd()
    os.chdir(entrega)
    try:
        import supuestos as S
        import costos as C
        import decision as D
        import eda
        import modelo_alquiler as M

        m = joblib.load(modelo)
        df = pd.read_csv(analitico, encoding="utf-8-sig", low_memory=False)
        ventas = df[df["operacion"] == "venta"].dropna(subset=["venta_usd", "sup_total_m2", "barrio"])
        alq = df[df["operacion"] == "alquiler"]
        alq_modelo = alq.dropna(subset=["alquiler_usd_mes", "sup_total_m2", "barrio"])

        # m2 de mercado de la VFH: celda barrio x tipo si tiene MIN_AVISOS_CELDA ventas
        g = ventas.groupby(["barrio", "tipo_familia"])["venta_m2_usd"]
        celda = g.median()[g.count() >= S.MIN_AVISOS_CELDA]
        m2_barrio_tipo = {f"{b}|{t}": round(float(v), 6) for (b, t), v in celda.items()}
        m2_barrio = ventas.groupby("barrio")["venta_m2_usd"].median()

        # m2 mediano de la celda barrio x tramo: contra eso se mide si es "barata"
        m2_celda = ventas.groupby(["barrio", "superficie_rango"])["venta_m2_usd"].median()

        alq_m2 = (alq_modelo["alquiler_usd_mes"] / alq_modelo["sup_total_m2"]).groupby(alq_modelo["barrio"]).median()
        n_celda_tipo = alq.groupby(["tipo_familia", "superficie_rango"]).size()

        # P3 por celda barrio x dormitorios, con las dos gestiones
        t = pd.read_csv(temporal, encoding="utf-8-sig")
        t["eq_auto"] = D.ocupacion_equilibrio(t, S.VACANCIA_PCT, autogestion=True)
        p3 = {f"{r.barrio}|{r.dormitorios_grupo}": {
                  "equilibrio_tercerizada_pct": float(r.ocupacion_equilibrio_pct),
                  "equilibrio_autogestion_pct": float(r.eq_auto),
                  "ocupacion_airbnb_pct": float(r.ocupacion_mediana_pct)}
              for r in t.itertuples()}

        liq = D.liquidez_por_ambientes(os.path.join(entrega, D.LIQUIDEZ))
        ok = df[(df["operacion"] == "venta") & (df["estimacion_confiable"] == 1)]
        u = df[df["universo_decision"] == True]  # noqa: E712 (columna booleana con nulos)

        P = {
            "origen": {
                "commit": _commit(entrega),
                "generado": datetime.now().isoformat(timespec="seconds"),
                "modelo_entrenado": m["metadata"]["entrenado"],
                "hash_entrenamiento_sha256": m["metadata"]["hash_entrenamiento_sha256"],
                "n_alquileres_entrenamiento": m["metadata"]["n_entrenamiento"],
                "cobertura_banda_calibrada": m["banda"]["cobertura_calibrada"],
            },
            "supuestos": {
                "tc_ars_usd": S.TC_ARS_USD,
                "vacancia_pct": S.VACANCIA_PCT,
                "gastos_sin_abl_pct": S.GASTOS_SIN_ABL_PCT,
                "presupuesto_usd": list(S.PRESUPUESTO_USD),
                "retorno_minimo_pct": list(S.RETORNO_MINIMO_BANDA),
                "margen_liquidez_pct": S.MARGEN_LIQUIDEZ_PCT,
                "horizonte_anios": S.HORIZONTE_ANIOS,
                "min_alq_barrio": M.MIN_ALQ_BARRIO,
                "min_alq_soporte": S.MIN_ALQ_SOPORTE,
                "ocupacion_ref_pct": S.OCUPACION_REF_PCT,
            },
            "abl": {
                "proporcion_vfh": m["proporcion_vfh"],
                "alicuota_base": S.ABL_ALICUOTA_BASE,
                "ponderacion_cg": S.ABL_PONDERACION_CG,
                "usc": S.ABL_USC,
                "umbral_recargo_vfh": S.ABL_UMBRAL_RECARGO_VFH,
                "recargo": S.ABL_RECARGO,
                "minimo_anual_ars": S.ABL_MINIMO_ANUAL_ARS,
                "tope_sobre_mercado": S.ABL_TOPE_SOBRE_MERCADO,
                "inmobiliario_tramos": [list(x) for x in S.INMOBILIARIO_TRAMOS],
                "coef_geografico": {b: float(np.mean(v)) for b, v in S.ABL_COEF_GEOGRAFICO.items()},
            },
            "entrada": {
                "comision_pct": list(S.COMISION_COMPRADOR_PCT),
                "escribano_pct": list(S.ESCRIBANO_PCT),
                "registrales_pct": list(S.REGISTRALES_PCT),
                "sellos_alicuota_pct": S.SELLOS_ALICUOTA_PCT,
                "sellos_alicuota_reducida_pct": S.SELLOS_ALICUOTA_REDUCIDA_PCT,
                "sellos_umbral_ars": S.SELLOS_UMBRAL_ARS,
                "sellos_parte_comprador": S.SELLOS_PARTE_COMPRADOR,
            },
            "refaccion": {
                "bano_usd": S.REFACCION_BANO_USD,
                "cocina_usd": S.REFACCION_COCINA_USD,
                "pintura_ars_m2": S.PINTURA_ARS_POR_M2,
                "integral_ars_m2": S.REFACCION_INTEGRAL_ARS_M2,
                "iva": S.IVA_GENERAL,
            },
            "banda": {
                "cortes_evidencia": [c if np.isfinite(c) else None for c in M.CORTES_EVIDENCIA],
                "grupos_evidencia": M.GRUPOS_EVIDENCIA,
                "ajuste_log_por_grupo": {k: float(v) for k, v in m["banda"]["ajuste_log_por_grupo"].items()},
            },
            "superficie_rango": {"cortes": [0, 35, 55, 80, 120, 2000],
                                 "etiquetas": ["hasta 35", "36-55", "56-80", "81-120", "120+"]},
            "barrios": sorted(ventas["barrio"].unique()),
            "nombre_barrio": {b: eda.nombre_barrio(b) for b in sorted(ventas["barrio"].unique())},
            "n_alq_barrio": {b: int(n) for b, n in alq_modelo.groupby("barrio").size().items()},
            "alquiler_m2_barrio": {b: round(float(v), 4) for b, v in alq_m2.items()},
            "m2_mercado_barrio_tipo": m2_barrio_tipo,
            "m2_mercado_barrio": {b: round(float(v), 6) for b, v in m2_barrio.items()},
            "m2_venta_celda": {f"{b}|{s}": round(float(v), 6) for (b, s), v in m2_celda.items() if pd.notna(v)},
            "n_alq_celda_tipo": {f"{t_}|{s}": int(n) for (t_, s), n in n_celda_tipo.items()},
            "dias_publicacion": {k: float(v) for k, v in liq.items()},
            "p3": p3,
            "mercado": {
                "n_ventas_confiables": int(len(ok)),
                "bruta_mediana_pct": round(float(ok["rent_bruta_pct"].median()), 2),
                "neta_mediana_pct": round(float(ok["rent_neta_pct"].median()), 2),
                "tir_mediana_pct": round(float(ok["tir_5a_pct"].median()), 2),
                "n_universo": int(len(u)),
                "universo_neta_min_pct": sorted(round(float(x), 2) for x in u["neta_min_pct"]),
                "universo_neta_max_pct": sorted(round(float(x), 2) for x in u["neta_max_pct"]),
            },
        }
    finally:
        os.chdir(cwd)

    with open(RUTA_PARAMETROS, "w", encoding="utf-8") as f:
        json.dump(P, f, ensure_ascii=False, indent=1)
    print(f"Parámetros actualizados en {RUTA_PARAMETROS}")
    print(f"    modelo entrenado el {P['origen']['modelo_entrenado']}, "
          f"commit {P['origen']['commit'] or 'desconocido'}")
    return 0


# ==========================================================================
# CARGA
# ==========================================================================

def cargar() -> tuple[dict, dict]:
    if not (os.path.exists(RUTA_MODELO) and os.path.exists(RUTA_PARAMETROS)):
        faltan = [r for r in (RUTA_MODELO, RUTA_PARAMETROS) if not os.path.exists(r)]
        print("No encuentro: " + ", ".join(faltan))
        print()
        print("El modelo lo guarda src/kpis.py; los parámetros se arman con:")
        print("    py simulador/simular.py --actualizar")
        sys.exit(1)
    m = joblib.load(RUTA_MODELO)
    with open(RUTA_PARAMETROS, encoding="utf-8") as f:
        P = json.load(f)
    return m, P


# ==========================================================================
# CALCULO — las mismas formulas que la Entrega 3 (kpis.py, costos.py,
# decision.py), vectorizadas: reciben un DataFrame con una fila por propiedad
# ==========================================================================

def grupo_evidencia(n_alq: pd.Series, P: dict) -> pd.Series:
    cortes = [np.inf if c is None else c for c in P["banda"]["cortes_evidencia"]]
    return pd.cut(n_alq.fillna(0), cortes, labels=P["banda"]["grupos_evidencia"], right=False).astype(str)


def superficie_rango(sup: pd.Series, P: dict) -> pd.Series:
    r = P["superficie_rango"]
    return pd.cut(sup, r["cortes"], labels=r["etiquetas"]).astype(str)


def estimar_alquiler(props: pd.DataFrame, m: dict) -> pd.DataFrame:
    """Alquiler central, percentiles 10 y 90 calibrados, y el post-refaccion."""
    X = props.copy()
    X["log_sup"] = np.log(X["sup_total_m2"].where(X["sup_total_m2"] > 0))
    X = X[m["columnas"]]
    b = m["banda"]
    d = props["_ajuste_banda"].values
    a = b["modelo_p10"].predict(X) - d
    c = b["modelo_p90"].predict(X) + d
    out = pd.DataFrame({
        "alquiler_est_usd_mes": (np.exp(m["pipeline"].predict(X)) * m["smearing"]).round(2),
        "alquiler_p10_usd_mes": np.exp(np.minimum(a, c)).round(2),
        "alquiler_p90_usd_mes": np.exp(np.maximum(a, c)).round(2),
    }, index=props.index)
    # Refaccionada: las mismas variables con a_reciclar = 0 y reciclado = 1
    rec = props["a_reciclar"] == 1
    post = pd.Series(np.nan, index=props.index)
    if rec.any():
        Xr = X.loc[rec].copy()
        Xr["a_reciclar"], Xr["reciclado"] = 0, 1
        post.loc[rec] = (np.exp(m["pipeline"].predict(Xr)) * m["smearing"]).round(2)
    out["alquiler_post_refaccion_usd_mes"] = post
    return out


def impuesto_inmobiliario(vfh: np.ndarray, A: dict) -> np.ndarray:
    tramos = A["inmobiliario_tramos"]
    desde = np.array([t[0] for t in tramos], dtype=float)
    i = np.clip(np.searchsorted(desde, vfh, side="right") - 1, 0, len(desde) - 1)
    cf = np.array([t[1] for t in tramos], dtype=float)[i]
    al = np.array([t[2] for t in tramos], dtype=float)[i]
    return (cf + (vfh - desde[i]) * al) * A["usc"]


def abl_ars_mes(props: pd.DataFrame, P: dict) -> pd.Series:
    """ABL mensual en pesos (Ley 6927, arts. 41 a 45) con la VFH aproximada, sin redondear."""
    A, tc = P["abl"], P["supuestos"]["tc_ars_usd"]
    clave = props["barrio"] + "|" + props["tipo_familia"]
    m2 = clave.map(P["m2_mercado_barrio_tipo"]).fillna(props["barrio"].map(P["m2_mercado_barrio"]))
    vfh = (A["proporcion_vfh"] * m2 * props["sup_total_m2"] * tc).to_numpy(dtype=float)
    cg = props["barrio"].map(A["coef_geografico"]).to_numpy(dtype=float)
    tasa = vfh * A["alicuota_base"] * (1 + cg * A["ponderacion_cg"]) * A["usc"]
    tasa = np.where(vfh > A["umbral_recargo_vfh"], tasa * (1 + A["recargo"]), tasa)
    total = np.maximum(impuesto_inmobiliario(vfh, A) + tasa, A["minimo_anual_ars"])
    total = np.minimum(total, props["venta_usd"].to_numpy(dtype=float) * tc * A["tope_sobre_mercado"])
    return pd.Series(total / 12, index=props.index)


def costos_entrada_pct(venta_usd: pd.Series, P: dict, escenario: str = "base") -> pd.Series:
    """Comision, escribano, registrales y la mitad de Sellos, como % del precio."""
    E = P["entrada"]
    i = {"base": 0, "alto": 1}[escenario]
    sellos = np.where(venta_usd * P["supuestos"]["tc_ars_usd"] <= E["sellos_umbral_ars"],
                      E["sellos_alicuota_reducida_pct"], E["sellos_alicuota_pct"]) * E["sellos_parte_comprador"]
    fijos = E["comision_pct"][i] + E["escribano_pct"][i] + E["registrales_pct"][i]
    return pd.Series(fijos + sellos, index=venta_usd.index).round(2)


def refaccion_usd(props: pd.DataFrame, P: dict, escenario: str = "base") -> pd.Series:
    """Refaccion de una unidad a reciclar: minima (base) o integral (alto)."""
    R, tc = P["refaccion"], P["supuestos"]["tc_ars_usd"]
    if escenario == "base":
        costo = (props["banos"].fillna(1).clip(lower=1) * R["bano_usd"] + R["cocina_usd"]
                 + R["pintura_ars_m2"] / tc * props["sup_total_m2"])
    else:
        costo = R["integral_ars_m2"] * (1 + R["iva"]) / tc * props["sup_total_m2"]
    return costo.where(props["a_reciclar"].fillna(0) == 1, 0.0).round(0)


def tir(neta_pct, costo_inicial_pct, anios: int) -> np.ndarray:
    """
    TIR anual en %: pagar el precio mas el costo inicial, cobrar la neta al
    final de cada anio y revender al mismo precio en dolares. Biseccion.
    """
    n = np.asarray(neta_pct, dtype=float) / 100
    c = np.asarray(costo_inicial_pct, dtype=float) / 100
    n, c = np.broadcast_arrays(n, c)
    t = np.arange(1, anios + 1)

    def vpn(r):
        desc = (1 + r[:, None]) ** -t
        return -(1 + c) + n * desc.sum(axis=1) + desc[:, -1]

    lo, hi = np.full(n.shape, -0.5), np.full(n.shape, 0.5)
    for _ in range(60):
        mid = (lo + hi) / 2
        positivo = vpn(mid) > 0
        lo, hi = np.where(positivo, mid, lo), np.where(positivo, hi, mid)
    return np.where(np.isnan(n) | np.isnan(c), np.nan, (lo + hi) / 2 * 100)


def neta(alquiler, venta, abl_ars, vacancia: float, gastos_sin_abl: float, tc: float):
    """Bruta x (1 - vacancia) x (1 - gastos), con el ABL en pesos sobre ese alquiler."""
    bruta = alquiler * 12 / venta * 100
    gastos = gastos_sin_abl + abl_ars / (alquiler * tc) * 100
    return bruta * (1 - vacancia / 100) * (1 - gastos / 100)


def simular(props: pd.DataFrame, m: dict, P: dict, vacancia: float | None = None) -> pd.DataFrame:
    """
    Todas las cifras de cada propiedad. `props` necesita barrio, tipo_familia,
    sup_total_m2, ambientes, dormitorios, banos, antiguedad_anios, las dummies
    y venta_usd (NaN si no se conoce el precio).
    """
    Sp = P["supuestos"]
    tc, gsa = Sp["tc_ars_usd"], Sp["gastos_sin_abl_pct"]
    vac = Sp["vacancia_pct"] if vacancia is None else vacancia
    props = props.copy()
    for c in CARACTERISTICAS:
        props[c] = props.get(c, 0)
        props[c] = props[c].fillna(0).astype(int)

    r = pd.DataFrame(index=props.index)
    r["n_alq_barrio"] = props["barrio"].map(P["n_alq_barrio"]).fillna(0).astype(int)
    r["estimacion_confiable"] = r["n_alq_barrio"] >= Sp["min_alq_barrio"]
    r["grupo_evidencia"] = grupo_evidencia(r["n_alq_barrio"], P)
    props["_ajuste_banda"] = r["grupo_evidencia"].map(P["banda"]["ajuste_log_por_grupo"])
    r = r.join(estimar_alquiler(props, m))
    r["alquiler_est_m2"] = (r["alquiler_est_usd_mes"] / props["sup_total_m2"]).round(2)
    r["referencia_barrio_usd_mes"] = (props["barrio"].map(P["alquiler_m2_barrio"]) * props["sup_total_m2"]).round(0)

    r["superficie_rango"] = superficie_rango(props["sup_total_m2"], P)
    r["n_alq_celda_tipo"] = (props["tipo_familia"] + "|" + r["superficie_rango"]).map(P["n_alq_celda_tipo"]).fillna(0).astype(int)
    r["en_soporte_modelo"] = r["n_alq_celda_tipo"] >= Sp["min_alq_soporte"]

    grupo_dorm = pd.cut(props["dormitorios"], [-0.5, 1, 2, 99], labels=["0-1", "2", "3+"]).astype(str)
    p3 = (props["barrio"] + "|" + grupo_dorm).map(P["p3"])
    for k in ("equilibrio_tercerizada_pct", "equilibrio_autogestion_pct", "ocupacion_airbnb_pct"):
        r[f"p3_{k}"] = p3.map(lambda d: d[k] if isinstance(d, dict) else np.nan).astype(float).round(1)
    amb = props["ambientes"].clip(lower=1)
    clave_amb = amb.map(lambda a: np.nan if pd.isna(a) else "5 ambientes y más" if a >= 5
                        else "1 ambiente" if a == 1 else f"{int(a)} ambientes")
    r["dias_publicacion_ambientes"] = clave_amb.map(P["dias_publicacion"])

    venta = props["venta_usd"].astype(float)
    if venta.isna().all():
        return r

    # KPIs 1 a 4 (kpis.py)
    alq = r["alquiler_est_usd_mes"]
    r["venta_usd"] = venta
    r["venta_m2_usd"] = (venta / props["sup_total_m2"]).round(2)
    # Como costos.py: el % sale del ABL sin redondear; el ABL en pesos se redondea
    abl_mes = abl_ars_mes(props, P)
    r["abl_ars_mes"] = abl_mes.round(0)
    r["abl_pct"] = (abl_mes / (alq * tc) * 100).round(2)
    r["gastos_pct"] = (gsa + r["abl_pct"]).round(2)
    r["rent_bruta_pct"] = (alq * 12 / venta * 100).round(2)
    r["rent_neta_pct"] = (r["rent_bruta_pct"] * (1 - vac / 100) * (1 - r["gastos_pct"] / 100)).round(2)
    r["rent_bruta_min"] = (r["alquiler_p10_usd_mes"] * 12 / venta * 100).round(2)
    r["rent_bruta_max"] = (r["alquiler_p90_usd_mes"] * 12 / venta * 100).round(2)
    r["meses_repago"] = (venta / alq).round(0)

    # Costos de entrada, refaccion y TIR a 5 anios (kpis.py)
    r["costos_entrada_pct"] = costos_entrada_pct(venta, P, "base")
    r["costos_entrada_alto_pct"] = costos_entrada_pct(venta, P, "alto")
    r["refaccion_usd"] = refaccion_usd(props.assign(venta_usd=venta), P, "base")
    r["refaccion_integral_usd"] = refaccion_usd(props.assign(venta_usd=venta), P, "alto")
    alq_post = r["alquiler_post_refaccion_usd_mes"].fillna(alq)
    neta_post = neta(alq_post, venta, r["abl_ars_mes"], vac, gsa, tc).round(2)
    inicial = r["costos_entrada_pct"] + r["refaccion_usd"] / venta * 100
    r["tir_5a_pct"] = pd.Series(tir(neta_post, inicial, Sp["horizonte_anios"]), index=r.index).round(2)

    # Decision (decision.py)
    r["neta_min_pct"] = neta(r["alquiler_p10_usd_mes"], venta, r["abl_ars_mes"], vac, gsa, tc).round(2)
    r["neta_max_pct"] = neta(r["alquiler_p90_usd_mes"], venta, r["abl_ars_mes"], vac, gsa, tc).round(2)
    sube = (r["alquiler_post_refaccion_usd_mes"] / alq).fillna(1.0)
    n_min = neta(r["alquiler_p10_usd_mes"] * sube, venta, r["abl_ars_mes"], vac, gsa, tc)
    r["tir_5a_min_pct"] = pd.Series(tir(n_min, inicial, Sp["horizonte_anios"]), index=r.index).round(2)
    r["en_presupuesto"] = venta.between(*Sp["presupuesto_usd"])
    r["universo_decision"] = r["estimacion_confiable"] & r["en_presupuesto"] & r["en_soporte_modelo"]
    umbral = Sp["retorno_minimo_pct"][1] + Sp["margen_liquidez_pct"]
    r["p1_comprar"] = r["universo_decision"] & (r["neta_min_pct"] > umbral)
    r["p1_comprar_con_entrada"] = r["universo_decision"] & (r["tir_5a_min_pct"] > umbral)
    lo = np.array(P["mercado"]["universo_neta_min_pct"])
    hi = np.array(P["mercado"]["universo_neta_max_pct"])
    # P2: cuantas del universo la superan con claridad (su pesimista > nuestra optimista), y a cuantas supera
    r["p2_la_superan"] = len(lo) - np.searchsorted(lo, r["neta_max_pct"].values, side="right")
    r["p2_supera_a"] = np.searchsorted(hi, r["neta_min_pct"].values, side="left")
    m2c = (props["barrio"] + "|" + r["superficie_rango"]).map(P["m2_venta_celda"])
    r["m2_relativo_celda"] = (r["venta_m2_usd"] / m2c).round(2)
    return r


# ==========================================================================
# PRESENTACION
# ==========================================================================

def num(x: float, d: int = 0) -> str:
    """Formato argentino: miles con punto, decimales con coma."""
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(x: float, d: int = 2) -> str:
    return f"{num(x, d)}%"


def con_signo(x: float, d: int = 0) -> str:
    return ("+" if x >= 0 else "") + num(x, d)


def usd(x: float) -> str:
    return f"USD {num(x)}"


def titulo(t: str) -> None:
    print()
    print("=" * 66)
    print(t)
    print("=" * 66)


def mostrar(prop: dict, r: pd.Series, P: dict, vacancia: float) -> None:
    Sp, M_ = P["supuestos"], P["mercado"]
    piso, techo = Sp["retorno_minimo_pct"]

    barrio = P["nombre_barrio"].get(prop["barrio"], prop["barrio"])
    titulo("PROPIEDAD SIMULADA")
    print(f"  Barrio         : {barrio}")
    print(f"  Superficie     : {num(prop['sup_total_m2'])} m² (tramo {r['superficie_rango']})")
    for k, nombre in [("ambientes", "Ambientes"), ("dormitorios", "Dormitorios"), ("banos", "Baños")]:
        if prop.get(k) is not None and not pd.isna(prop.get(k)):
            print(f"  {nombre:<15}: {num(prop[k])}")
    a = prop.get("antiguedad_anios")
    if a is not None and not pd.isna(a):
        print(f"  Antigüedad     : {'a estrenar' if a == 0 else num(a) + ' años'}")
    print(f"  Tipo           : {prop['tipo_familia']}")
    activas = [n for c, n in CARACTERISTICAS.items() if prop.get(c)]
    print(f"  Características: {', '.join(activas) if activas else '(ninguna)'}")

    titulo("ALQUILER ESTIMADO")
    print(f"  {usd(r['alquiler_est_usd_mes'])} por mes  (USD {num(r['alquiler_est_m2'], 1)} por m²)")
    print(f"  Banda p10-p90  : {usd(r['alquiler_p10_usd_mes'])} a {usd(r['alquiler_p90_usd_mes'])}")
    print("                   fuera de muestra, 8 de cada 10 alquileres reales caen en su banda")
    if pd.notna(r["referencia_barrio_usd_mes"]):
        dif = (r["alquiler_est_usd_mes"] / r["referencia_barrio_usd_mes"] - 1) * 100
        print(f"  Control        : con el alquiler mediano por m² de {barrio} daría "
              f"{usd(r['referencia_barrio_usd_mes'])};")
        print(f"                   el modelo estima {con_signo(dif)}% por sus características")
    if pd.notna(r["alquiler_post_refaccion_usd_mes"]):
        sube = (r["alquiler_post_refaccion_usd_mes"] / r["alquiler_est_usd_mes"] - 1) * 100
        print(f"  Refaccionada   : {usd(r['alquiler_post_refaccion_usd_mes'])} por mes ({con_signo(sube)}%)")
    print()
    if r["estimacion_confiable"]:
        print(f"  Basado en {r['n_alq_barrio']} alquileres de {barrio} "
              f"(grupo de evidencia {r['grupo_evidencia']}).")
    else:
        print(f"  AVISO: {barrio} tiene {r['n_alq_barrio']} alquileres en la muestra "
              f"(menos de {Sp['min_alq_barrio']}). La estimación")
        print("  extrapola desde otros barrios: el análisis no la considera confiable.")
    if not r["en_soporte_modelo"]:
        print(f"  AVISO: hay {r['n_alq_celda_tipo']} alquileres de {prop['tipo_familia']} de "
              f"{r['superficie_rango']} m² (menos de {Sp['min_alq_soporte']}).")
        print("  Fuera del soporte del modelo el alquiler es extrapolación: la decisión no la recomienda.")

    if pd.isna(r.get("venta_usd", np.nan)):
        print()
        print("  Pasá el precio de venta (--venta) para ver rentabilidad, TIR y decisión.")
        print()
        return

    titulo("RENTABILIDAD (KPIs 1 a 4)")
    print(f"  Precio de venta   : {usd(r['venta_usd'])}  ({usd(r['venta_m2_usd'])} por m²)")
    if pd.notna(r["m2_relativo_celda"]):
        print(f"  Contra su celda   : su m² vale {num(r['m2_relativo_celda'], 2)} veces el mediano de "
              f"{barrio}, {r['superficie_rango']} m²")
    print(f"  Bruta             : {pct(r['rent_bruta_pct'])}   banda {pct(r['rent_bruta_min'])} "
          f"a {pct(r['rent_bruta_max'])}")
    print(f"  ABL               : ARS {num(r['abl_ars_mes'])} por mes, {pct(r['abl_pct'])} del alquiler "
          "(Ley 6927, VFH aproximada)")
    print(f"  Gastos            : {pct(r['gastos_pct'])} del alquiler: el ABL más {pct(Sp['gastos_sin_abl_pct'])} "
          "de administración,")
    print("                      expensas extraordinarias y mantenimiento")
    print(f"  Vacancia          : {pct(vacancia)}")
    print(f"  Neta              : {pct(r['rent_neta_pct'])}   banda {pct(r['neta_min_pct'])} "
          f"a {pct(r['neta_max_pct'])}")
    print(f"  Repago            : {num(r['meses_repago'])} meses ({num(r['meses_repago'] / 12, 1)} años)")

    titulo(f"COSTOS DE ENTRADA Y TIR A {Sp['horizonte_anios']} AÑOS")
    print(f"  Costos de entrada : {pct(r['costos_entrada_pct'])} del precio, "
          f"{usd(r['costos_entrada_pct'] / 100 * r['venta_usd'])}; escenario alto {pct(r['costos_entrada_alto_pct'])}")
    print("                      comisión, escribano, certificados y la mitad de Sellos")
    if r["refaccion_usd"] > 0:
        print(f"  Refacción mínima  : {usd(r['refaccion_usd'])} (baño, cocina y pintura); "
              f"integral: {usd(r['refaccion_integral_usd'])}")
    print(f"  TIR a 5 años      : {pct(r['tir_5a_pct'])}   pesimista {pct(r['tir_5a_min_pct'])}")
    print("                      reventa al mismo precio en dólares, sin apreciación ni costos de salida")

    titulo("DECISIÓN")
    print(f"  Vara    : banda de retorno mínimo de {pct(piso)} a {pct(techo)} (TIR de una ON en dólares)")
    print(f"  Mercado : neta mediana {pct(M_['neta_mediana_pct'])}, TIR mediana {pct(M_['tir_mediana_pct'])} "
          f"({num(M_['n_ventas_confiables'])} ventas)")
    print()
    if r["rent_neta_pct"] >= techo:
        lectura = "supera el techo de la banda"
    elif r["rent_neta_pct"] >= piso:
        lectura = "queda dentro de la banda"
    else:
        lectura = f"queda {num(piso - r['rent_neta_pct'], 2)} pp debajo del piso"
    print(f"  La neta central {lectura}; con los costos de comprar, la TIR es {pct(r['tir_5a_pct'])}.")

    faltan = []
    if not r["en_presupuesto"]:
        lo_, hi_ = Sp["presupuesto_usd"]
        faltan.append(f"está fuera del presupuesto ({usd(lo_)} a {usd(hi_)})")
    if not r["estimacion_confiable"]:
        faltan.append("su barrio tiene pocos alquileres")
    if not r["en_soporte_modelo"]:
        faltan.append("está fuera del soporte del modelo")
    umbral = techo + Sp["margen_liquidez_pct"]
    print()
    if faltan:
        print(f"  P1 ¿comprar?    : fuera del universo de la decisión: {'; '.join(faltan)}.")
        print(f"                    Su neta pesimista es {pct(r['neta_min_pct'])}, contra un umbral de {pct(umbral)}.")
    elif r["p1_comprar"]:
        print(f"  P1 ¿comprar?    : PASA. La neta pesimista ({pct(r['neta_min_pct'])}) supera {pct(umbral)}.")
        print("                    Es una propiedad A VERIFICAR, no una recomendación: las que pasan suelen")
        print("                    ser más baratas que su celda por algo que el aviso no dice.")
        print(f"                    Con costos de entrada {'también pasa' if r['p1_comprar_con_entrada'] else 'ya no pasa'} "
              f"(TIR pesimista {pct(r['tir_5a_min_pct'])}).")
    else:
        print(f"  P1 ¿comprar?    : NO PASA. La neta pesimista ({pct(r['neta_min_pct'])}) no supera {pct(umbral)}.")
    if not faltan:
        n_u = num(M_["n_universo"])
        if r["p2_la_superan"] == 0:
            print(f"  P2 ¿cuál?       : entraría en la lista corta: ninguna de las {n_u} propiedades del universo")
            print("                    la supera con claridad (sus bandas se superponen).")
        else:
            print(f"  P2 ¿cuál?       : {num(r['p2_la_superan'])} de {n_u} propiedades del universo la superan con")
            print("                    claridad: su neta pesimista está arriba de la optimista de esta.")
        print(f"                    Esta supera con claridad a {num(r['p2_supera_a'])}.")

    if pd.notna(r["p3_equilibrio_tercerizada_pct"]):
        print(f"  P3 ¿temporal?   : en {barrio}, con esos dormitorios, el temporal empata con "
              f"{pct(r['p3_equilibrio_tercerizada_pct'], 1)} de ocupación")
        print(f"                    tercerizado ({pct(r['p3_equilibrio_autogestion_pct'], 1)} autogestionado). "
              f"Inside Airbnb mide {pct(r['p3_ocupacion_airbnb_pct'], 1)} y la prensa,")
        print(f"                    {pct(Sp['ocupacion_ref_pct'], 0)} para CABA. Conviene el tradicional, salvo "
              "autogestión con evidencia")
        print("                    de más de la mitad del año ocupado.")
    else:
        print("  P3 ¿temporal?   : no hay datos de alquiler temporario para esa celda barrio x dormitorios.")
    if pd.notna(r["dias_publicacion_ambientes"]):
        print(f"  Liquidez        : un aviso con esos ambientes pasa unos {num(r['dias_publicacion_ambientes'])} "
              "días publicado (IDECBA, toda la Ciudad).")

    print()
    print("  Límites: precios de publicación, no de cierre; una sola inmobiliaria (~8% más barata que")
    print("  el mercado); sin apreciación, costos de salida ni riesgo legal.")
    print()


# ==========================================================================
# MODO INTERACTIVO
# ==========================================================================

def normalizar(texto: str) -> str:
    """minusculas y sin tildes, como estan los barrios en el dataset."""
    t = unicodedata.normalize("NFKD", texto.strip().lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def leer(prompt: str, default: str = "") -> str:
    """input() que no revienta si se corta la entrada (Ctrl+C o pipe vacio)."""
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return default


def preguntar(texto: str, default=None, tipo=float, opciones=None, rango=None):
    """Pregunta con valor por defecto y validacion."""
    for _ in range(10):          # tope de reintentos, evita bucle infinito
        sufijo = f" [{default}]" if default is not None else ""
        r = leer(f"  {texto}{sufijo}: ")
        if not r and default is not None:
            return default
        if not r:
            print("    Requerido.")
            continue
        if tipo is str:
            r = normalizar(r)
        if opciones and r not in opciones:
            print(f"    No reconozco '{r}'. Ejemplos: {', '.join(opciones[:5])}")
            continue
        if tipo is str:
            return r
        try:
            x = tipo(r.replace(",", "."))
        except ValueError:
            print("    Valor inválido, probá con un número.")
            continue
        if rango and not rango[0] <= x <= rango[1]:
            print(f"    Fuera de rango: entre {rango[0]:g} y {rango[1]:g}.")
            continue
        return x
    print("    Demasiados intentos: uso el valor por defecto.")
    return default


def interactivo(P: dict) -> dict:
    titulo("SIMULADOR — enter para aceptar el valor por defecto")
    print()
    barrios = P["barrios"]
    print(f"  Barrios disponibles ({len(barrios)}):")
    for i in range(0, len(barrios), 4):
        print("    " + "  ".join(f"{b:<18}" for b in barrios[i:i + 4]))
    print()

    prop = {}
    prop["barrio"] = preguntar("Barrio", "palermo", str, barrios)
    prop["sup_total_m2"] = preguntar("Superficie total (m²)", 50.0, rango=RANGOS["sup_total_m2"])
    prop["ambientes"] = preguntar("Ambientes", 2.0, rango=RANGOS["ambientes"])
    prop["dormitorios"] = preguntar("Dormitorios", 1.0, rango=RANGOS["dormitorios"])
    prop["banos"] = preguntar("Baños", 1.0, rango=RANGOS["banos"])
    prop["antiguedad_anios"] = preguntar("Antigüedad en años (0 = a estrenar)", 30.0,
                                         rango=RANGOS["antiguedad_anios"])
    prop["tipo_familia"] = preguntar("Tipo (departamento/ph/casa)", "departamento", str, TIPOS)

    print()
    print("  Características (s/n):")
    for c, nombre in CARACTERISTICAS.items():
        r = leer(f"    ¿{nombre}? [n]: ", "n").lower()
        prop[c] = 1 if r in ("s", "si", "sí", "y", "yes") else 0

    print()
    prop["venta_usd"] = None
    for _ in range(10):
        v = leer("  Precio de venta en USD, sin decimales (enter para omitir): ")
        if not v:
            break
        try:
            x = float(v.replace(".", "").replace(",", ""))
        except ValueError:
            print("    Valor inválido, probá con un número.")
            continue
        lo, hi, _ = RANGOS["venta_usd"]
        if lo <= x <= hi:
            prop["venta_usd"] = x
            break
        print(f"    Fuera de rango: entre {num(lo)} y {num(hi)}.")
    return prop


# ==========================================================================
# PAGINA WEB — el mismo calculo en JavaScript (web/motor.js)
# ==========================================================================

def modelo_lineal(pipe, P: dict) -> dict:
    """
    Un pipeline del modelo (imputacion + escala + one-hot + modelo lineal)
    como coeficientes: log(alquiler) = intercepto + sum(coef x (x - media) / escala)
    + efecto del barrio + efecto del tipo + sum(coef x dummy). El efecto de cada
    categoria sale de transformarla con el mismo OneHotEncoder, asi que las
    infrecuentes y las desconocidas quedan como las trata scikit-learn.
    """
    pre, mod = pipe.named_steps["pre"], pipe.named_steps["mod"]
    coef = np.asarray(mod.coef_, dtype=float).ravel()
    nombres = list(pre.get_feature_names_out())
    pos = {n: i for i, n in enumerate(nombres)}
    num = pre.named_transformers_["num"]
    imp, esc = num.named_steps["imp"], num.named_steps["esc"]
    cols_num = list(pre.transformers_[0][2])
    ohe = pre.named_transformers_["cat"]
    cols_cat = list(pre.transformers_[1][2])
    cols_dum = list(pre.transformers_[2][2])

    def efectos(col: str, valores: list[str]) -> dict:
        base = {c: ohe.categories_[i][0] for i, c in enumerate(cols_cat)}
        filas = pd.DataFrame([{**base, col: v} for v in valores])[cols_cat]
        Z = ohe.transform(filas)
        Z = Z.toarray() if hasattr(Z, "toarray") else np.asarray(Z)
        bloque = [k for k, n in enumerate(ohe.get_feature_names_out(cols_cat)) if n.startswith(f"{col}_")]
        ini = pos[f"cat__{ohe.get_feature_names_out(cols_cat)[bloque[0]]}"]
        c = coef[ini:ini + len(bloque)]
        return {v: float(Z[k, bloque] @ c) for k, v in enumerate(valores)}

    return {
        "intercepto": float(np.ravel(mod.intercept_)[0]),
        "numericas": {c: {"mediana": float(imp.statistics_[k]), "media": float(esc.mean_[k]),
                          "escala": float(esc.scale_[k]), "coef": float(coef[pos[f"num__{c}"]])}
                      for k, c in enumerate(cols_num)},
        "barrio": efectos("barrio", P["barrios"]),
        "tipo": efectos("tipo_familia", TIPOS),
        "dummies": {c: float(coef[pos[f"dum__{c}"]]) for c in cols_dum},
    }


def predecir_lineal(L: dict, X: pd.DataFrame) -> np.ndarray:
    """La prediccion en log con los coeficientes exportados (lo que hace motor.js)."""
    y = np.full(len(X), L["intercepto"])
    for c, d in L["numericas"].items():
        x = X[c].astype(float).fillna(d["mediana"]).to_numpy()
        y = y + d["coef"] * (x - d["media"]) / d["escala"]
    y = y + X["barrio"].map(L["barrio"]).fillna(0).to_numpy()
    y = y + X["tipo_familia"].map(L["tipo"]).fillna(0).to_numpy()
    for c, k in L["dummies"].items():
        y = y + k * X[c].astype(float).to_numpy()
    return y


def exportar_modelo(m: dict, P: dict) -> dict:
    b = m["banda"]
    return {"smearing": m["smearing"], "columnas": m["columnas"],
            "central": modelo_lineal(m["pipeline"], P),
            "p10": modelo_lineal(b["modelo_p10"], P),
            "p90": modelo_lineal(b["modelo_p90"], P)}


def generar_html(m: dict, P: dict, salida: str) -> int:
    """Arma una pagina autocontenida: plantilla + motor.js + modelo y parametros."""
    web = os.path.join(AQUI, "web")
    plantilla = os.path.join(web, "plantilla.html")
    motor = os.path.join(web, "motor.js")
    for ruta in (plantilla, motor):
        if not os.path.exists(ruta):
            print(f"No encuentro {ruta}")
            return 1
    datos = {"modelo": exportar_modelo(m, P), "parametros": P,
             "caracteristicas": CARACTERISTICAS, "rangos": {k: v[:2] for k, v in RANGOS.items()}}
    # "</" cortaria el <script>; "<\/" es el mismo texto para JSON
    js = json.dumps(datos, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    with open(plantilla, encoding="utf-8") as f:
        html = f.read()
    with open(motor, encoding="utf-8") as f:
        html = html.replace("/*__MOTOR__*/", f.read())
    html = html.replace("/*__DATOS__*/", f"const DATOS = {js};")
    with open(salida, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Página generada: {salida} ({os.path.getsize(salida) / 1024:,.0f} KB)")
    return 0


# ==========================================================================
# MAIN
# ==========================================================================

def main() -> int:
    p = argparse.ArgumentParser(
        description="Simulador de alquiler, rentabilidad y decision (modelo de la 3ra pre-entrega)",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    p.add_argument("--actualizar", action="store_true",
                   help="vuelve a armar parametros.json con la salida del pipeline")
    p.add_argument("--barrio")
    p.add_argument("--m2", type=float, help="superficie total")
    p.add_argument("--ambientes", type=float)
    p.add_argument("--dormitorios", type=float)
    p.add_argument("--banos", type=float, default=1)
    p.add_argument("--antiguedad", type=float)
    p.add_argument("--tipo", default="departamento", choices=TIPOS)
    p.add_argument("--venta", type=float, help="precio de venta en USD (calcula rentabilidad, TIR y decision)")
    p.add_argument("--vacancia", type=float, default=None,
                   help="vacancia del alquiler tradicional, en %% (por defecto, la de supuestos.py)")
    p.add_argument("--json", action="store_true", help="imprime el resultado como JSON")
    p.add_argument("--html", nargs="?", const=os.path.join(AQUI, "simulador.html"), metavar="SALIDA",
                   help="genera la pagina web interactiva (por defecto, simulador/simulador.html)")
    for c in CARACTERISTICAS:
        p.add_argument(f"--{c.replace('_txt', '').replace('_', '-')}", dest=c, action="store_true")
    args = p.parse_args()
    # En consola Python escribe Unicode; redirigido (archivo, pipe, --json), en UTF-8
    if not sys.stdout.isatty():
        sys.stdout.reconfigure(encoding="utf-8")
    if not sys.stdin.isatty():
        sys.stdin.reconfigure(encoding="utf-8")

    if args.actualizar:
        return actualizar()

    m, P = cargar()
    if args.html:
        return generar_html(m, P, args.html)
    if not args.json:
        o = P["origen"]
        print(f"Modelo de la Entrega 3 — entrenado el {o['modelo_entrenado'][:10]} con "
              f"{num(o['n_alquileres_entrenamiento'])} alquileres; parámetros del {o['generado'][:10]}")

    if args.barrio and args.m2:
        prop = {
            "barrio": normalizar(args.barrio), "sup_total_m2": args.m2,
            "ambientes": args.ambientes, "dormitorios": args.dormitorios,
            "banos": args.banos, "antiguedad_anios": args.antiguedad,
            "tipo_familia": args.tipo, "venta_usd": args.venta,
        }
        for c in CARACTERISTICAS:
            prop[c] = int(getattr(args, c, False))
        if prop["barrio"] not in P["barrios"]:
            print(f"\nBarrio '{prop['barrio']}' no está en el modelo.")
            print("Disponibles:", ", ".join(P["barrios"]))
            return 1
        errores = fuera_de_rango(prop)
        if errores:
            print()
            print("\n".join(errores))
            return 1
    else:
        prop = interactivo(P)

    fila = pd.DataFrame([prop]).astype({"ambientes": float, "dormitorios": float, "banos": float,
                                        "antiguedad_anios": float, "venta_usd": float})
    vacancia = P["supuestos"]["vacancia_pct"] if args.vacancia is None else args.vacancia
    r = simular(fila, m, P, vacancia).iloc[0]

    if args.json:
        salida = {"propiedad": prop, "vacancia_pct": vacancia,
                  "resultado": {k: (None if pd.isna(v) else v.item() if hasattr(v, "item") else v)
                                for k, v in r.items()}}
        print(json.dumps(salida, ensure_ascii=False, indent=1))
    else:
        mostrar(prop, r, P, vacancia)
    return 0


if __name__ == "__main__":
    sys.exit(main())
