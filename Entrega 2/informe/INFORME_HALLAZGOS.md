# Informe de hallazgos — 2da pre-entrega

**TP Integrador · 82.04 Analítica Descriptiva (ITBA) · Grupo 2**

*Generado por `py src/reporte.py` el 05-10-2026. Cada cifra de este documento se calcula al generarlo a partir de `data/processed/` y `data/external/`: si se reejecuta el pipeline, el informe se regenera con los números nuevos.*

**Cliente:** un pequeño inversor con ahorros en dólares que compra **una sola unidad** en CABA para alquilarla, con un presupuesto de USD 80.000 a USD 200.000. **Base:** 9.203 departamentos, casas y PH en venta de la cartera de RE/MAX, relevados entre el 16-08-2026 y el 17-08-2026, con alquiler estimado confiable.

Los hallazgos van ordenados por cuánto cambian la decisión del inversor. Cada uno cierra con la decisión que modifica.

---

## 1. Solo por renta, el ladrillo no le gana a un bono corporativo en dólares

La rentabilidad **neta** mediana (después de 5,88% de vacancia y 14,04% de gastos del propietario) es **5,67%**. La banda de retorno mínimo, las obligaciones negociables corporativas en dólares de YPF 2031 y Pampa 2037, va de **7,10% a 7,60%**. La propiedad mediana queda 1,43 pp por debajo del piso.

| | mediana | supera el piso de la banda |
|---|---|---|
| Rentabilidad bruta | 7,01% | 48,1% |
| Rentabilidad neta | 5,67% | 19,1% |
| Neta, solo dentro del presupuesto | 5,56% | 14,6% |
| Neta en el extremo optimista de la banda de error (KPI 4) | — | 33,8% |

De los 29 barrios con 30 o más ventas, 1 tiene una neta mediana sobre el piso (Constitución). La comparación es contra un instrumento que paga en dólares, cotiza en bolsa y no tiene vacancia, inquilino ni expensas extraordinarias.

**El resultado depende poco de los supuestos en el nivel, pero mucho en el umbral.** Recorriendo vacancia de 4% a 12% y gastos de 8% a 16%, la neta mediana se mueve entre 5,18% y 6,19%: en ningún escenario alcanza el piso. Lo que sí cambia es cuántos barrios lo superan: de 10 en el escenario más favorable a 1 en el más adverso.

**Tampoco lo resuelve el horizonte.** Con un repago mediano de 171 meses, en 5 años el alquiler devuelve el 35% del precio. El resto depende de revender la unidad, en un mercado donde en 2025 solo el 19,1% de las compraventas de la Ciudad se hizo con hipoteca: los compradores pagan con ahorros propios. Y vender lleva tiempo: en el 2do trimestre de 2026 un departamento en venta pasaba en promedio 298 días publicado, unos 9,8 meses (el máximo de la serie fue 425 días, en el 1er trimestre de 2024). Es el costo de salida que una obligación negociable no tiene. Es tiempo publicado, no tiempo de venta, y es de toda la Ciudad (Instituto de Estadística de la Ciudad, sobre avisos de Argenprop).

**Qué no dice:** que comprar sea un error. El KPI mide renta corriente y deja afuera la apreciación del inmueble, que un corte temporal único no permite estimar.

> **Decisión que cambia.** La pregunta deja de ser "¿en qué barrio compro?" y pasa a ser "¿compro o no?". Comprar para renta solo se justifica para las unidades cuya neta supera el piso de la banda con margen, o como una apuesta explícita a la revalorización, declarada como tal. Para la unidad típica, la alternativa de renta fija en dólares domina en retorno corriente, liquidez y riesgo de gestión.

## 2. Alquilar por noche no rescata la inversión

Se comparó el alquiler temporal contra el tradicional, **neta contra neta**, en 47 combinaciones de barrio y dormitorios con datos suficientes de los dos lados (Inside Airbnb y RE/MAX). En el temporal las expensas y los servicios los paga el dueño, y se suman comisión de plataforma, gestión, desgaste y amoblamiento.

