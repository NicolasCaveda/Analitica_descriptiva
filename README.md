# Inteligencia de mercado inmobiliario — CABA

**TP Integrador · 82.04 Analítica Descriptiva (ITBA) · Grupo 2 · 2026**

Iael Berezovsky · Nicolás Caveda · Máximo Lladhon · Ezequiel Naymark

Análisis de rentabilidad inmobiliaria en la Ciudad Autónoma de Buenos Aires para un
**pequeño inversor particular** que evalúa comprar una propiedad para alquilarla.

---

## Entregas

| Carpeta | Etapa | Contenido |
|---|---|---|
| [`Entrega 1/`](Entrega%201/) | Estrategia, arquitectura y recolección (Unidades 1-2) | Definición del cliente, KPIs, hipótesis, scrapers y dataset maestro |
| [`Entrega 2/`](Entrega%202/) | Curaduría, ingeniería de variables y EDA (Unidades 3-6) | Limpieza auditada, minería de texto con RegEx, KPIs materializados, fuentes externas y análisis exploratorio. Informe: [`INFORME_HALLAZGOS.md`](Entrega%202/informe/INFORME_HALLAZGOS.md) |
| [`Entrega 3/`](Entrega%203/) | Validación, análisis avanzado y decisión | Fusión espacial y accesibilidad al transporte, ABL segmentado, costos de entrada y TIR a 5 años, tests formales de H1 a H4, función de decisión prescriptiva (P1 a P3) implementada y evaluada, tablero y simulador, sobre el pipeline depurado de la 2da entrega. Informe: [`INFORME_HALLAZGOS.md`](Entrega%203/informe/INFORME_HALLAZGOS.md) |

Cada carpeta es autónoma: tiene su propio `README.md` con la documentación de esa
etapa, sus notebooks y sus datos. La única excepción es el `requirements.txt` de esta
raíz: lo usa la versión del tablero publicada en Streamlit Community Cloud.

---

## Para el inversor

- **Tablero**: <https://dashboard-descriptiva-g2.streamlit.app/>. Se abre en el
  navegador, sin instalar nada. Responde si conviene comprar, en qué barrios y qué
  propiedades mirar, sobre las 9.203 ventas relevadas. Cómo correrlo localmente, en
  [`Entrega 3/README.md`](Entrega%203/README.md#el-tablero).
- **Simulador**: [`Entrega 3/simulador/simulador.html`](Entrega%203/simulador/simulador.html).
  Se descarga y se abre con doble clic. Evalúa cualquier propiedad que el inversor tenga
  en vista, a su precio, con el mismo modelo y los mismos criterios de decisión (ver
  [El simulador](Entrega%203/README.md#el-simulador)).

---

## Licencia

Uso académico. Ver [`LICENSE`](LICENSE) para el alcance, el tratamiento de los datos
y la limitación de responsabilidad.

Los precios corresponden a valores de publicación, no de cierre, relevados en un
único momento y de una sola fuente. Nada de este trabajo constituye asesoramiento
financiero ni de inversión.
