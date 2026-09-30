# Curaduría, ingeniería de variables y EDA — mercado inmobiliario de CABA

**TP Integrador · 82.04 Analítica Descriptiva (ITBA) · Grupo 2 · 2da pre-entrega**

Segunda etapa del análisis de rentabilidad inmobiliaria para un pequeño inversor
particular. La 1ra entrega construyó el dataset por scraping y definió el cliente,
los KPIs y las hipótesis. Esta entrega **convierte esos datos en una matriz confiable**,
extrae valor del texto libre, materializa los KPIs como columnas y declara, con fuente
y fecha, cada supuesto del que dependen.

> La 1ra entrega está en [`../Entrega 1/`](../Entrega%201/) y no se modifica: esta carpeta
> parte de su `dataset_maestro.csv` y es autónoma.

---

## Reproducir

```bash
py -m pip install -r requirements.txt

py test_variables.py                 # tests del motor RegEx, sin red
py test_eda.py                       # tests de la estadística de eda.py, sin datos
py limpieza.py --tc 1500             # crudo -> dataset limpio + auditoría
py variables.py                      # RegEx sobre el texto -> 35 dummies
py kpis.py                           # modelo de alquiler -> los 4 KPIs
py fuentes_externas.py               # IDECBA, Colegio, Airbnb y Censo -> data/external/
py temporal.py                       # alquiler tradicional contra temporal
py sesgo.py                          # sesgo de la cartera de RE/MAX
py reporte.py                        # informe/INFORME_HALLAZGOS.md, cifras en vivo
py test_supuestos.py                 # coherencia de supuestos.py con el pipeline
py test_fuentes.py                   # joins con fuentes externas, sin red
py supuestos.py                      # imprime los supuestos con su derivación
```

Los tres primeros scripts reconstruyen `data/processed/` a partir de
`data/raw/dataset_maestro.csv`, que es la fuente y se versiona. `fuentes_externas.py`
baja los crudos externos a `data/external/raw/` (no versionado) solo si faltan; las
tablas agregadas de `data/external/` sí se versionan, con su fecha de descarga.

Después, los notebooks en orden:

```bash
cd notebooks
py -m nbconvert --to notebook --execute --inplace 01_limpieza_y_calidad.ipynb
py -m nbconvert --to notebook --execute --inplace 02_ingenieria_variables.ipynb
py -m nbconvert --to notebook --execute --inplace 03_eda.ipynb
```

---

## Pipeline

```
data/raw/dataset_maestro.csv          14.867 avisos, 55 columnas
   │
   │  limpieza.py       9 pasos, nada se borra en silencio
   ├─→ dataset_limpio.csv             12.097 filas, 66 columnas
   ├─→ dataset_excluidos.csv          2.770 filas con motivo_exclusion
   ├─→ auditoria_calidad.csv          una fila por columna: nulos y decisión
   │
   │  variables.py      minería de texto con RegEx
   ├─→ dataset_variables.csv          + 35 dummies + 5 vars de estructura
   ├─→ reporte_regex.txt              prevalencias y auditoría contra el método viejo
   │
   │  kpis.py           Ridge sobre log(alquiler) + materialización
   │     ↑ supuestos.py  vacancia y gastos (valores por defecto)
   ├─→ dataset_analitico.csv          LA matriz final, con los 4 KPIs
   ├─→ ranking_barrios.csv
   ├─→ sensibilidad_supuestos.csv     KPI 2 y ranking en la grilla vacancia × gastos
   └─→ reporte_kpis.txt

fuentes_externas.py  →  data/external/ (IDECBA precios y tiempo de publicación, Colegio,
                                         Inside Airbnb, Censo 2022)
   │
   ├─ temporal.py  (+ dataset_analitico)  →  temporal_vs_tradicional.csv
   └─ sesgo.py     (+ dataset_analitico)  →  sesgo_precio_barrio.csv,
                                            sesgo_representacion_comuna.csv

reporte.py  (todo lo anterior)  →  informe/INFORME_HALLAZGOS.md
```

---

## Qué hay en cada archivo