Como la ocupación no se observa, la medida central es la **ocupación de equilibrio**, con la que el temporal empata al tradicional: mediana **65,3%** con gestión tercerizada (51,5% autogestionado) y nunca menos de 50,8%. La ocupación que estima Inside Airbnb para esas celdas tiene una mediana de 18,6%: con ella, el temporal le gana al tradicional en 0 de 47 celdas, con una neta mediana de -0,61%. Aun con el 53% de ocupación que informa la prensa, gana en 3.

> **Decisión que cambia.** El temporal no es la salida para mejorar la renta de la unidad típica. Solo se justifica si el inversor puede sostener una ocupación por encima del equilibrio de su barrio y su tipología, que en la mediana es mayor que la ocupación que publica la prensa para el mercado.

## 3. La cartera de RE/MAX publica más barato que el mercado: sus rentabilidades están del lado alto

Contra el precio publicado del m² que calcula el Instituto de Estadística de la Ciudad sobre avisos de Argenprop, en la misma celda de barrio, ambientes y estado, RE/MAX publica más barato en el 94% de las 135 celdas comparadas: -9,0% de desvío mediano en usados y -17,2% a estrenar. Contra el stock de departamentos del Censo 2022, la cartera sobrerrepresenta la comuna 1 y subrepresenta las comunas 4, 8 y 9: habría que reasignar el 7,2% de las ventas para replicar la composición de la Ciudad.

El precio está en el denominador de la rentabilidad. Si la unidad se comprara al precio publicado promedio del mercado y no al de la cartera, la neta mediana bajaría de 5,67% a alrededor de 5,22% (aplicando el desvío promedio ponderado de -8,0%), suponiendo que el alquiler no cambia. No hay fuente oficial para medir si la cartera de alquileres tiene el mismo sesgo, así que el efecto neto no se puede firmar.

> **Decisión que cambia.** Los niveles absolutos de rentabilidad del trabajo son los de la cartera de RE/MAX, no los de CABA, y probablemente están del lado alto: la brecha contra la renta fija del hallazgo 1 es, si algo, mayor. El inversor debe usar el análisis para **comparar** propiedades y barrios entre sí, no para prometerse una rentabilidad.

## 4. Elegir la propiedad pesa tanto como elegir el barrio

Entre el barrio que más rinde (Constitución) y el que menos (Palermo) hay 3,95 pp de rentabilidad bruta mediana. El rango intercuartil **dentro** de un solo barrio llega a 3,89 pp (Barracas), y el mediano es 2,18 pp. No es mezcla de tamaños: dentro de cada rango de superficie, la dispersión interna máxima de un barrio equivale a entre 72% y 164% de la distancia entre barrios.

Pero la estimación tiene su propio error, de 12,3% mediano: para el 41,7% de las propiedades, la banda de incertidumbre contiene la mediana del mercado, y su diferencia contra el promedio no se distingue del ruido.

> **Decisión que cambia.** "Comprá en tal barrio" no alcanza como criterio. El inversor tiene que comparar unidades concretas, y solo preferir una sobre otra cuando sus bandas de incertidumbre no se superponen. Si se superponen, la elección se decide por liquidez o por riesgo, no por el KPI.

## 5. Qué rinde más, comparando propiedades semejantes

Cada efecto se mide **dentro de celdas de barrio y rango de superficie**, para no atribuirle a un atributo lo que es diferencia de zona o de tamaño.

