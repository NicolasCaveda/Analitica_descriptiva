# Diseño del tablero

Especificación del tablero en Streamlit: paleta, estructura, visualizaciones, filtros y
dinámica. Complementa a `GUIA_TABLERO.md`, que define **qué datos** usar y cómo leerlos;
este documento define **cómo se muestran**. Ante cualquier duda sobre columnas, cifras o
limitaciones, manda `GUIA_TABLERO.md`.

> Pregunta del tablero: **Tengo entre USD 80.000 y 200.000: ¿conviene comprar para
> alquilar, y si compro, qué?**

Publicado en Streamlit Community Cloud: <https://dashboard-descriptiva-g2.streamlit.app/>

---

## 1. Paleta y estilo

La paleta base del grupo (`#FFD275`, `#778472`, `#C5D5EA`, `#30343F`) se usa para la
**interfaz**. Para los **datos** se agregan tres tonos más profundos de los mismos matices,
porque el amarillo y el celeste originales tienen un contraste de ~1,4:1 sobre blanco (el
mínimo para marcas de un gráfico es 3:1) y el verde y el celeste se perciben casi grises.
Los tonos de datos se validaron en fondo claro y oscuro, incluida la separación para
daltonismo.

| Rol | Color | Uso |
|---|---|---|
| Texto y títulos | `#30343F` | Todo el texto; fondo de la barra lateral, de la tarjeta de lectura (pestaña 1) y de la conclusión (pestaña 4) |
| Fondo de la página | `#F3F5F9` | Detrás de las tarjetas |
| Tarjetas | `#FFFFFF` | Tarjetas de KPI y recuadros de cada gráfico, con borde de 1 px en `#E1E6EE` |
| Fondo secundario | `#E8EEF7` | Controles, filas de la sensibilidad iguales a la base, número de cada limitación |
| Texto secundario | `#5B6170` | Rótulos, notas y ejes (contraste 6:1 sobre blanco) |
| Acento | `#FFD275` | La banda de retorno 7,10–7,60% (área sombreada) y su muestra en la barra lateral. Única excepción de texto: la distancia al piso en la tarjeta oscura de lectura, donde el contraste es alto |
| Contexto | `#778472` | Pendiente de Theil-Sen (H1); referencias de ocupación (P3) |
| Dato principal | `#2F68B0` | Neta central, serie principal, histograma, gestión tercerizada (P3) |
| Dato de alerta | `#C08A1E` | Candidatas P1 "a verificar"; propiedades sobre el techo |
| Dato secundario | `#4A7F3A` | TIR por barrio; gestión autogestionada (P3) |
| Selección | `#00A676` | Propiedad elegida en todas las vistas (P2, mapa, ficha). Solo para eso |

**Escala divergente** (posición respecto de la banda, para el mapa y clasificaciones):

| Categoría | Color |
|---|---|
| Debajo del piso (< 7,10%) | `#2F68B0` |
| Dentro de la banda (7,10–7,60%) | `#B9BCC4` |
| Sobre el techo (> 7,60%) | `#C08A1E` |

**Reglas de color**
- Un color sigue a la entidad, no a su posición: si un filtro cambia las series, las que
  quedan no se repintan.
- La identidad nunca depende solo del color: con dos series o más hay leyenda o etiqueta
  directa.
- El texto va en `#30343F` (o `#5B6170` si es secundario), nunca en el color de la serie.

**Estilo**
- Letra **IBM Plex Sans** (Google Fonts), con cifras tabulares para que los números se
  alineen.
- **Barra lateral oscura** (`#30343F`) con los filtros; la página en `#F3F5F9` y cada
  gráfico en una tarjeta blanca.
- **Tamaño general** al ~80% del de Streamlit (`baseFontSize = 13`): el tablero entero
  entra en una pantalla de notebook sin achicar el navegador.

Los colores de datos e interfaz se definen una sola vez, en el diccionario `COLORES` de
`tablero/datos.py`; el tema de Streamlit está en `tablero/.streamlit/config.toml`:

```toml
[theme]
base = "light"
primaryColor = "#30343F"
backgroundColor = "#F3F5F9"
secondaryBackgroundColor = "#E8EEF7"
textColor = "#30343F"
linkColor = "#2F68B0"
borderColor = "#E1E6EE"
font = "IBM Plex Sans:https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap, sans-serif"
baseRadius = "10px"
baseFontSize = 13
showSidebarBorder = false

[theme.sidebar]
backgroundColor = "#30343F"
secondaryBackgroundColor = "#3A3F4B"
textColor = "#F1F3F7"
primaryColor = "#C5D5EA"
borderColor = "#555B6B"
```

---

## 2. Estructura

Una página con barra lateral de filtros, un encabezado y **cinco pestañas**. Cada pestaña
responde una pregunta del inversor; el tablero no replica los notebooks.

### Encabezado (visible en todas las pestañas)

- **Título** *"¿Conviene comprar para alquilar?"* y, debajo, la pregunta completa del
  tablero.
- **Contador de alcance**, a la derecha: *"N de 9.203 propiedades"* con una barra de la
  proporción y *"Cartera RE/MAX · relevada el 16 y 17-08-2026"*. N responde a los filtros.
- **Tres botones con las limitaciones obligatorias** (`GUIA_TABLERO.md`), siempre visibles.
  Cada uno abre su explicación completa con un clic (también en pantallas táctiles):
  1. *"Precios de publicación"*: son precios de publicación, no de cierre.
  2. *"Una sola inmobiliaria, ~8% más barata"*: es la cartera de una sola inmobiliaria,
     que publica ~8% más barato que el mercado; las rentabilidades probablemente están
     del lado alto.
  3. *"Cada rentabilidad es una banda"*: cada rentabilidad es una banda, no un número.

### Barra lateral

Marca del tablero, los filtros (sección 4), el botón **Restablecer filtros** y, al pie, la
**clave de la banda de retorno mínimo** (7,10–7,60% anual en USD, ON de YPF 2031 y Pampa
2037), que vale para todos los gráficos: es una referencia fija, no un filtro.

### Pestañas

| # | Pestaña | Pregunta que responde |
|---|---|---|
| 1 | ¿Conviene comprar? | ¿La propiedad típica le gana a la renta fija en dólares? |
| 2 | ¿Dónde? | ¿Qué barrios rinden más y por qué? |
| 3 | ¿Qué comprar? | ¿Qué propiedades vale la pena verificar? |
| 4 | ¿Tradicional o temporal? | ¿Alquilar por noche cambia la respuesta? |
| 5 | Supuestos y alcance | ¿Cuánto depende todo de los supuestos? ¿Qué no se puede afirmar? |

---

## 3. Visualizaciones

**Reglas para todas las vistas**
- Ninguna neta sin su banda (`neta_min_pct` a `neta_max_pct`).
- Ningún gráfico de rentabilidad sin la franja 7,10–7,60% sombreada en `#FFD275`.
- Medidas de resumen: **medianas**, no promedios.
- La banda y el presupuesto salen de `supuestos.py` (`S.RETORNO_MINIMO_BANDA`,
  `S.PRESUPUESTO_USD`); los nombres de barrio, de `eda.nombre_barrio()`. Ningún número
  escrito a mano en la app: todas las cifras de la pantalla se calculan con los datos.
- Gráficos con Plotly, con tooltip al pasar el mouse. Grilla y ejes discretos. Las
  tarjetas, la lectura, las etapas, el panel del mapa, la ficha y la sensibilidad son HTML
  propio (`st.html`).

### Pestaña 1 · ¿Conviene comprar?

- **Tarjeta de lectura** (oscura, a la izquierda): la conclusión con estos filtros, por
  ejemplo *"La propiedad típica rinde 1,72 pp menos que una ON en dólares: no conviene
  comprar."* Debajo, una escala con la banda de retorno, la banda mediana de la neta, la
  neta mediana y el tramo hasta el piso, con su leyenda. Reemplaza a la tarjeta "Distancia
  al piso".
- **Tres tarjetas de KPI** (responden a los filtros), cada una con su ayuda (ⓘ):
  - Neta mediana, con su banda mediana debajo y una escala chica con la banda de retorno
    (nunca la neta sola).
  - TIR a 5 años mediana (con costos de entrada), con la misma escala.
  - % de propiedades con neta sobre el piso, con una barra apilada en la escala
    divergente: debajo del piso, dentro de la banda y sobre el techo.