| Archivo | Qué hace |
|---|---|
| `limpieza.py` | Los 8 pasos de la 1ra entrega **más** detección de outliers comparada (4 criterios) y auditoría de nulos con imputación trazable |
| `variables.py` | Motor RegEx: 35 dummies con límites de palabra y manejo de negación, 5 variables de estructura extraídas del texto, y la auditoría contra el método de subcadena anterior |
| `supuestos.py` | **Todos los supuestos y umbrales del análisis**, cada uno con fuente y fecha: presupuesto del inversor, vacancia, los cuatro componentes de los gastos, banda de retorno mínimo, mínimos de cobertura y cortes gráficos. Los valores derivados (vacancia, total de gastos, banda) se calculan a partir de sus componentes |
| `modelo_alquiler.py` | Sin cambios respecto de la 1ra entrega: el modelo se revisa en la 3ra. Lo que cambió es de dónde vienen sus supuestos: la vacancia y los gastos que recibe ya no son sus constantes internas sino los de `supuestos.py`, que `kpis.py` le pasa como argumentos |
| `kpis.py` | Orquesta el modelo y materializa KPI 1-4 sobre las 12.097 filas |
| `eda.py` | Estadística robusta, comparación dentro de estratos (`efecto_estratificado`) y estilo gráfico compartido por los notebooks |
| `test_variables.py` | 73 tests del motor RegEx, sin red |
| `test_eda.py` | Tests de `eda.py`, incluido un caso sintético donde la comparación ingenua inventa un efecto que la comparación dentro del estrato elimina |
| `fuentes_externas.py` | Lee cuatro fuentes externas (IDECBA con precios y tiempo de publicación, Colegio de Escribanos, Inside Airbnb y Censo 2022), normaliza los barrios a los 48 oficiales y deja tablas agregadas y fechadas en `data/external/`. Catálogo en [`informe/FUENTES_EXTERNAS.md`](informe/FUENTES_EXTERNAS.md) |
| `temporal.py` | Alquiler tradicional contra temporal, neta contra neta, por barrio y dormitorios, con la ocupación de equilibrio (P3) |
| `sesgo.py` | Sesgo de la cartera de RE/MAX: precio contra IDECBA por barrio y representación contra el Censo 2022 por comuna |
| `reporte.py` | Escribe [`informe/INFORME_HALLAZGOS.md`](informe/INFORME_HALLAZGOS.md): los hallazgos que cambian la decisión del inversor, con cada cifra calculada al generarlo |
| `test_supuestos.py` | Verifica que los gastos sumen el total que recibe el modelo, que cada derivado salga de sus componentes y que el dataset y la comparación del temporal se hayan generado con los supuestos vigentes. Incluye casos negativos |
| `test_fuentes.py` | Verifica que ningún join con las fuentes externas cambie la cantidad de filas, con negativos que provocan la trampa a propósito, y la normalización de barrios |
| `notebooks/01_limpieza_y_calidad.ipynb` | Auditoría de calidad: nulos por naturaleza, outliers, exclusiones |
| `notebooks/02_ingenieria_variables.ipynb` | Motor RegEx, variables de estructura y KPIs |
| `notebooks/03_eda.ipynb` | EDA con estadística robusta y once visualizaciones (05 a 15), incluido un mapa de dispersión espacial. Toda afirmación bivariada se verifica dentro del estrato barrio × superficie; evalúa H1, H3 y H4 por tamaño del efecto |

---

## Los cuatro KPIs, materializados

| KPI | Columna | Definición |
|---|---|---|
| 1 — Rentabilidad bruta anual | `rent_bruta_pct` | (alquiler estimado × 12) / precio de venta × 100 |
| 2 — Rentabilidad neta anual | `rent_neta_pct` | bruta × (1 − vacancia) × (1 − gastos) |
| 3 — Meses de repago | `meses_repago` | precio de venta / alquiler estimado |
| 4 — Banda de incertidumbre | `rent_bruta_min` / `rent_bruta_max` | bruta × (1 ± error del segmento de superficie) |

Los KPIs quedan vacíos en las 1.348 filas publicadas en alquiler. Eso es correcto:
una propiedad en alquiler no tiene precio de venta, así que su rentabilidad no
está definida. No se imputa.

**El KPI 3 es un recupero simple.** Cuenta cuántos meses de alquiler hacen falta para
igualar el precio de compra. Ignora el valor residual del inmueble, su apreciación o
depreciación y la inflación en dólares. No es un período de repago descontado ni una
TIR.

### Supuestos del KPI 2

Vacancia y gastos se definen, miden y justifican por separado en `supuestos.py`.
Resumen (`py supuestos.py` imprime la versión vigente):

