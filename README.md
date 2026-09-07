# Inteligencia de Mercado Inmobiliario — CABA

**TP Integrador — 82.04 Analítica Descriptiva (ITBA)**
**Primera Pre-Entrega: Estrategia, Arquitectura del Problema y Recolección de Datos**

Construcción desde cero de una base de datos del mercado inmobiliario porteño
mediante extracción automatizada, orientada a una pregunta de negocio: **¿qué
conviene comprar en CABA para ponerlo en alquiler?**

La materia prima no venía dada. Este repositorio documenta cómo se construyó.

---

## Reproducir la extracción

```bash
py -m pip install -r requirements.txt

py test_parseo.py                    # verifica el parseo, no toca la red
py run_scrapers.py --portal remax --operacion ambas --paginas 200 --detalle
```

El resultado se consolida en `data/raw/dataset_maestro.csv`, que ya está en el
repositorio.

> **`Brotli` no es opcional.** Sin ese paquete el scraper devuelve 0 avisos sin
> dar ningún error. Ver [Desafíos técnicos](#a-desafíos-técnicos-encontrados).

**Evidencia de la corrida:** [`notebooks/01_extraccion.ipynb`](notebooks/01_extraccion.ipynb)

---

## 1. Contexto y situación de negocio

### La problemática

El mercado inmobiliario argentino es, para el ahorrista promedio, el destino más
habitual de los excedentes en dólares. Pero también es un mercado **opaco**: no
existe un registro público de precios de cierre, la oferta está dispersa en decenas
de portales con criterios distintos, y la asimetría de información favorece
sistemáticamente a quien vende.

El resultado es que las decisiones de inversión se toman con información anecdótica.
"Comprá en Palermo que siempre se alquila" o "Caballito es lo que más rinde" son
afirmaciones que circulan como sentido común sin ningún respaldo cuantitativo, y que
comprometen el ahorro de toda una vida.

### El interlocutor

**Perfil: pequeño inversor particular.**

Una persona con ahorros en dólares —típicamente entre USD 80.000 y 200.000— que
evalúa comprar **una sola unidad** en CABA para ponerla en alquiler y generar un
ingreso mensual. No es un desarrollador ni un fondo: es alguien que hace esta
operación una o dos veces en su vida.

Sus características definen todo el análisis:

**Compra una unidad, no una cartera.** No puede diversificar. Si elige mal, no hay
otra inversión que compense: el error impacta el 100% de su capital.

**Su ticket está acotado.** El 59% de la oferta relevada está por debajo de los USD
150.000, y la mediana en USD 130.000. Ese es su universo real de decisión.

**Prioriza previsibilidad sobre rendimiento máximo.** Un punto adicional de
rentabilidad no compensa el riesgo de tres meses sin inquilino o de un inmueble
difícil de revender.

**No tiene acceso a información profesional.** No trabaja con tasadores ni
consultoras; su fuente de información son los mismos avisos públicos que este
proyecto releva.

### El dolor concreto

Frente a dos departamentos de precio similar, el inversor no tiene forma de saber
cuál va a rendir mejor. No existe una fuente pública que relacione, para un mismo
tipo de inmueble y una misma zona, el precio de venta con el precio de alquiler.

Esa relación es precisamente lo que determina si una compra es buen negocio, y es la
que este proyecto se propone construir.

---

## 2. Objetivo principal del análisis

**Dotar al pequeño inversor de una estimación cuantificada de la rentabilidad
esperada de cualquier inmueble en venta de CABA, junto con el margen de error de esa
estimación, para que pueda comparar alternativas concretas sobre evidencia en lugar
de sobre percepciones del mercado.**

El objetivo se descompone en tres capacidades:

**Estimar.** Predecir cuánto se alquilaría un inmueble que hoy está publicado en
venta, a partir de sus características observables.

**Comparar.** Ordenar barrios y tipologías por rentabilidad esperada, distinguiendo
las diferencias reales de las que caen dentro del error de estimación.

**Advertir.** Explicitar la incertidumbre de cada estimación. Una recomendación sin
intervalo de confianza le da al inversor una falsa sensación de precisión, que en su
situación —una sola compra, sin posibilidad de diversificar— es más peligrosa que la
ignorancia.

### Lo que este análisis NO se propone

No estima la **revalorización** del inmueble, solo la renta. El retorno total de una
inversión inmobiliaria incluye la apreciación del capital, que requiere series
históricas de las que este dataset carece.

No sustituye la **inspección física** ni la verificación legal del inmueble.

No predice **precios de cierre**, sino que trabaja sobre precios de publicación.

---

## 3. Alcance

**Incluye.** Avisos de venta y alquiler publicados en CABA por RE/MAX, relevados en
agosto de 2026, cubriendo los 48 barrios y las 15 comunas.

**Excluye del análisis posterior.** Cocheras, oficinas, locales, terrenos, depósitos
y hoteles: no responden a la tesis de inversión del cliente definido y distorsionan
el precio por metro cuadrado. Se capturan igual en la extracción y se filtran en la
etapa de curaduría.

**Limitaciones declaradas.**

1. **Fuente única.** El dataset refleja la cartera de RE/MAX, no el mercado completo
   de CABA. Las comparaciones entre barrios son válidas; los niveles absolutos deben
   leerse como representativos de ese segmento.
2. **Corte temporal único.** No permite análisis de series ni estacionalidad.
3. **Precios de publicación, no de cierre.** En un mercado con negociación, el precio
   final suele ser menor.
4. **Desbalance venta/alquiler.** Hay 7,4 avisos de venta por cada uno de alquiler, lo
   que condiciona cómo podrá estimarse el alquiler esperado.

---

## 4. Definición del usuario final

### Quién usa el producto

El **pequeño inversor particular** descrito en el punto 1, sin formación técnica en
datos. No programa, no interpreta un R², y no va a leer un notebook.

Esto impone tres restricciones de diseño para las etapas siguientes:

**Los resultados deben ser legibles sin conocimiento estadístico.**

**La incertidumbre debe expresarse en las unidades de su decisión** — no en puntos de
error de un modelo, sino en el rango de rentabilidad que puede esperar.

**La herramienta debe responder su pregunta real**, que no es "¿qué barrio rinde
más?" sino "¿este departamento que estoy mirando es una buena compra?".

### Usuarios secundarios

**Inmobiliarias y agentes**, que podrían usar una estimación de renta como argumento
de venta cuantificado.

**El equipo del proyecto**, para quien el dataset construido es el insumo de todas las
etapas posteriores.

---

## 5. Preguntas clave según los 4 niveles de análisis

### Descriptivo — ¿qué pasó?

- ¿Cuál es el precio por m² promedio, mediano y su dispersión en cada barrio de CABA?
- ¿Cómo varía esa curva según la antigüedad de la edificación?
- ¿Cómo se distribuye espacialmente la oferta de venta frente a la de alquiler?
- ¿Qué proporción de la oferta tiene cochera, balcón o amenities?
- ¿Qué porcentaje del stock se publica como apto crédito?

### Diagnóstico — ¿por qué pasó?

- ¿Qué características explican la variación del precio de alquiler?
- ¿Cuánto del precio se explica por la ubicación y cuánto por atributos del inmueble?
- ¿Cuánto "premio" otorga el mercado por tener cochera, balcón o seguridad, y ese
  premio es igual en todos los barrios?
- ¿Cómo impacta la cercanía al transporte público en la valuación?

### Predictivo — ¿qué va a pasar?

- Dado un inmueble publicado en venta, ¿cuánto se alquilaría?
- ¿Qué rentabilidad esperada tiene cada propiedad de la oferta actual?
- ¿Con qué margen de error puede estimarse esa rentabilidad?

### Prescriptivo — ¿qué conviene hacer?

- ¿En qué barrios conviene comprar para maximizar la renta?
- ¿Qué combinación de barrio, tipología y superficie ofrece la mejor relación entre
  rentabilidad y riesgo?
- ¿Conviene pagar la prima por cochera o amenities en términos de renta?

---

## 6. Definición de los KPIs

Cada indicador se define en dos planos: la fórmula que lo calcula y la decisión que le
permite tomar al inversor.

### KPI 1 — Rentabilidad Bruta Anual

```
Rentabilidad Bruta Anual (%) = (Alquiler mensual estimado × 12) / Precio de venta × 100
```

**Lectura comercial.** Es el rendimiento del capital antes de costos. Responde
*"¿cuánto me devuelve por año lo que invierto?"* y sirve para **comparar** alternativas
entre sí, porque no depende de supuestos sobre gastos.

Es el indicador de **cribado**: permite descartar rápido las opciones que rinden por
debajo del mercado. No es lo que el inversor va a cobrar; para eso está el siguiente.

### KPI 2 — Rentabilidad Neta Anual

```
Rentabilidad Neta Anual (%) = Bruta × (1 − vacancia) × (1 − gastos)
```

**Lectura comercial.** Es el ingreso que efectivamente queda en el bolsillo del
propietario. Responde *"¿cuánto voy a cobrar realmente?"* y es el número que se compara
contra alternativas de inversión: un plazo fijo en dólares, un bono, un fondo.

Descuenta dos cosas que el inversor primerizo suele ignorar: la **vacancia** —los meses
sin inquilino entre contratos— y los **gastos del propietario**: administración, ABL,
expensas extraordinarias y mantenimiento.

Las **expensas ordinarias no se descuentan** porque en CABA las paga el inquilino. Sí
impactan de forma indirecta, ya que un edificio con expensas altas reduce el alquiler
que el mercado está dispuesto a pagar.

### KPI 3 — Meses de repago

```
Meses de repago = Precio de venta / Alquiler mensual estimado
```

**Lectura comercial.** Cuánto tarda la inversión en devolver el capital vía renta.
Responde *"¿en cuántos años recupero lo que puse?"*.

Es el KPI más intuitivo para quien no está familiarizado con porcentajes de retorno, y
el más directo de comunicar. También funciona como control de sanidad: un repago
anormalmente corto en este mercado es señal de que hay un error en los datos.

### KPI 4 — Banda de incertidumbre

```
Rango de rentabilidad = Rentabilidad Bruta × (1 ± error de estimación)
```

**Lectura comercial.** Es el KPI que evita decisiones sobre diferencias que no son
reales. Responde *"¿qué tan confiable es esta estimación?"*.

Si dos propiedades estiman rentabilidades muy parecidas pero el margen de error las
solapa, la diferencia entre ellas es indistinguible del ruido y no debe usarse para
decidir. Para un inversor que compra una sola propiedad y no puede promediar errores
entre varias, este indicador es tan importante como el rendimiento mismo.

---

## 7. Hipótesis a validar

**H1 — La rentabilidad bruta es inversamente proporcional al precio del m² del
barrio.** Los barrios premium rinden menos como renta, porque el precio de venta sube
más rápido que el de alquiler.

> *Cómo se testea:* correlación de Spearman entre precio mediano por m² y rentabilidad
> bruta, calculada por barrio sobre los barrios con muestra suficiente.

**H2 — El precio por m² decrece con la distancia a la estación de subte más cercana**,
y existe un radio de influencia a partir del cual el beneficio se diluye.

> *Cómo se testea:* cruce espacial con las bocas de subte del GCBA usando las
> coordenadas de cada propiedad, controlando por barrio para aislar el efecto de la
> centralidad.

**H3 — Los inmuebles "a reciclar" cotizan con descuento respecto de su valor esperado
según características**, y ese descuento es la oportunidad de arbitraje.

> *Cómo se testea:* comparación del precio observado contra el predicho por un modelo
> que controle superficie, barrio, antigüedad y amenities.

**H4 — La antigüedad impacta más en el precio de venta que en el de alquiler.** Quien
alquila valora la funcionalidad presente; quien compra, la vida útil restante del
activo.

> *Cómo se testea:* comparación del coeficiente de antigüedad en dos modelos análogos,
> uno sobre precio de venta y otro sobre precio de alquiler.

---

## 8. Descripción del dataset

### Fuente utilizada

**RE/MAX Argentina**, a través de su API JSON pública (`api.redremax.com`), la misma
que consume su sitio web.

Se desarrollaron y evaluaron extractores para cuatro portales:

| Portal | Método evaluado | Resultado |
|---|---|---|
| Argenprop | HTML server-rendered | Funcional. Descartado por unicidad de criterio. |
| MercadoLibre | HTML + JSON embebido | Funcional. Descartado por unicidad de criterio. |
| Zonaprop | HTML + JSON embebido | Bloqueado por DataDome (ver anexo A.3). |
| **RE/MAX** | **API JSON** | **Fuente elegida.** |

**Por qué una sola fuente.** Consolidar cuatro portales exige un dedup cruzado por
dirección, superficie y precio, porque un mismo inmueble suele publicarse en varios.
Ese cruce es impreciso y arrastra un error difícil de cuantificar. Además, cada portal
normaliza distinto los barrios, las superficies y las tipologías. Se priorizó la
**consistencia interna** sobre el volumen.

**Ventaja adicional.** RE/MAX es la única de las cuatro fuentes que expone **latitud y
longitud** confiables, lo que habilita los cruces espaciales previstos para etapas
posteriores.

### Volumen y composición

| | Cantidad |
|---|---:|
| Avisos capturados | 14.867 |
| Variables | 55 |
| Operaciones de venta | 13.106 |
| Operaciones de alquiler | 1.761 |
| Barrios cubiertos | 48 de 48 |
| Comunas cubiertas | 15 de 15 |

La captura se realizó con el flag `--detalle`, que entra a cada ficha individual. Sin
él, la API de listado no devuelve antigüedad, dormitorios, cocheras ni descripciones.

### Tipos de dato capturados

El esquema unificado cubre los cuatro tipos que exige la consigna:

- **Numéricas (12)** — `precio_valor`, `sup_total_m2`, `sup_cubierta_m2`, `ambientes`,
  `dormitorios`, `banos`, `cocheras`, `antiguedad_anios`, `expensas_valor`, `latitud`,
  `longitud`, `precio_m2`
- **Textuales y categóricas (8)** — `portal`, `operacion`, `tipo_propiedad`, `barrio`,
  `calle`, `titulo`, `descripcion`, `precio_moneda`
- **Ordinales (2)** — `comuna`, `piso`
- **Dicotómicas (23)** — `amenities`, `pileta`, `parrilla`, `gimnasio`, `sum`,
  `losa_radiante`, `aire_acondicionado`, `apto_credito`, `apto_profesional`,
  `cochera_txt`, `baulera`, `seguridad`, `luminoso`, `balcon`, `a_reciclar`,
  `reciclado`, `credito_uva`, `frente`, `amoblado`, `patio_jardin`, `ascensor`,
  `profesional_renta`, `es_a_estrenar`

**El precio se captura separado en valor numérico y moneda**, no como cadena de texto.
Es una mejora sobre el script base de la cátedra, que lo dejaba como `"USD 145.000"`,
imposible de promediar.

**El barrio se normaliza** contra los 48 barrios oficiales de CABA, resolviendo alias
(`Palermo Hollywood` → `palermo`, `Barrio Norte` → `recoleta`, `Once` → `balvanera`),
y de él se deriva la comuna.

**Las variables dicotómicas se construyen** aplicando expresiones regulares sobre el
texto libre de título, descripción y detalles.

---

## 9. Planificación de fuentes externas

Fuentes públicas que se integrarán en las etapas siguientes, cada una justificada por
la hipótesis o pregunta que permite responder.

| Fuente | Qué aporta | Para qué |
|---|---|---|
| Bocas de subte (BA Data) | Coordenadas de las 379 bocas | Validar H2: distancia al transporte y su radio de influencia |
| Estaciones ferroviarias (BA Data) | Coordenadas de estaciones | Completar la accesibilidad en zonas sin subte |
| Espacios verdes (BA Data) | Polígonos de plazas y parques | Medir la prima por cercanía a espacio verde |
| Polígonos de barrios y comunas (BA Data) | Geometrías oficiales | Validar la asignación de barrio y habilitar mapas coropléticos |
| Delitos por comuna (BA Data) | Hechos registrados | Construir un índice de seguridad por zona |
| Tipo de cambio (API BCRA) | Serie ARS/USD | Convertir alquileres publicados en pesos y medir la sensibilidad del KPI |
| Censo 2022 por radio censal (INDEC) | Nivel socioeconómico | Segmentar la demanda potencial de alquiler |

El cruce es posible porque el 99,9% de los avisos tiene coordenadas geográficas.

---

## 10. Hoja de ruta

Tareas analíticas previstas para las etapas siguientes.

**Curaduría del dato.** Tratamiento de faltantes y outliers con justificación técnica,
normalización monetaria, detección de errores de carga y filtrado de tipologías fuera
de alcance.

**Ingeniería de variables.** Materialización de los KPIs definidos en el punto 6,
construcción de variables derivadas y minería de las descripciones con expresiones
regulares.

**Análisis exploratorio.** Estadísticos de resumen robustos, distribuciones por barrio
y tipología, matrices de correlación y narrativa visual.

**Inferencia.** Tests estadísticos formales para validar las hipótesis del punto 7,
documentando p-valor y decisión sobre la hipótesis nula.

**Fusión espacial.** Cruce de las coordenadas con las fuentes externas del punto 9.

**Reducción de dimensionalidad y clustering.** PCA y MCA para sintetizar los atributos
dispersos en índices interpretables, y segmentación no supervisada para descubrir
micro-mercados.

**Tablero y presentación.** Dashboard interactivo e informe final orientado al inversor.

### Dependencia crítica

El análisis temporal —tiempo de publicación como proxy del *time to sell*, evolución de
precios, probabilidad de colocación en 30 o 60 días— requiere **recolección
periódica**. Si no se inicia un relevamiento recurrente en las próximas semanas, esas
preguntas quedan fuera de alcance de forma definitiva: no pueden reconstruirse hacia
atrás.

---

# Anexos técnicos

## A. Desafíos técnicos encontrados

### A.1 Compresión Brotli — el bug silencioso

**Síntoma.** Tres de los cuatro portales devolvían **cero avisos**. Status HTTP 200,
respuestas de unos 290 KB, ninguna excepción. Todo indicaba un cambio de selectores CSS.

**Diagnóstico.** Al inspeccionar el HTML guardado, el contenido era **78% de bytes no
imprimibles**: no era HTML, era un blob binario.

**Causa.** El scraper declaraba `Accept-Encoding: gzip, deflate, br` pero el paquete
`Brotli` no estaba instalado. El servidor toma la palabra y responde comprimido,
`urllib3` no sabe descomprimirlo y entrega los bytes crudos. `resp.text` devuelve
basura binaria y BeautifulSoup no encuentra nada.

Argenprop nunca falló porque su CDN devuelve **gzip**, que la librería estándar sí
descomprime. Esa asimetría hacía parecer que el problema era de los otros portales.

**Por qué es insidioso.** No falla ruidosamente: no hay excepción, el status es 200 y el
tamaño del cuerpo es el esperable. Es indistinguible de un problema de selectores, y es
fácil perder horas buscando en el lugar equivocado.

**Solución, en dos capas** (`src/utils.py`):

1. `_codecs_disponibles()` verifica en tiempo de import qué librerías de descompresión
   están instaladas y declara **solo esos codecs**.
2. `_arreglar_compresion()` detecta un cuerpo binario y lo descomprime a mano, por si el
   servidor comprime aunque no se lo hayamos pedido.

Probado contra gzip, brotli, zstd y deflate.

### A.2 Huella TLS

`requests` tiene un *fingerprint* TLS —el JA3 del handshake— que no coincide con el de
ningún navegador real: orden de cipher suites, extensiones, curvas elípticas. Los
servicios anti-bot comerciales lo detectan **en el handshake, antes de leer un solo
header**, por lo que declarar un User-Agent de Chrome no ayuda.

Se resolvió con [`curl_cffi`](https://github.com/lexiforest/curl_cffi), que usa
`libcurl-impersonate` para replicar el handshake exacto de Chrome. `utils.py` lo usa si
está instalado y cae a `requests` si no.

### A.3 Zonaprop y DataDome

Zonaprop es el portal de mayor volumen del mercado y el más protegido: fingerprinting de
TLS, challenge de JavaScript, rate limiting por IP y captcha. Ninguna librería HTTP
resuelve el challenge de JavaScript, porque requiere ejecutarlo.

Se implementó un plan B con Playwright, que corre un Chromium real y resuelve el
challenge automáticamente. Funciona, pero la fragilidad del enfoque —sumada a la
decisión de trabajar con fuente única— llevó a descartar el portal.

### A.4 API oficial de MercadoLibre

MercadoLibre cerró el acceso anónimo a `api.mercadolibre.com`; hoy exige un token de
aplicación registrada. Por eso se scrapeó HTML. La salida limpia sería tramitar
credenciales en `developers.mercadolibre.com.ar`.

---

## B. Mejoras sobre el script base de la cátedra

1. **Precio numérico con moneda separada.** Antes quedaba como cadena `"USD 145.000"`,
   imposible de promediar.
2. **Superficie, ambientes, dormitorios, baños, cocheras y antigüedad** parseados a
   valores numéricos.
3. **Barrio normalizado** contra los 48 barrios oficiales, con resolución de alias y
   derivación de comuna.
4. **Venta y alquiler parametrizados** (el original tenía la operación hardcodeada).
5. **Selectores con fallback**: si el portal cambia una clase, prueba alternativas en
   orden en vez de devolver un dataset vacío.
6. **Reintentos con backoff exponencial, checkpoints y deduplicación** por URL e ID.
7. **Manejo de errores explícito.** Los `except: pass` del script original ocultaban las
   fallas; ahora se cuentan y se reportan.
8. **Tests de parseo sin red** (`test_parseo.py`), que permiten verificar la lógica de
   extracción sin depender de la disponibilidad de los portales.

---

## Estructura del repositorio

```
├── src/                          paquete de extracción
│   ├── utils.py                  parseo, barrios, esquema, HTTP, compresión
│   ├── base.py                   BaseScraper: paginación, dedup, checkpoints
│   └── remax.py                  cliente de la API de RE/MAX
├── notebooks/
│   └── 01_extraccion.ipynb       evidencia documentada de la corrida
├── data/raw/
│   └── dataset_maestro.csv       14.867 avisos, 55 variables
├── run_scrapers.py               CLI de extracción
├── test_parseo.py                tests sin red
├── requirements.txt
├── README.md                     este documento
└── Informe_Ejecutivo.pdf         informe de negocio
```

---

## Convenciones de código

- Código y comentarios en español, sin tildes en los comentarios (evita problemas de
  encoding en Windows). En Markdown sí van tildes.
- Los comentarios explican **por qué**, no qué. Se documentan las decisiones y las
  trampas encontradas.
- No usar `except: pass`. Los errores se cuentan y se reportan.
- Todo parseo nuevo va con su test en `test_parseo.py`.
- Los CSV se guardan con `utf-8-sig` para que Excel abra bien las tildes.
- Respetar los delays entre requests. No bajarlos para ir más rápido.

## Si un scraper deja de funcionar

Los portales cambian el HTML seguido. Cuando devuelva cero avisos:

```bash
py run_scrapers.py --portal remax --paginas 1 --debug
```

Revisar el HTML guardado en `data/debug/`. Si tiene un alto porcentaje de bytes no
imprimibles, es el problema de compresión del anexo A.1, no los selectores. Si es HTML
legible, buscar el nombre de clase nuevo y agregarlo **al principio** de la lista en
`first_elements([...])`, sin borrar los viejos.