- **Histograma de la neta** (o de la TIR, según la métrica elegida) con la banda sombreada
  y la mediana marcada. Es el gráfico central del tablero.
- **Etapas del universo de decisión** (*"¿Cuántas pasan cada vara?"*): universo → neta
  central sobre el techo → P1 (neta pesimista sobre el techo) → TIR pesimista sobre el
  techo. Sin filtros: 4.484 → 227 → 18 → 4. **Barras horizontales** en escala lineal (no
  embudo, no logarítmica), con la cifra **afuera** de la barra en formato *"cantidad · %
  del universo"* (p. ej. *"18 · 0,4%"*), para que los valores chicos se lean. Las dos
  primeras en el dato principal y las dos últimas en el de alerta. Debajo, en un recuadro
  de aviso: *"Las que pasan P1 no son una recomendación: hay que verificar por qué son
  baratas."*
- El histograma y las etapas van lado a lado (columnas 3:2).

### Pestaña 2 · ¿Dónde?

Disposición: el **mapa con su panel** primero, a todo el ancho; debajo, los **puntos por
barrio** y la **dispersión H1** lado a lado. Tiene scroll (sección 6).

- **Mapa** de propiedades (`latitud`, `longitud`, fondo Carto Positron) coloreado con la
  escala divergente. A su derecha, un **panel** con la barra apilada de posición respecto
  de la banda, la cantidad y el % de cada categoría, los seis barrios con más propiedades
  sobre el techo y la nota de los avisos sin coordenadas (5 de las 9.203 ventas, 2 con los
  filtros por defecto). Con una propiedad elegida, el panel la agrega a la leyenda.
- **Puntos por barrio** desde `ranking_barrios.csv` (solo barrios con 30 ventas o más):
  neta y TIR medianas, ordenadas, con la banda de la neta y la franja sombreada. Los
  barrios elegidos en el filtro se resaltan y el resto queda atenuado; la tabla en sí no
  se filtra.
- **Dispersión H1**: m² del barrio contra rentabilidad bruta, con la pendiente de
  Theil-Sen. Arriba, la cifra grande de la pendiente con su IC 95% (con los filtros por
  defecto, −0,68 pp de bruta por cada USD 500/m², IC −0,92 a −0,52).

### Pestaña 3 · ¿Qué comprar?

Solo con `universo_decision = True`.

- **Gráfico de rangos de la frontera P2** (`p2_no_dominada`): una barra horizontal de
  `neta_min_pct` a `neta_max_pct` por propiedad, con la banda de referencia,
  **ordenada por ancho de banda (más angosta arriba), nunca por rentabilidad**. Nota:
  *"Entre estas propiedades ninguna le gana con claridad a otra."*
- **Tabla P1 "a verificar"** (`p1_comprar`): barrio, precio, superficie, neta pesimista,
  m² contra su celda, **"Con entrada"** (*"pasa"* si también pasa con los costos de
  entrada) y link al aviso (`url`). Encima, en un recuadro de aviso: *"Cuestan ~30% menos
  por m² que su celda: verificar por qué antes de decidir."* Nunca rotularla como
  "comprar". Las columnas guardan números y solo el formato es argentino, así que la
  tabla **ordena por número** al hacer clic en el encabezado.
- **Ficha de la propiedad seleccionada** (el link lleva al aviso relevado; si ya no está
  publicado, RE/MAX abre su portada, y el tooltip lo avisa): título, barrio y ambientes,
  botón *"Ver aviso"*, neta con su banda en una escala, precio y m², m² contra su celda,
  alquiler estimado con su rango p10–p90, TIR 5 años (y pesimista), costos de entrada,
  modo de transporte y distancia, y días de publicación típicos.

### Pestaña 4 · ¿Tradicional o temporal?

- **Líneas** desde `decision_p3.csv`: cantidad de celdas (de 47) donde gana el temporal
  según la ocupación sostenible, una línea por tipo de gestión (tercerizada en
  `#2F68B0`, autogestionada en `#4A7F3A`), con etiqueta directa. Líneas verticales de
  referencia en 18,6% (Inside Airbnb) y 53% (prensa), rotuladas.
- **Selector de vacancia** del alquiler tradicional, como botones con los valores de la
  tabla y la base marcada.