| Supuesto | Valor | Cómo se obtiene | Fuente |
|---|---|---|---|
| Vacancia | 5,88% | 1,5 meses vacíos por rotación ÷ ciclo de 24 + 1,5 meses | Cámara Inmobiliaria Argentina, 30 a 60 días para re-alquilar (Ámbito, 01-10-2025); plazo supletorio de 2 años, CCyC art. 1198 según DNU 70/2023 |
| Administración | 4,15% | Tope de comisión de locación sobre el valor total del contrato, a cargo del propietario | Ley 5859 CABA (Garantear, 14-08-2026) |
| ABL | 3,80% | ARS 32.622/mes sobre un alquiler de USD 573 × 1.500 | Ley Tarifaria 2026 (Roomix, 05-05-2026); alquiler mediano de 2 ambientes del dataset |
| Expensas extraordinarias | 1,92% | 9% de las expensas van a obras extraordinarias × expensas = 21,3% del alquiler | ConsorcioAbierto (Ámbito, 14-07-2026); mediana de `expensas_sobre_alquiler` |
| Mantenimiento | 4,17% | Medio mes de alquiler por año | **Estimación propia**: no hay una serie publicada para CABA |
| **Gastos, total** | **14,04%** | Suma de los cuatro componentes | — |

Las expensas **ordinarias** no se descuentan: en CABA las paga el inquilino
(CCyC art. 1209). El ABL sí, porque ante la AGIP el contribuyente es el propietario,
aunque algunos contratos se lo trasladen al inquilino.

---

## Contexto argentino: por qué cambia la lectura de los datos

Muchos resultados de este trabajo no se explican por el inmueble sino por el mercado
en el que se publica. Esta sección conecta cinco rasgos de ese mercado con lo que
significan, en concreto, las columnas del dataset.

### 1. Inflación y dolarización

**El dato.** Gaggero y Nemiña (2018) señalan que "hace menos de 40 años, las
transacciones inmobiliarias en la Argentina se realizaban en moneda nacional, incluso
en momentos de alta inflación", y que hoy los precios "se denominan y 'miden' en
dólares y las transacciones se realizan en la moneda norteamericana". La inflación
sigue alta: el IPC de agosto de 2026 subió 33,5% interanual (INDEC, informe IPC
agosto 2026).

**En nuestros datos.** El 100% de las ventas del dataset está publicado en dólares y
el 81,6% de los alquileres, en pesos (columna `precio_moneda`). Cada rentabilidad
compara un **stock en dólares** (el precio) contra un **flujo en pesos** (el alquiler)
convertido a un único tipo de cambio: ARS 1.500, el `--tc` de `limpieza.py`.

**Consecuencia analítica.** `rent_bruta_pct` es una **foto a un tipo de cambio**, no
un rendimiento en dólares garantizado. Si el peso se deprecia más rápido de lo que se
ajusta el contrato, el alquiler medido en dólares cae y la rentabilidad real queda por
debajo de la calculada; si se aprecia, al revés. Por eso los KPIs no se leen como
retornos futuros, sino como una comparación válida **entre propiedades a la misma
fecha**, que es para lo que se construyeron.

### 2. Crédito hipotecario escaso y cíclico

**El dato.** El crédito hipotecario representa el 1% del PBI en Argentina, contra 28%
en Chile, 11% en Brasil y 10% en México (Deloitte Econosignal, citado por Infobae,
22-05-2026). Además es cíclico: el boom de los créditos UVA superó los 70.000
préstamos en 2017, y las devaluaciones y la aceleración inflacionaria de la segunda
mitad de 2018 lo frenaron en seco. Hubo un relanzamiento en 2024-2025 y en los
primeros siete meses de 2026 el volumen cayó 47% interanual (BAE Negocios,
26-08-2026, con datos de Fundación Tejido Urbano).

**En nuestros datos.** Solo el 24,1% de los avisos de venta declara ser apto crédito
(dummy `apto_credito`, extraída por RegEx) y el 9,4% ofrece financiación
(`financiacion`).

**Consecuencia analítica.** Para el cliente de este trabajo el crédito no es una
palanca: compra con ahorros propios. Por eso la rentabilidad se calcula **sobre el
precio total y sin apalancamiento**, y la vara de comparación no es la tasa de una
hipoteca sino lo que ese mismo dinero rendiría en otro activo en dólares (la banda de
retorno mínimo de `supuestos.py`). También limita la reventa: si tres de cada cuatro
avisos no declaran ser aptos para crédito, lo más probable es que el comprador futuro
de esa unidad también tenga que pagar de contado, y eso achica el mercado de salida.

### 3. Predominio de operaciones al contado

