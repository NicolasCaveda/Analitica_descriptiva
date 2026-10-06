# Catálogo de fuentes externas

**TP Integrador · 82.04 Analítica Descriptiva (ITBA) · Grupo 2 · 2da pre-entrega**

El análisis de las entregas anteriores dependía de una sola fuente: la cartera de avisos de
RE/MAX. Este catálogo documenta las fuentes que se sumaron para leerla contra el mercado
y las que quedan planificadas. Cada una se describe con los mismos campos: qué variable
aporta, cobertura geográfica, período, granularidad, cómo se une con RE/MAX, qué pregunta,
KPI o hipótesis ayuda a analizar, y sus limitaciones.

Las fuentes integradas se leen con `py src/fuentes_externas.py`, que deja tablas agregadas y
fechadas en `data/external/`. Los archivos crudos no se versionan (`data/external/raw/`
está en `.gitignore`): se vuelven a bajar con el script. El agregado versionado congela la
evidencia, porque algunas fuentes reemplazan sus archivos (Inside Airbnb, cada trimestre).
Ningún cruce es espacial: todos son por nombre de barrio, por comuna o a nivel ciudad.

| # | Fuente | Estado | Se une por | Responde a |
|---|---|---|---|---|
| 1 | Estadística Ciudad: precio publicado del m² | Integrada | barrio × ambientes × estado | Sesgo de precio de RE/MAX |
| 2 | Colegio de Escribanos: escrituras | Integrada | nivel ciudad, por mes | Precio de cierre, liquidez, crédito |
| 3 | Inside Airbnb | Integrada | barrio × dormitorios | P3: tradicional o temporal |
| 4 | Censo 2022: departamentos por comuna | Integrada | comuna | Sesgo de representación |
| 5 | Estadística Ciudad: tiempo medio de publicación | Integrada | ambientes, nivel ciudad | Liquidez (P1, P2) |
| 6 | IPC del INDEC | Planificada | nivel país, por mes | Lectura en términos reales |
| 7 | Transporte y espacios verdes (BA Data) | Planificada | coordenadas | H2 |

---

## Fuentes integradas

### 1. Estadística Ciudad (IDECBA): precio promedio de publicación del m²