- Dos tarjetas con la **ocupación de equilibrio** de cada gestión.
- **Conclusión** en una tarjeta oscura: tradicional, salvo autogestión con evidencia de
  más de la mitad del año ocupado.

### Pestaña 5 · Supuestos y alcance

- **Sensibilidad** desde `decision_sensibilidad.csv`: cuántas propiedades pasan P1 (y P1
  con entrada) en cada uno de los 22 escenarios, **agrupados por supuesto**, con barras y
  cifras; las filas iguales a la base van con fondo. Arriba, la cifra que resume la
  pestaña: sin contar los dos extremos combinados, P1 va de 6 a 33 propiedades según el
  supuesto (base: 18).
- **Limitaciones completas**, numeradas: las tres del encabezado, más casas y PH fuera de
  las recomendaciones, sin apreciación, sin costos de salida, sin riesgo legal, liquidez de
  toda la Ciudad y no causalidad.
- **Fuentes y fecha de los datos**, con remisión a `informe/FUENTES_EXTERNAS.md`.

---

## 4. Filtros

En la barra lateral, todos juntos, con un botón para restablecerlos.

| Filtro | Columna | Control | Default |
|---|---|---|---|
| Presupuesto | `venta_usd` | Dos campos, *Desde* y *Hasta* (USD, de a 5.000) | 80.000–200.000 (`S.PRESUPUESTO_USD`) |
| Tipo | `tipo_familia` | Selector de un botón: Depto., PH, Casa, Todos | Departamento |
| Comuna | `comuna` | Multiselect | Todas |
| Barrio | `barrio` | Multiselect (acotado por la comuna elegida) | Todos |
| Ambientes | `ambientes` | Botones 1, 2, 3, 4 y 5+ (5+: cinco o más) | Todos |
| Superficie | `superficie_rango` | Botones (≤ 35, 36–55, 56–80, 81–120, 120+) | Todos |
| Antigüedad | `antiguedad_rango` | Botones (A estrenar, 1–5, 6–15, 16–30, 31–50, 50+) | Todos |
| Métrica | — | Selector de un botón: Neta / TIR 5 años | Neta |
| Restablecer filtros | — | Botón | — |

En los filtros de botones, ninguno elegido equivale a todos.

**Fuera de los filtros, a propósito**
- La banda de retorno: es una línea de referencia fija, no un filtro.
- Amenities, cochera y demás atributos: no cambian la decisión (`GUIA_TABLERO.md`).

---

## 5. Dinámica

- **Qué responde a los filtros.** Las vistas que leen `dataset_analitico.csv` (pestaña 1,
  mapa, panel y dispersión de la 2, toda la 3) se filtran. Las que leen tablas
  precalculadas (ranking de barrios, P3, sensibilidad) no, y cada una lo indica con la
  etiqueta *"No responde a los filtros"*.
- **Estados vacíos.** Si los filtros dejan 0 propiedades: un mensaje (`st.info`) en lugar
  de los gráficos. Si quedan menos de 30: advertencia de que la mediana es poco
  confiable.
- **Casas y PH.** Si se eligen: advertencia de que el modelo casi no tiene alquileres
  observados de ellos, y las secciones P1 y P2 se ocultan.
- **Selección.** Clic en una fila de la tabla P1 o en una barra de P2 abre su ficha y
  resalta la propiedad en `#00A676` en P2 y en el mapa: la elegida va encima, más gruesa y
  sin borde; el resto se atenúa. Destildar la fila, hacer clic de nuevo sobre la elegida o
  afuera de las barras la deselecciona: P2, el mapa y la ficha vuelven a su estado sin
  selección. Elegir en P1 o en P2 vacía la selección del otro. La selección se mantiene
  aunque la tabla esté ordenada por otra columna.
- **Rendimiento.** El CSV se lee una sola vez con `st.cache_data`, solo con las columnas
  de `GUIA_TABLERO.md`, aplicando el filtro `operacion = "venta"` y
  `estimacion_confiable = 1`.
- **Tamaño.** Un solo valor, `baseFontSize` en `config.toml`, controla el tamaño de todo:
  los estilos propios van en `rem`, y el alto de los gráficos de Plotly, el zoom del mapa y
  el ancho inicial de la barra lateral se escalan con la misma proporción.