**El dato.** En agosto de 2026 se firmaron en CABA 6.055 escrituras de compraventa, y
1.059 de ellas con hipoteca: 17,5% del total. Es decir que el 82,5% se hizo sin
crédito hipotecario. En el acumulado de enero a agosto, las escrituras con hipoteca
cayeron casi 34% interanual (Colegio de Escribanos de la Ciudad de Buenos Aires,
citado por Infobae, 23-09-2026).

**Consecuencia analítica.** Un mercado de contado es un mercado **poco líquido**: la
demanda está limitada a quienes ya tienen el capital en dólares. Para un inversor que
compra una sola unidad, eso vuelve la **liquidez** una restricción de primer orden y no
un detalle: si necesita el dinero antes de tiempo, venderla puede llevar meses. La serie
mensual del Colegio, integrada en `data/external/`, da el volumen del mercado de salida
(69.490 compraventas en 2025, el 19,1% con hipoteca), pero no el tiempo que tarda en
venderse una unidad. Eso lo da el tiempo medio de publicación de departamentos en venta
de IDECBA, también integrado: en el 2do trimestre de 2026 fue de 298 días, casi diez
meses, y llegó a 425 en el 1er trimestre de 2024. Es un promedio de la Ciudad y es
tiempo publicado, no tiempo de venta: la liquidez de **cada** propiedad sigue siendo
información faltante, porque el dataset es un corte único.

### 4. Precio publicado contra precio de cierre

**El dato.** En agosto de 2026 la diferencia entre el precio de publicación y el
efectivamente pactado en CABA fue de −4,79%, y el precio de cierre promedio fue de
USD 2.150 por m² (Índice M² Real de RE/MAX Argentina, UCEMA y Reporte Inmobiliario,
publicado el 18-09-2026). El monto promedio escriturado en agosto fue de
USD 119.270, al tipo de cambio oficial promedio (Colegio de Escribanos, citado por
Infobae, 23-09-2026).

**En nuestros datos.** Todos los precios del dataset son **de publicación**: tanto
`venta_usd` como `alquiler_usd_mes`. El precio medio de venta del dataset es
USD 167.021, un 40% más que el monto promedio escriturado, y la mediana es
USD 130.000.

**Consecuencia analítica.** Hay dos efectos, y van en sentidos opuestos:

- **Del lado de la venta, el KPI es un piso.** El precio está en el denominador. Si el
  cierre real es 4,79% más bajo, la rentabilidad bruta mediana pasa de 7,01% a 7,36%.
- **Del lado del alquiler, el KPI es un techo.** El modelo se entrena con alquileres
  pedidos, no pactados. Si también se negocian a la baja, el numerador está inflado.
  No encontramos una serie publicada de esa brecha, así que el efecto neto no se
  puede firmar.

La brecha de negociación explica solo 5 de los 40 puntos que separan el precio medio
del dataset del monto medio escriturado. El resto es composición, y no se puede
atribuir sin más datos: el Colegio registra todas las compraventas de la Ciudad y
nuestro dataset, solo la cartera residencial de RE/MAX. Además, el m² medio publicado
en el dataset (USD 2.050) queda *por debajo* del m² de cierre del índice (USD 2.150), y
un precio publicado no debería estar por debajo del de cierre del mismo mercado.

`sesgo.py` lo confirma y lo cuantifica contra el precio publicado de IDECBA en la misma
celda de barrio × ambientes × estado: la cartera de RE/MAX publica **más barato** en 127
de 135 celdas, entre −5% y −9% en usados y entre −14% y −16% a estrenar en el total de
la Ciudad. Del lado de la venta, eso empuja la rentabilidad de la cartera por encima de
la del mercado publicado. El detalle y la representación por comuna están en
[`informe/FUENTES_EXTERNAS.md`](informe/FUENTES_EXTERNAS.md).

### 5. El ciclo regulatorio del alquiler

**El dato.** La Ley 27.551 (2020) fijó un plazo mínimo de 3 años para los contratos
de vivienda. El
DNU 70/2023, del 20-12-2023, la derogó y dejó a la libre voluntad de las partes el
plazo, la moneda y el ajuste; si el contrato no fija plazo, rigen 2 años (CCyC
art. 1198 reformado). Después del DNU, la oferta de alquileres en CABA creció
174,95% hasta octubre de 2024 (Observatorio Estadístico del Sector Inmobiliario,
citado por TV Pública, 30-10-2024).