| Campo | Detalle |
|---|---|
| **Variable que aporta** | Precio promedio de publicación del m², en dólares, de departamentos en venta (`usd_m2`) |
| **Cobertura geográfica** | Los 48 barrios de CABA, más el total de la Ciudad |
| **Período** | Serie trimestral desde el 4to trimestre de 2006 (1 ambiente, desde 2017) hasta el 2do trimestre de 2026. Se conservan los últimos 8 trimestres, del 3ro de 2024 al 2do de 2026 |
| **Granularidad** | Barrio × ambientes (1, 2, 3) × estado (usado, a estrenar) × trimestre. Seis cuadros, uno por combinación de ambientes y estado |
| **Cómo se une con RE/MAX** | Por `barrio`, `ambientes` y estado (`es_a_estrenar`), fijando un trimestre. Promedio contra promedio, porque IDECBA publica promedios |
| **Qué ayuda a analizar** | El **sesgo de precio de la cartera de RE/MAX**: si publica más caro o más barato que el mercado en la misma celda. Afecta directamente al KPI 1, que tiene el precio en el denominador |
| **Limitaciones** | Son precios **de publicación**, no de cierre, igual que los de RE/MAX: la comparación es publicado contra publicado. La base es Argenprop desde julio de 2015, así que es otro portal, no el mercado entero. IDECBA suprime las celdas con pocos avisos: en el último trimestre hay dato para entre 18 y 45 barrios según la combinación. Hay un trimestre de desfase con el scraping (agosto de 2026) |
| **Archivo** | `data/external/estadistica_ciudad_m2_barrio.csv` |
| **Fuente** | [IDECBA, banco de datos, mercado inmobiliario](https://www.estadisticaciudad.gob.ar/eyc/categoria-banco-datos/mercado-inmobiliario/), cuadros `MI_DVP_AX01` a `AX04`, `AX09` y `AX10` |

### 2. Colegio de Escribanos de la Ciudad de Buenos Aires: escrituras

| Campo | Detalle |
|---|---|
| **Variable que aporta** | Cantidad de escrituras de compraventa, cantidad con hipoteca, porcentaje con hipoteca y, para 2026, monto promedio en dólares |
| **Cobertura geográfica** | Toda la Ciudad, sin apertura por barrio |
| **Período** | Mensual, de enero de 2002 a diciembre de 2025 (cuadro de IDECBA) más julio y agosto de 2026 (informes mensuales del Colegio) |
| **Granularidad** | Ciudad × mes |
| **Cómo se une con RE/MAX** | No se une fila a fila. Es un **ancla agregada**: el monto promedio escriturado se compara con el precio promedio de la cartera, y el volumen mensual describe la liquidez del mercado en el que se va a revender |
| **Qué ayuda a analizar** | La diferencia entre **precio publicado y precio de cierre** (contexto, punto 4 del README), el **predominio del contado** (en 2025, 19,1% de las compraventas tuvo hipoteca) y la **liquidez** del mercado de salida (restricción de P1) |
| **Limitaciones** | Incluye todas las compraventas de la Ciudad (cualquier tipo de inmueble), no solo departamentos residenciales, así que el monto promedio no es comparable uno a uno con la cartera. Sin apertura por barrio. **El cuadro de IDECBA trae 2026 con valores inconsistentes**: julio de 2026 figura con 1.159 compraventas y el Colegio informa 6.051 (acumulado enero-julio: 6.771 contra 35.528). Hasta 2025 coinciden (agosto de 2025: 6.372 contra 6.370). Por eso se usa el cuadro solo hasta 2025, y 2026 sale de los informes del Colegio, cargados con su URL. Solo hay monto en dólares para los meses de 2026 |
| **Archivo** | `data/external/colegio_escribanos_mensual.csv` |
| **Fuente** | [IDECBA, actos notariales de compraventa e hipotecas](https://www.estadisticaciudad.gob.ar/eyc/banco-datos/actos-notariales-de-compraventa-de-inmuebles-e-hipotecas-anotados-en-el-colegio-de-escribanos-ciudad-de-buenos-aires-enero-de-2002-junio-de-2025/); Colegio de Escribanos, informes de [julio](https://www.colegio-escribanos.org.ar/2026/08/24/cantidad-de-escrituras-de-compraventa-realizadas-en-julio-2026/) y [agosto de 2026](https://www.colegio-escribanos.org.ar/2026/09/22/cantidad-de-escrituras-de-compraventa-realizadas-en-agosto-2026/) |

### 3. Inside Airbnb: Buenos Aires

| Campo | Detalle |
|---|---|
| **Variable que aporta** | Tarifa por noche (ADR), ocupación estimada, ingreso anual estimado y cantidad de avisos activos, por barrio y por dormitorios |
| **Cobertura geográfica** | CABA. 46 de los 48 barrios tienen avisos activos; Versalles no tiene ninguno |
| **Período** | Snapshot del 29-06-2026. Ocupación e ingreso de los últimos 12 meses |
| **Granularidad** | En origen, un aviso por fila (29.685). Agregado a barrio y a barrio × dormitorios (0-1, 2, 3+), solo unidades enteras con al menos una reseña en los últimos 12 meses (20.895) |
| **Cómo se une con RE/MAX** | Por `barrio` y grupo de dormitorios, contra los departamentos en venta de la cartera. Los barrios de Airbnb (`neighbourhood_cleansed`) usan los nombres oficiales y se normalizan sin pérdidas |
| **Qué ayuda a analizar** | **P3**: la alternativa de explotar la unidad por noche en vez de con contrato. Se compara neta contra neta en `temporal.py`, con los costos del temporal declarados en `supuestos.py` |
| **Limitaciones** | **La ocupación es una estimación, no un dato observado**: Inside Airbnb la infiere de las reseñas. Su mediana (21,4% en la Ciudad) queda muy por debajo del 53% que informa la prensa (La Nación, 29-05-2025). Por eso la comparación informa la **ocupación de equilibrio** y no una rentabilidad puntual. Los precios están en pesos y se convierten con el mismo tipo de cambio del pipeline (ARS 1.500). Inside Airbnb reemplaza sus archivos cada trimestre, y el snapshot usado puede dejar de estar disponible |
| **Archivos** | `data/external/airbnb_barrio.csv`, `data/external/airbnb_barrio_dormitorios.csv` |
| **Fuente** | [Inside Airbnb, get the data](https://insideairbnb.com/get-the-data/) |

### 4. Censo 2022: viviendas particulares habitadas por tipo, según comuna

| Campo | Detalle |
|---|---|
| **Variable que aporta** | Cantidad de departamentos habitados por comuna (1.025.296 en la Ciudad) y su peso sobre el total |
| **Cobertura geográfica** | Las 15 comunas de CABA |
| **Período** | Censo Nacional de Población, Hogares y Viviendas 2022 |
| **Granularidad** | Comuna. Es el nivel más fino con un universo completo publicado: IDECBA no publica oferta ni stock actual por barrio |
| **Cómo se une con RE/MAX** | Por `comuna`, contra la distribución de los departamentos de la cartera |
| **Qué ayuda a analizar** | El **sesgo de representación**: qué zonas pesan en la cartera más o menos de lo que pesan en la Ciudad |
| **Limitaciones** | Es stock censado, no oferta: una comuna puede tener mucho stock y poca rotación. El índice mide composición, no error. Es de 2022 |
| **Archivo** | `data/external/censo_departamentos_comuna.csv` |
| **Fuente** | [IDECBA, viviendas particulares habitadas por tipo de vivienda según comuna](https://www.estadisticaciudad.gob.ar/eyc/banco-datos/viviendas-particulares-habitadas-hogares-y-poblacion-censada-por-tipo-de-vivienda-segun-comuna-ciudad-de-buenos-aires-ano-2010/), sobre datos del INDEC |

### 5. Estadística Ciudad: tiempo medio de publicación de departamentos en venta

| Campo | Detalle |
|---|---|
| **Variable que aporta** | Días promedio que un departamento en venta permanece publicado |
| **Cobertura geográfica** | Toda la Ciudad |
| **Período** | Trimestral, del 4to trimestre de 2013 al 2do trimestre de 2026 |
| **Granularidad** | Ambientes × trimestre, sin apertura por barrio |
| **Cómo se une con RE/MAX** | Por `ambientes`, a nivel ciudad |
| **Qué ayuda a analizar** | La **liquidez**, que es una restricción de P1 y P2: cuánto tardaría el inversor en vender su unidad. En el 2do trimestre de 2026, el promedio fue de 298 días publicado |
| **Limitaciones** | El tiempo publicado no es tiempo de venta: un aviso puede bajarse sin venderse. Sin barrio, y sin forma de medirlo por propiedad con un scraping de un solo día |
| **Archivo** | `data/external/estadistica_ciudad_tiempo_publicacion.csv` |
| **Fuente** | [IDECBA, cuadro `MI_DVT`](https://www.estadisticaciudad.gob.ar/eyc/banco-datos/tiempo-medio-de-publicacion-dias-de-departamentos-en-venta-por-cantidad-de-ambientes-ciudad-de-buenos-aires-4to-trimestre-de-2013-2do-trimestre-de-2024/) |

---

## El sesgo de usar una sola fuente, cuantificado

`py src/sesgo.py` mide las dos dimensiones que se pueden contrastar con fuentes oficiales.
Resultados completos en `data/processed/reporte_sesgo.txt`.

**Precio.** La cartera de RE/MAX publica **más barato** que el promedio de Argenprop en
127 de las 135 celdas de barrio × ambientes × estado con datos suficientes. En el total de
la Ciudad, el desvío es de −5,2% a −8,5% en usados y de −13,5% a −16,3% a estrenar. El
desfase de un trimestre entre las fuentes no lo explica: IDECBA varió como máximo 0,8%
entre el 1er y el 2do trimestre de 2026.

*Consecuencia para los KPIs.* El precio está en el denominador de la rentabilidad, así
que la de la cartera sale **más alta** que la que daría el precio publicado promedio del
mercado. El alquiler estimado también sale de avisos de RE/MAX, y no hay fuente oficial
para medir si su cartera de alquileres tiene el mismo sesgo. Por lo tanto, el efecto neto
sobre el KPI no se puede firmar.

**Representación.** Respecto del stock de departamentos del Censo 2022, la cartera de
ventas sobrerrepresenta la comuna 1 (índice 1,28) y subrepresenta las comunas 4, 8 y 9
(índices de 0,47 a 0,68), que están en el sur y el oeste. Para replicar la composición del
censo habría que reasignar el 7,2% de las ventas a otras comunas. En alquileres el sesgo
es mayor: la comuna 14 (Palermo) tiene un índice de 1,68 y la 8, de 0,11.

*Consecuencia para generalizar.* Los promedios de ciudad del trabajo pesan de más a las
comunas sobrerrepresentadas. Por eso los KPIs se leen por barrio y no como un número del
mercado de CABA.

---

## Fuentes planificadas

### 6. IPC del INDEC

| Campo | Detalle |
|---|---|
| **Variable que aporta** | Variación mensual e interanual de precios al consumidor, incluido el componente de alquiler de la vivienda |
| **Cobertura geográfica** | Nacional y por región (GBA) |
| **Período** | Mensual |
| **Granularidad** | Región × mes × división |
| **Cómo se une con RE/MAX** | Por mes, a nivel agregado |
| **Qué ayuda a analizar** | La lectura en términos reales de un alquiler en pesos contra un precio en dólares (contexto, punto 1 del README) |
| **Limitaciones** | Mide precios al consumidor, no el precio de los inmuebles. No tiene apertura por barrio |
| **Fuente** | INDEC, informe técnico del IPC ([agosto de 2026](https://www.indec.gob.ar/uploads/informesdeprensa/ipc_09_26A1BE2DC4CD.pdf)) |

### 7. Transporte y espacios verdes (BA Data)

| Campo | Detalle |
|---|---|
| **Variable que aporta** | Distancia a la boca de subte, a la estación de tren y al espacio verde más cercanos |
| **Cobertura geográfica** | CABA |
| **Período** | Capas vigentes al momento de la descarga |
| **Granularidad** | Punto o polígono |
| **Cómo se une con RE/MAX** | Por coordenadas (`latitud`, `longitud`): es una **fusión espacial**, materia de la 3ra entrega |
| **Qué ayuda a analizar** | H2: el precio del m² decrece con la distancia al subte |
| **Limitaciones** | Las capas todavía no se descargaron: la 1ra entrega las identificó (379 bocas de subte, 301 estaciones ferroviarias y 2.176 espacios verdes públicos) y esta entrega no hace joins espaciales. Se incorporarán a `data/external/` en la 3ra. El cruce es viable porque el 99,9% de los avisos tiene coordenadas |
| **Fuente** | [Buenos Aires Data](https://data.buenosaires.gob.ar/) |