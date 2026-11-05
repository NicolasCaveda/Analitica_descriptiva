// motor.js — El calculo de simular.py, en JavaScript, para la pagina web.
//
// Mismas formulas y mismos redondeos que simular() (y que la Entrega 3:
// kpis.py, costos.py y decision.py). El modelo llega como coeficientes
// (simular.py, modelo_lineal): el Ridge y las regresiones cuantilicas son
// lineales en log(alquiler).
//
// Si se cambia una formula aca, hay que cambiarla tambien en simular.py.

"use strict";

const Motor = (() => {
  // pandas/numpy redondean "a par" (rint): 0,125 -> 0,12. Math.round sube siempre.
  function redondear(x, d = 0) {
    if (x === null || Number.isNaN(x)) return NaN;
    const f = 10 ** d;
    const y = x * f;
    let r = Math.round(y);
    if (Math.abs(y % 1) === 0.5) r = 2 * Math.round(y / 2);
    return r / f;
  }

  const vacio = (x) => x === null || x === undefined || Number.isNaN(x);

  // --- Alquiler ---------------------------------------------------------------

  function predecirLog(L, prop) {
    const x = { ...prop, log_sup: prop.sup_total_m2 > 0 ? Math.log(prop.sup_total_m2) : NaN };
    let y = L.intercepto;
    for (const [c, d] of Object.entries(L.numericas)) {
      const v = vacio(x[c]) ? d.mediana : x[c];
      y += (d.coef * (v - d.media)) / d.escala;
    }
    y += L.barrio[prop.barrio] ?? 0;
    y += L.tipo[prop.tipo_familia] ?? 0;
    for (const [c, k] of Object.entries(L.dummies)) y += k * (prop[c] || 0);
    return y;
  }

  function grupoEvidencia(n, P) {
    const cortes = P.banda.cortes_evidencia.map((c) => (c === null ? Infinity : c));
    for (let i = 0; i < cortes.length - 1; i++) {
      if (n >= cortes[i] && n < cortes[i + 1]) return P.banda.grupos_evidencia[i];
    }
    return P.banda.grupos_evidencia[P.banda.grupos_evidencia.length - 1];
  }

  function superficieRango(sup, P) {
    const { cortes, etiquetas } = P.superficie_rango;
    for (let i = 0; i < etiquetas.length; i++) {
      if (sup > cortes[i] && sup <= cortes[i + 1]) return etiquetas[i];
    }
    return null;
  }

  function grupoDormitorios(d) {
    if (vacio(d)) return null;
    if (d > -0.5 && d <= 1) return "0-1";
    if (d > 1 && d <= 2) return "2";
    if (d > 2 && d <= 99) return "3+";
    return null;
  }

  function claveAmbientes(a) {
    if (vacio(a)) return null;
    a = Math.max(a, 1);
    if (a >= 5) return "5 ambientes y más";
    if (a === 1) return "1 ambiente";
    return `${Math.trunc(a)} ambientes`;
  }

  // --- ABL (Ley 6927, arts. 41 a 45) ------------------------------------------

  function impuestoInmobiliario(vfh, A) {
    const t = A.inmobiliario_tramos;
    let i = 0;
    while (i + 1 < t.length && vfh >= t[i + 1][0]) i++;
    return (t[i][1] + (vfh - t[i][0]) * t[i][2]) * A.usc;
  }

  // ABL mensual en pesos, sin redondear
  function ablArsMes(prop, P) {
    const A = P.abl;
    const tc = P.supuestos.tc_ars_usd;
    const m2 = P.m2_mercado_barrio_tipo[`${prop.barrio}|${prop.tipo_familia}`] ?? P.m2_mercado_barrio[prop.barrio];
    const vfh = A.proporcion_vfh * m2 * prop.sup_total_m2 * tc;
    const cg = A.coef_geografico[prop.barrio];
    let tasa = vfh * A.alicuota_base * (1 + cg * A.ponderacion_cg) * A.usc;
    if (vfh > A.umbral_recargo_vfh) tasa *= 1 + A.recargo;
    let total = Math.max(impuestoInmobiliario(vfh, A) + tasa, A.minimo_anual_ars);
    total = Math.min(total, prop.venta_usd * tc * A.tope_sobre_mercado);
    return total / 12;
  }

  // --- Costos de entrada, refaccion y TIR ---------------------------------------

  function costosEntradaPct(venta, P, escenario = "base") {
    const E = P.entrada;
    const i = escenario === "base" ? 0 : 1;
    const alicuota = venta * P.supuestos.tc_ars_usd <= E.sellos_umbral_ars
      ? E.sellos_alicuota_reducida_pct : E.sellos_alicuota_pct;
    const fijos = E.comision_pct[i] + E.escribano_pct[i] + E.registrales_pct[i];
    return redondear(fijos + alicuota * E.sellos_parte_comprador, 2);
  }

  function refaccionUsd(prop, P, escenario = "base") {
    if ((prop.a_reciclar || 0) !== 1) return 0;
    const R = P.refaccion;
    const tc = P.supuestos.tc_ars_usd;
    let costo;
    if (escenario === "base") {
      const banos = Math.max(vacio(prop.banos) ? 1 : prop.banos, 1);
      costo = banos * R.bano_usd + R.cocina_usd + (R.pintura_ars_m2 / tc) * prop.sup_total_m2;
    } else {
      costo = ((R.integral_ars_m2 * (1 + R.iva)) / tc) * prop.sup_total_m2;
    }
    return redondear(costo, 0);
  }

  // TIR anual en %: pagar precio + costo inicial, cobrar la neta cada anio, revender al mismo precio
  function tir(netaPct, costoPct, anios) {
    if (vacio(netaPct) || vacio(costoPct)) return NaN;
    const n = netaPct / 100;
    const c = costoPct / 100;
    const vpn = (r) => {
      let s = -(1 + c);
      let desc = 1;
      for (let t = 1; t <= anios; t++) {
        desc = (1 + r) ** -t;
        s += n * desc;
      }
      return s + desc;
    };
    let lo = -0.5;
    let hi = 0.5;
    for (let k = 0; k < 60; k++) {
      const mid = (lo + hi) / 2;
      if (vpn(mid) > 0) lo = mid; else hi = mid;
    }
    return ((lo + hi) / 2) * 100;
  }

  function neta(alquiler, venta, ablArs, vacancia, gastosSinAbl, tc) {
    const bruta = (alquiler * 12) / venta * 100;
    const gastos = gastosSinAbl + (ablArs / (alquiler * tc)) * 100;
    return bruta * (1 - vacancia / 100) * (1 - gastos / 100);
  }

  // cuantos valores de un arreglo ordenado son > x (o >= si estricto = false)
  function cuantosMayores(ordenado, x) {
    let lo = 0;
    let hi = ordenado.length;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (ordenado[mid] <= x) lo = mid + 1; else hi = mid;
    }
    return ordenado.length - lo;
  }

  function cuantosMenores(ordenado, x) {
    let lo = 0;
    let hi = ordenado.length;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (ordenado[mid] < x) lo = mid + 1; else hi = mid;
    }
    return lo;
  }

  // --- Todo junto: el equivalente de simular() para una propiedad -------------

  function simular(prop, M, P, vacancia = null) {
    const Sp = P.supuestos;
    const tc = Sp.tc_ars_usd;
    const gsa = Sp.gastos_sin_abl_pct;
    const vac = vacancia === null ? Sp.vacancia_pct : vacancia;
    const r = {};

    r.n_alq_barrio = P.n_alq_barrio[prop.barrio] ?? 0;
    r.estimacion_confiable = r.n_alq_barrio >= Sp.min_alq_barrio;
    r.grupo_evidencia = grupoEvidencia(r.n_alq_barrio, P);
    const d = P.banda.ajuste_log_por_grupo[r.grupo_evidencia];

    r.alquiler_est_usd_mes = redondear(Math.exp(predecirLog(M.central, prop)) * M.smearing, 2);
    const a = predecirLog(M.p10, prop) - d;
    const b = predecirLog(M.p90, prop) + d;
    r.alquiler_p10_usd_mes = redondear(Math.exp(Math.min(a, b)), 2);
    r.alquiler_p90_usd_mes = redondear(Math.exp(Math.max(a, b)), 2);
    r.alquiler_post_refaccion_usd_mes = prop.a_reciclar === 1
      ? redondear(Math.exp(predecirLog(M.central, { ...prop, a_reciclar: 0, reciclado: 1 })) * M.smearing, 2)
      : NaN;
    r.alquiler_est_m2 = redondear(r.alquiler_est_usd_mes / prop.sup_total_m2, 2);
    const refM2 = P.alquiler_m2_barrio[prop.barrio];
    r.referencia_barrio_usd_mes = refM2 === undefined ? NaN : redondear(refM2 * prop.sup_total_m2, 0);

    r.superficie_rango = superficieRango(prop.sup_total_m2, P);
    r.n_alq_celda_tipo = P.n_alq_celda_tipo[`${prop.tipo_familia}|${r.superficie_rango}`] ?? 0;
    r.en_soporte_modelo = r.n_alq_celda_tipo >= Sp.min_alq_soporte;

    const p3 = P.p3[`${prop.barrio}|${grupoDormitorios(prop.dormitorios)}`];
    r.p3_equilibrio_tercerizada_pct = p3 ? redondear(p3.equilibrio_tercerizada_pct, 1) : NaN;
    r.p3_equilibrio_autogestion_pct = p3 ? redondear(p3.equilibrio_autogestion_pct, 1) : NaN;
    r.p3_ocupacion_airbnb_pct = p3 ? redondear(p3.ocupacion_airbnb_pct, 1) : NaN;
    r.dias_publicacion_ambientes = P.dias_publicacion[claveAmbientes(prop.ambientes)] ?? NaN;

    const venta = prop.venta_usd;
    if (vacio(venta)) return r;

    // KPIs 1 a 4
    const alq = r.alquiler_est_usd_mes;
    r.venta_usd = venta;
    r.venta_m2_usd = redondear(venta / prop.sup_total_m2, 2);
    const ablMes = ablArsMes(prop, P);
    r.abl_ars_mes = redondear(ablMes, 0);
    r.abl_pct = redondear((ablMes / (alq * tc)) * 100, 2);
    r.gastos_pct = redondear(gsa + r.abl_pct, 2);
    r.rent_bruta_pct = redondear((alq * 12) / venta * 100, 2);
    r.rent_neta_pct = redondear(r.rent_bruta_pct * (1 - vac / 100) * (1 - r.gastos_pct / 100), 2);
    r.rent_bruta_min = redondear((r.alquiler_p10_usd_mes * 12) / venta * 100, 2);
    r.rent_bruta_max = redondear((r.alquiler_p90_usd_mes * 12) / venta * 100, 2);
    r.meses_repago = redondear(venta / alq, 0);

    // Costos de entrada, refaccion y TIR a 5 anios
    r.costos_entrada_pct = costosEntradaPct(venta, P, "base");
    r.costos_entrada_alto_pct = costosEntradaPct(venta, P, "alto");
    r.refaccion_usd = refaccionUsd(prop, P, "base");
    r.refaccion_integral_usd = refaccionUsd(prop, P, "alto");
    const alqPost = vacio(r.alquiler_post_refaccion_usd_mes) ? alq : r.alquiler_post_refaccion_usd_mes;
    const netaPost = redondear(neta(alqPost, venta, r.abl_ars_mes, vac, gsa, tc), 2);
    const inicial = r.costos_entrada_pct + (r.refaccion_usd / venta) * 100;
    r.tir_5a_pct = redondear(tir(netaPost, inicial, Sp.horizonte_anios), 2);

    // Decision
    r.neta_min_pct = redondear(neta(r.alquiler_p10_usd_mes, venta, r.abl_ars_mes, vac, gsa, tc), 2);
    r.neta_max_pct = redondear(neta(r.alquiler_p90_usd_mes, venta, r.abl_ars_mes, vac, gsa, tc), 2);
    const sube = vacio(r.alquiler_post_refaccion_usd_mes) ? 1 : r.alquiler_post_refaccion_usd_mes / alq;
    const nMin = neta(r.alquiler_p10_usd_mes * sube, venta, r.abl_ars_mes, vac, gsa, tc);
    r.tir_5a_min_pct = redondear(tir(nMin, inicial, Sp.horizonte_anios), 2);
    r.en_presupuesto = venta >= Sp.presupuesto_usd[0] && venta <= Sp.presupuesto_usd[1];
    r.universo_decision = r.estimacion_confiable && r.en_presupuesto && r.en_soporte_modelo;
    const umbral = Sp.retorno_minimo_pct[1] + Sp.margen_liquidez_pct;
    r.p1_comprar = r.universo_decision && r.neta_min_pct > umbral;
    r.p1_comprar_con_entrada = r.universo_decision && r.tir_5a_min_pct > umbral;
    r.p2_la_superan = cuantosMayores(P.mercado.universo_neta_min_pct, r.neta_max_pct);
    r.p2_supera_a = cuantosMenores(P.mercado.universo_neta_max_pct, r.neta_min_pct);
    const m2c = P.m2_venta_celda[`${prop.barrio}|${r.superficie_rango}`];
    r.m2_relativo_celda = m2c === undefined ? NaN : redondear(r.venta_m2_usd / m2c, 2);
    return r;
  }

  return { simular, redondear, tir };
})();