**En nuestros datos.** El scraping es del 16 y 17 de agosto de 2026 (`fecha_scraping`),
en pleno régimen desregulado. Hay 7,97 ventas por cada alquiler (10.749 contra
1.348), y el 18,4% de los alquileres se publica en dólares, algo que la libertad de
moneda habilita.

**Consecuencia analítica.** Los alquileres observados son los de un mercado con oferta
abundante y contratos más cortos. Eso tiene tres efectos sobre la lectura:

- El **modelo de alquiler aprende precios de este régimen**. Un cambio regulatorio
  mueve la relación alquiler/precio y, con ella, todos los KPIs.
- **Contratos más cortos implican más rotación**, y más rotación implica más vacancia.
  Por eso la vacancia de `supuestos.py` se deriva de la duración del contrato y no se
  fija como un número suelto.
- La **proporción de 8 ventas por alquiler es un rasgo del régimen** y de la cartera de
  RE/MAX, no del stock de viviendas. Es la razón por la que el alquiler de las
  propiedades en venta se estima con un modelo y no se observa.

---

## Preguntas clave según los cuatro niveles de análisis

### Dos sentidos de "predictivo"

El trabajo usa la palabra "predictivo" en un solo sentido, y conviene separarlo del
otro:

- **Predicción transversal** (lo que hace este trabajo): estimar cuánto se alquilaría
  **hoy** una propiedad publicada solo en venta, a partir de los alquileres de
  propiedades comparables observados **en la misma fecha**. Es lo que produce
  `alquiler_est_usd_mes`. Es válida porque el modelo se evalúa fuera de muestra
  (R² = 0,848 en log, con error por tramo de superficie en `error_estimacion`).
- **Pronóstico temporal** (lo que este trabajo **no** hace): anticipar cómo van a
  evolucionar los precios o los alquileres. Requiere una serie de tiempo, y el dataset
  es un corte único de agosto de 2026. Ninguna columna del dataset es un pronóstico.

### Descriptivo — ¿qué hay en el mercado?

| Pregunta | Se responde con |
|---|---|
| ¿Cuál es el precio por m² mediano de cada barrio? | `venta_m2_usd` agrupada por `barrio` |
| ¿Cómo se distribuye la oferta entre tipologías y superficies? | `tipo_familia`, `superficie_rango`, `operacion` |
| ¿Qué proporción de la oferta tiene cochera, balcón o amenities? | `cochera_txt`, `balcon`, `terraza`, `amenities`, `n_amenities` |
| ¿Cuál es la antigüedad mediana del stock por barrio? | `antiguedad_anios` por `barrio`, excluyendo o marcando `antiguedad_anios_imputada == 1` |
| ¿Qué parte de la oferta entra en el presupuesto del cliente? | `venta_usd` contra `supuestos.PRESUPUESTO_USD` |

### Diagnóstico — ¿por qué?

| Pregunta | Se responde con |
|---|---|
| ¿Qué características explican el precio de alquiler? | `alquiler_usd_mes` (variable objetivo) contra las predictoras del modelo; coeficientes en `reporte_kpis.txt` |
| ¿Por qué los barrios más caros rinden menos como renta? (H1) | `venta_m2_usd` contra `rent_bruta_pct`, medianas por `barrio` (Spearman) |
| ¿El repunte de rentabilidad de las unidades grandes es de tamaño o de composición? | `rent_bruta_pct` por `superficie_rango` y `tipo_familia` |
| ¿Los amenities se pagan en el precio pero no en el alquiler? | `rent_bruta_pct` por `amenities` |

### Predictivo (transversal) — ¿cuánto rendiría hoy?

| Pregunta | Se responde con |
|---|---|
| Dado un inmueble en venta, ¿cuánto se alquilaría hoy? | `alquiler_est_usd_mes`, con `estimacion_confiable` y `n_alq_barrio` |
| ¿Qué rentabilidad implica hoy cada propiedad publicada? | `rent_bruta_pct`, `rent_neta_pct`, `meses_repago` |
| ¿Cuánto de esa rentabilidad es ruido de estimación? | `error_estimacion`, `rent_bruta_min`, `rent_bruta_max` |

### Prescriptivo — ¿qué conviene hacer?

La pregunta rectora, en los términos de la consigna:

> **Dado un presupuesto de USD 80.000 a 200.000 y un horizonte de 5 años,
> ¿qué propiedad ofrece la mejor combinación de retorno esperado, liquidez y riesgo, y
> supera esa combinación la de no comprar y quedarse en renta fija en dólares, sujeto
> a las restricciones definidas?**