- **Organización del código.** Todo el tablero vive en `tablero/`. `app.py` solo arma la
  interfaz. La carga, el filtrado y las medianas van en `tablero/datos.py`, con su test
  (`tablero/test_tablero.py`); `datos.py` importa `supuestos` y `eda` de `src/`. Los KPIs
  no se recalculan: se usan las columnas ya materializadas. `st.html` limpia el HTML con
  DOMPurify y descarta los `<svg>`, así que los íconos van como imágenes `data:`.
- **Ejecución local.** Desde `Entrega 3/tablero/`: `streamlit run app.py`. Streamlit lee el
  tema de `.streamlit/config.toml` en la carpeta desde donde se ejecuta, por eso se corre
  desde `tablero/`. Las dependencias están en `Entrega 3/requirements.txt` y las
  instrucciones en el README.
- **Publicación.** Streamlit Community Cloud toma las dependencias del `requirements.txt`
  de la **raíz** del repositorio, con solo los paquetes del tablero: no lee
  `Entrega 3/requirements.txt`, y el espacio de "Entrega 3" corta la ruta que le pasa al
  instalador. Ese archivo pide `streamlit>=1.66.1` y no una versión fija: con una versión
  más vieja que la de la nube, la página queda cargando sin fin.

---

## 6. Reglas de diseño de pantalla

Valen para todas las pestañas.

- **Layout ancho** (`st.set_page_config(layout="wide")`).
- **Las pestañas 1, 3 y 4 entran sin scroll en 1440×900**: lo principal arriba, el detalle
  debajo. Las otras dos tienen scroll a propósito: la 2, porque el mapa va primero y a
  todo el ancho; la 5, por la lista de los 22 escenarios de la sensibilidad.
- **Gráficos lado a lado** en columnas (`st.columns`) y dentro de tarjetas blancas con
  borde (`st.container(border=True)`), con márgenes de Plotly chicos.
- **Explicaciones en ayudas** (el ícono de ayuda junto al título o ⓘ en las tarjetas), no
  en párrafos.
- **Sin subtítulos que no sean esenciales** y sin repetir en texto lo que ya dice una
  tarjeta o un gráfico.
- **Los valores chicos siempre con etiqueta legible** fuera de la barra.
- **Solo quedan como texto visible las advertencias que exige `GUIA_TABLERO.md`**: las
  limitaciones del encabezado, el "verificar, no comprar" de P1 y el no ordenar P2 por
  rentabilidad, en una sola línea cada una. Los estados de la sección 5 (sin
  propiedades, pocas observaciones, casas y PH) también se muestran.

---

## Verificación antes de entregar

Hecha el 05-11-2026 sobre la versión de `main`.

| Qué se verifica | Cómo | Resultado |
|---|---|---|
| Sin filtros, los números coinciden con `informe/INFORME_HALLAZGOS.md` (neta mediana 5,65%, 19,4% sobre el piso, etapas 4.484 → 227 → 18 → 4, TIR mediana 4,27%) | `tablero/test_tablero.py` | 106 tests, 0 fallos |
| Cada filtro cambia el contador N y las vistas que deben cambiar, y no cambia las que no | `test_tablero.py` (cada filtro contra su condición, fila por fila); las vistas precalculadas llevan la etiqueta *"No responde a los filtros"* | OK |
| Los estados vacíos y de pocas observaciones no rompen los KPIs ni las etapas, y muestran su mensaje | `test_tablero.py` (filtros que dejan 0 filas) y mensajes en `app.py` | OK |
| Ninguna neta aparece sin su banda ni ningún gráfico de rentabilidad sin la franja | Revisión de las cinco pestañas | OK |
| Las pestañas 1, 3 y 4 entran sin scroll en 1440×900; la 2 y la 5 tienen scroll a propósito | Alto de cada pestaña medido en un navegador a 1440×900 | 900 px las tres; 1.225 px la 2 y 1.107 px la 5 |
| La tabla P1 ordena por número y la selección de P1 o P2 abre la ficha y marca la propiedad en P2 y en el mapa | Prueba en el navegador | OK |
| El tablero publicado carga | <https://dashboard-descriptiva-g2.streamlit.app/> | Carga con sus cinco pestañas, sin errores |
| Capturas de las vistas principales para la entrega final | — | Pendiente |