- **Metro cuadrado barato.** Los barrios con el m² más caro rinden menos (Spearman -0,903 sobre 29 barrios), y la relación se sostiene dentro de cada rango de superficie (de -0,949 a -0,876).
- **Fuera del corredor norte.** En el norte (comunas 2, 13 y 14) solo el 4,4% de las propiedades supera en neto el piso de las ON, contra el 25,6% en el centro y el 25,3% en el sur y oeste, con la oferta repartida en proporciones parecidas entre las tres zonas (30%, 39% y 31%).
- **Amenities.** Restan 0,55 pp de rentabilidad dentro del estrato (0,64 pp fijando también el tipo de propiedad), con diferencia negativa en el 74% de 122 celdas. Encarecen el m² un 23,5% y suben el alquiler por m² solo un 13,0%.
- **Unidades chicas.** Entre departamentos del mismo barrio, los de hasta 35 m² rinden +0,34 pp respecto de los de 81-120 m², y rinden más en el 72% de los 29 barrios comparables.
- **A reciclar.** Cotizan con un descuento de 23,3% en el m² respecto de propiedades comparables (negativo en el 100% de 35 celdas), y dejan +1,12 pp de rentabilidad bruta antes de descontar el costo del reciclaje, que el dataset no tiene.

> **Decisión que cambia.** Dentro del presupuesto, conviene buscar fuera del corredor norte e inclinarse por barrios de m² más barato, unidades chicas y edificios sin amenities, y mirar las unidades a reciclar como oportunidad solo si el costo de obra cabe en el descuento. Pagar amenities es una decisión de consumo, no de inversión. Las unidades chicas rotan más de inquilino: la vacancia uniforme del KPI 2 probablemente la subestima.

## 6. Estado de las hipótesis

Se evalúan por el tamaño del efecto dentro del estrato, sin p-valor. El contraste formal es alcance de la 3ra entrega, y el test que lo hará queda declarado.

| Hipótesis | Evidencia en esta entrega | Estado | Test formal (3ra entrega) |
|---|---|---|---|
| **H1.** La rentabilidad bruta cae con el precio del m² del barrio | Spearman -0,903 sobre 29 barrios; de -0,949 a -0,876 dentro de cada rango de superficie. La 1ra entrega daba -0,923: la diferencia la explican las dummies de RegEx (README) | Respaldada | Spearman unilateral con p-valor por permutación, repetido por tramo con corrección por comparaciones múltiples |
| **H2.** El precio del m² cae con la distancia al subte | No evaluable: requiere fusión espacial | Pendiente | Regresión del precio del m² sobre la distancia, con efectos fijos de barrio |
| **H3.** Los inmuebles a reciclar cotizan con descuento, y ese descuento es la oportunidad | Descuento de 23,3% en el m² en 35 celdas; +1,12 pp de rentabilidad bruta en 30 celdas | Respaldada, tentativa por la cantidad de celdas | Van Elteren (Mann-Whitney estratificado por celda) |
| **H4.** La antigüedad pesa más en el precio de venta que en el alquiler | Spearman antigüedad vs m² dentro del estrato: -0,552 en venta (117 celdas) contra -0,253 en alquiler (40 celdas), con antigüedad observada | Respaldada, tentativa por las pocas celdas de alquiler | Wald sobre la diferencia de coeficientes de dos regresiones (log precio y log alquiler) con efectos fijos de celda |

> **Decisión que cambia.** H1 y H4 describen el mismo mecanismo: el precio de compra se mueve más que el alquiler, y lo que abarata la compra (zona, antigüedad) sube la renta. Para un inversor que busca renta, lo viejo y lo periférico no son defectos a evitar sino la fuente del rendimiento, siempre que entre en su tolerancia de riesgo y liquidez.

## Lo que este informe no permite afirmar

- **Retorno total.** Solo se mide renta; la apreciación requiere una serie temporal.
- **Causalidad.** Comparar dentro del estrato controla por zona, tamaño y tipología, no por todo.
- **El mercado de CABA.** Se describe la cartera de una red inmobiliaria, con el sesgo del hallazgo 3.
- **Precios de cierre.** Todos los precios son de publicación, del lado de la venta y del alquiler.
- **Liquidez por propiedad.** El tiempo de publicación es un promedio de la Ciudad; el dataset es un corte único y no mide cuánto tarda en venderse cada unidad.

Los supuestos (vacancia, gastos, banda de retorno, horizonte, costos del temporal) están en `supuestos.py` con su fuente y fecha. El detalle de cada hallazgo está en `notebooks/03_eda.ipynb`, y las fuentes externas, en `informe/FUENTES_EXTERNAS.md`.