El cliente compra **una** unidad, así que la pregunta es por una propiedad y no por
una cartera. Se descompone en tres decisiones, cada una con sus cinco componentes. La
función de decisión que las resuelve es alcance de la 3ra entrega: acá quedan
formuladas.

Las restricciones comunes a las tres, con los valores de `supuestos.py`:

| Restricción | Valor | Constante |
|---|---|---|
| Presupuesto | USD 80.000 a 200.000 | `PRESUPUESTO_USD` |
| Retorno mínimo (costo de oportunidad) | banda de 7,10% a 7,60% anual en USD: ON corporativas de YPF 2031 (YMCXO) y Pampa 2037 (MGCRO), Ámbito, julio de 2026. Es lo que rinde el mismo capital en dólares y con riesgo argentino, sin la iliquidez del inmueble | `RETORNO_MINIMO_BANDA` |
| Referencia soberana | 11,65%: Treasury a 10 años (5,24%) + riesgo país (641 pb) al 28-09-2026. No es la vara del inversor: sirve para leer cuánto de la banda es prima por riesgo argentino | `RETORNO_SOBERANO_REF_PCT` |
| Riesgo de estimación | la banda de cada propiedad (KPI 4) | columnas `rent_bruta_min` / `rent_bruta_max` |
| Riesgo de concentración | una sola unidad: no hay diversificación | perfil del cliente |
| Liquidez | mercado de contado; un departamento pasa en promedio unos diez meses publicado (IDECBA, 2do trimestre de 2026); sin medida por propiedad | `data/external/estadistica_ciudad_tiempo_publicacion.csv` |
| Horizonte | 5 años: el plazo de la ON que fija el piso de la banda (YMCXO vence en 2031), porque un inmueble y un bono solo se comparan a plazo equivalente. Cubre dos contratos completos de 24 meses | `HORIZONTE_ANIOS` |

La banda de retorno mínimo es una **restricción del análisis**, no una recomendación
de inversión: marca la vara contra la que se lee la rentabilidad neta.

#### P1 — ¿Comprar un inmueble para alquilar, o no comprar?

| Componente | Formulación |
|---|---|
| **Decisión** | Destinar el capital a una unidad para renta, o mantenerlo en renta fija en dólares |
| **Alternativas** | (a) comprar y alquilar en forma tradicional; (b) comprar y alquilar en forma temporal (ver P3); (c) no comprar: ON corporativas o bonos soberanos en USD |
| **Información necesaria** | `rent_neta_pct` y su banda para las propiedades dentro del presupuesto; TIR vigente de las alternativas de renta fija; costo de entrada y salida del inmueble (escritura, comisiones), que el dataset no tiene |
| **Restricciones** | Presupuesto, retorno mínimo, liquidez y horizonte, según la tabla de arriba |
| **Criterio para recomendar** | Recomendar el inmueble solo si su rentabilidad neta, calculada sobre el **extremo inferior** de su banda (`rent_bruta_min` con los mismos descuentos que el KPI 2), supera el techo de la banda de retorno mínimo con un margen que pague su menor liquidez. Hoy la mediana de `rent_neta_pct` en la base confiable es 5,67%, por debajo incluso del piso de 7,10%. Por eso la pregunta no es retórica: para la propiedad mediana, la alternativa (c) domina en retorno corriente. Tampoco la resuelve el horizonte: con un repago mediano de 171 meses, en 5 años el alquiler devuelve el 35% del precio, y el resto depende de vender la unidad. El valor de reventa, la apreciación y la liquidez de salida deciden el resultado y requieren una serie temporal que este dataset no tiene |

#### P2 — Si se compra, ¿qué propiedad?

| Componente | Formulación |
|---|---|
| **Decisión** | Qué unidad comprar dentro del presupuesto |
| **Alternativas** | Las propiedades en venta con `venta_usd` dentro de `PRESUPUESTO_USD` y `estimacion_confiable == 1`, que difieren en `barrio`, `superficie_rango`, `tipo_familia` y `amenities` |
| **Información necesaria** | `rent_neta_pct`, `rent_bruta_min`, `rent_bruta_max`, `error_estimacion`; oferta por barrio como indicio de profundidad de mercado; `apto_credito` como indicio de liquidez de salida |
| **Restricciones** | Presupuesto; solo barrios con cobertura suficiente (`MIN_VENTAS_BARRIO`); riesgo de estimación acotado por la banda |
| **Criterio para recomendar** | A sobre B solo si sus bandas **no se superponen** (`rent_bruta_min` de A > `rent_bruta_max` de B). Si se superponen, la diferencia de rentabilidad no se distingue del error de estimación, y la elección debe decidirse por liquidez o riesgo, no por el KPI |

#### P3 — ¿Alquiler tradicional o temporal?

| Componente | Formulación |
|---|---|
| **Decisión** | Cómo explotar la unidad comprada |
| **Alternativas** | (a) tradicional: contrato de 24 meses; expensas ordinarias y servicios a cargo del inquilino; (b) temporal: por noche, mediante plataforma |
| **Información necesaria** | Para (a), `rent_neta_pct`. Para (b): tarifa por noche y ocupación por barrio, y sus costos propios (comisión de plataforma, limpieza, gestión, amoblamiento amortizado, y expensas y servicios que en el temporal paga el dueño). **Ninguno está en el dataset de RE/MAX**: la tarifa y la ocupación salen de Inside Airbnb (`data/external/airbnb_barrio_dormitorios.csv`) y los costos, de `supuestos.py`. La ocupación es una estimación de Inside Airbnb, no un dato observado |
| **Restricciones** | Retorno mínimo; riesgo de ocupación, mayor en el temporal; horizonte, que tiene que alcanzar para amortizar el amoblamiento |
| **Criterio para recomendar** | Comparar **neta contra neta**, por barrio y dormitorios. Comparar el ingreso bruto del temporal contra la neta del tradicional sesga el resultado a favor del temporal de entrada. Como la ocupación del temporal no se observa, el criterio es la **ocupación de equilibrio**: con cuánta ocupación el temporal empata al tradicional. Recomendar el temporal solo si la ocupación que el inversor puede sostener supera ese umbral con margen |

**Primer resultado** (`py temporal.py`, datos de Inside Airbnb del 29-06-2026 y supuestos de `supuestos.py`): en las 47 combinaciones de barrio y dormitorios con datos suficientes de los dos lados, la ocupación de equilibrio mediana es 65,3% con gestión tercerizada y 51,5% autogestionada. La ocupación que estima Inside Airbnb para esas celdas tiene una mediana de 18,6%, y con ella el temporal no le gana al tradicional en ninguna. Aun con el 53% que informa la prensa (La Nación, 29-05-2025), gana en 3 de 47. El resultado resiste los dos supuestos más débiles: con servicios a la mitad y sin amoblamiento, el equilibrio mediano sigue en 54,4%. El ingreso por noche es alto, pero en el temporal las expensas y los servicios los paga el dueño, y eso, sumado a la plataforma y la gestión, se come la diferencia. La ocupación de Inside Airbnb es una estimación a partir de reseñas, no un dato observado.

---

## Diferencias con la 1ra entrega

### H1: Spearman de −0,923 a −0,903

La 1ra entrega informó una correlación de Spearman de **−0,923** entre el precio del
m² y la rentabilidad bruta mediana por barrio. Esta entrega da **−0,903**. La hipótesis
sigue respaldada con holgura. La diferencia tiene una causa identificada y medida.

**Qué no cambió.** Los dos rankings tienen los mismos 29 barrios, con la misma
cantidad de ventas cada uno (9.184 en total) y exactamente el mismo precio mediano
del m². Si se combina el precio de esta entrega con la rentabilidad de la 1ra, el
Spearman vuelve a −0,9230. Toda la diferencia está del lado del **alquiler estimado**,
que se movió en promedio un 1,3% por barrio (hasta 5,6% en Chacarita y 3,9% en Parque
Chacabuco).

**Por qué cambió el alquiler estimado.** El modelo de alquiler es el mismo, pero 14 de
sus predictoras son dummies extraídas del texto, y esta entrega reemplazó la búsqueda
por subcadena por el motor RegEx de `variables.py`. Sobre los mismos avisos, `amenities`
cambia en el 19,6% de las filas, `balcon` en el 12,5% (casi todo por mudanza a
`terraza`) y `amoblado` en el 10,6%. Para aislar el efecto se reentrenó el modelo sobre
el dataset de esta entrega, cambiando una cosa por vez:

| Variante | Spearman |
|---|---|
| Dataset de esta entrega, tal cual | −0,9026 |
| Mismo dataset, con las 14 dummies de la 1ra entrega | −0,9240 |
| Mismo dataset, con las predictoras numéricas de la 1ra entrega | −0,9030 |
| Mismo dataset, con dummies y numéricas de la 1ra entrega | −0,9230 |

Las dummies explican la diferencia completa. La antigüedad, que difiere en el 1,1% de
las filas por la imputación nueva de `limpieza.py`, la compensa en una milésima.

**Cómo leerlo.** El número de la 1ra entrega no estaba mal calculado: estaba calculado
con variables de texto más ruidosas. El de esta entrega es el que corresponde a las
dummies auditadas, y es el que se reporta. Que una de cada cinco filas cambie de
valor en `amenities` y el Spearman se mueva solo 0,02 indica que H1 es robusta a la
calidad de esas variables.

*Método: comparación de `ranking_barrios.csv` de ambas entregas y reentrenamiento del
modelo con vacancia 8% y gastos 12% (los supuestos de la 1ra entrega), ejecutado el
28-09-2026 contra los resultados procesados de la 1ra entrega, en solo lectura. El ranking
por barrio de la 1ra entrega está versionado en `data/reference/`.*

---

## Convenciones

- Código y comentarios en español, sin tildes en los comentarios (encoding Windows).
  En Markdown sí van tildes.
- Los comentarios explican **por qué**, no qué.
- No usar `except: pass`. Los errores se cuentan y se reportan.
- Los CSV se guardan con `utf-8-sig`.
- Cada gráfico va con la pregunta que responde y su lectura.
- Ningún hallazgo numérico se escribe a mano en los notebooks: se calcula en vivo.
  Las cifras de este README salen de `reporte_kpis.txt` y del dataset analítico, y
  se actualizan cuando se reejecuta el pipeline.
- Los supuestos y umbrales viven en `supuestos.py`, con fuente y fecha. Ningún número
  de ese tipo se escribe suelto en un script o notebook.

---

## Fuentes del contexto

Consultadas el 28-09-2026, salvo indicación.

- Gaggero, A. y Nemiña, P. (2018). "El origen de la dolarización inmobiliaria en la
  Argentina". *Sociales en debate*, UBA.
  <https://publicaciones.sociales.uba.ar/index.php/socialesendebate/article/view/3323>
- INDEC. Índice de precios al consumidor, agosto de 2026.
  <https://www.indec.gob.ar/uploads/informesdeprensa/ipc_09_26A1BE2DC4CD.pdf>
- Infobae (22-05-2026). "El crédito hipotecario de la Argentina es el más bajo de la
  región", con datos de Deloitte Econosignal.
  <https://www.infobae.com/economia/2026/05/22/el-credito-hipotecario-de-la-argentina-es-el-mas-bajo-de-la-region-cual-es-el-nivel-en-otros-paises/>
- BAE Negocios (26-08-2026). "Hipotecas UVA: del boom de 2017 al desplome y la
  búsqueda de recuperación".
  <https://www.baenegocios.com/negocios/hipotecas-uva-del-boom-de-2017-al-desplome-y-la-busqueda-de-recuperacion/>
- Infobae (23-09-2026). Escrituras de agosto de 2026 en CABA, con datos del Colegio de
  Escribanos de la Ciudad de Buenos Aires.
  <https://www.infobae.com/economia/2026/09/23/con-bajo-impulso-de-las-hipotecas-las-escrituras-de-compraventa-en-caba-cayeron-casi-5-interanual-en-agosto/>
- Reporte Inmobiliario (18-09-2026). "Precio real de cierre por m² – agosto 2026",
  Índice M² Real de RE/MAX Argentina, UCEMA y Reporte Inmobiliario.
  <https://www.remax-buro2.com.ar/sector-inmobiliario/precio-real-de-cierre-por-m%C2%B2-agosto-2026-noticias-sobre-residencial-en-reporte-inmobiliario/>
- TV Pública (30-10-2024). "CABA: la oferta de alquileres aumentó 180% tras el DNU",
  con datos del Observatorio Estadístico del Sector Inmobiliario.
  <https://www.tvpublica.com.ar/post/caba-la-oferta-de-alquileres-aumento-180-tras-el-dnu-desregulador-de-milei>
- Pozo Gowland Abogados. "La regulación de los contratos de locación luego del DNU
  N° 70/2023".
  <https://pg-abogados.com.ar/es/la-regulacion-de-los-contratos-de-locacion-luego-del-dnu-n-70-2023/>

Las fuentes de cada supuesto numérico están en el comentario de su constante, en
`supuestos.py`.
