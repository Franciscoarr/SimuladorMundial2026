# Simulador del Mundial 2026

Script en Python que simula de principio a fin la Copa Mundial de la FIFA 2026: fase de grupos completa, fase eliminatoria con el nuevo formato de 48 equipos, y un resumen exportable a CSV con todos los resultados. La fuerza de cada selección se basa en su rating Elo real (cargado desde un CSV), y los marcadores se generan con un modelo de Poisson ponderado por esa fuerza relativa.

## Qué hace, en resumen

1. Carga los ratings Elo más recientes de 48 selecciones desde un archivo CSV
2. Construye los 12 grupos (A–L) con 4 equipos cada uno y juega los 6 partidos de cada grupo (todos contra todos).
3. Calcula la clasificación de cada grupo y determina los 2 primeros de cada uno, más los 8 mejores terceros de los 12 grupos
4. Juega el cuadro eliminatorio completo: dieciseisavos, octavos, cuartos, semifinales, partido por el tercer puesto y final
5. Imprime en consola un relato partido a partido con fecha, sede y estadio
6. Exporta un resumen estructurado de todo el torneo a `resumen_torneo_mundial2026.csv`

## Requisitos

- Python 3.x
- [pandas](https://pandas.pydata.org/) (`pip install pandas`)
- Módulos estándar ya incluidos en Python: `random`, `csv`, `math`

## Archivo de entrada: `df_gemaldini.csv`

El script espera, en el mismo directorio, un CSV histórico de ratings Elo con (al menos) estas columnas:

| columna | descripción |
|---|---|
| `date` | fecha del registro de Elo |
| `team` | nombre del equipo (debe coincidir con los nombres usados en el script, en inglés, p. ej. `Spain`, `Argentina`) |
| `elo` | valor numérico del rating Elo en esa fecha |

`cargar_elos()` ordena el CSV por fecha y se queda con el **último valor de Elo registrado por equipo** (`groupby("team")["elo"].last()`), es decir, el más actual. Si una de las 48 selecciones del torneo no aparece en el CSV, se le asigna un Elo por defecto de **1500**.

## Los 48 equipos y los 12 grupos

Los equipos y grupos están fijados directamente en el código (lista `equipos_raw`):

| Grupo | Equipos |
|---|---|
| A | México, Sudáfrica, Corea del Sur, República Checa |
| B | Canadá, Bosnia y Herzegovina, Catar, Suiza |
| C | Brasil, Marruecos, Haití, Escocia |
| D | Estados Unidos, Paraguay, Australia, Turquía |
| E | Alemania, Curazao, Costa de Marfil, Ecuador |
| F | Países Bajos, Japón, Suecia, Túnez |
| G | Bélgica, Egipto, Irán, Nueva Zelanda |
| H | España, Cabo Verde, Arabia Saudita, Uruguay |
| I | Francia, Senegal, Irak, Noruega |
| J | Argentina, Argelia, Austria, Jordania |
| K | Portugal, RD Congo, Uzbekistán, Colombia |
| L | Inglaterra, Croacia, Ghana, Panamá |

Cada grupo tiene también su propio calendario fijo (`fixtures_grupos`), con fecha, ciudad sede y estadio para cada uno de los 6 partidos de la fase de grupos, replicando el calendario tipo del Mundial 2026 en Estados Unidos, Canadá y México.

## El motor de simulación de partidos

La generación de cada marcador ocurre en dos pasos independientes: primero se decide **quién gana** usando Elo, y después se construye un **marcador realista** para ese resultado usando una distribución de Poisson. Esto evita el problema típico de simular goles de forma totalmente independiente, donde el favorito puede "perder" el partido por azar incluso teniendo muchísima más probabilidad.

### 1. Decidir el resultado (`_elegir_resultado_por_elo`)

Se usa la fórmula logística estándar de Elo para la probabilidad de victoria:

```
prob_a_ganar = 1 / (1 + 10^((elo_b - elo_a) / 400))
```

- En partidos de **eliminatoria** (`es_eliminatoria=True`) solo se sortea entre "A" o "B" con esa probabilidad; no hay empates, ya que en la realidad se resolverían en la prórroga o penaltis.
- En la **fase de grupos** se calcula además una probabilidad de empate acotada entre 0.12 y 0.30: cuanto más parejos son los equipos en Elo, más alta es la probabilidad de empate. El resto de la probabilidad se reparte entre "A" y "B" manteniendo la proporción original.

### 2. Construir el marcador (`_mu_goles`, `_poisson`, `_marcador_con_elo`)

- `_mu_goles` calcula el número esperado de goles (λ) de cada equipo: una base de 1.35 en fase de grupos o 1.15 en eliminatoria (los partidos de eliminación directa se modelan algo más cerrados/cautelosos), ajustada por la diferencia de Elo entre los dos equipos dividida entre 900, y siempre acotada entre 0.2 y 3.8.
- `_poisson` es una implementación propia del muestreo de Poisson (algoritmo de Knuth), sin depender de numpy/scipy.
- `_marcador_con_elo` muestrea goles para ambos equipos hasta 12 veces, buscando un marcador que sea coherente con el resultado ya decidido en el paso 1 (por ejemplo, si se decidió que gana el equipo A, repite el muestreo hasta obtener `goles_a > goles_b`). Si tras 12 intentos no lo consigue, fuerza un marcador plausible a mano (un gol de diferencia o más para el ganador, o el mismo número de goles bajo para un empate).

`simular_partido()` combina ambos pasos y es la función que se llama para cada partido del torneo.

## Fase de grupos

Para cada uno de los 12 grupos:

- Se juegan los 6 partidos del calendario fijo, sumando puntos (3-1-0), goles a favor y goles en contra a cada `Equipo`.
- Al terminar, los equipos se ordenan por el criterio de desempate: **puntos → diferencia de goles → goles a favor**. Nota: es una versión simplificada del desempate oficial FIFA, no incluye enfrentamiento directo, fair play ni sorteo.
- Se guardan el 1º y 2º de cada grupo, y el 3º entra en la bolsa de "mejores terceros".

Terminados los 12 grupos, se comparan los 12 equipos que quedaron terceros y se seleccionan los **8 mejores** (mismo criterio de desempate), tal como exige el formato real de 48 equipos.

## Fase eliminatoria

El cuadro de dieciseisavos usa etiquetas de posición en lugar de nombres de equipo fijos, igual que en un bracket real:

- `1A`, `2B`, etc. → ganador o segundo del grupo correspondiente.
- `3A/B/C/D/F` → el mejor tercero disponible entre los grupos listados que sí haya clasificado entre los 8 mejores terceros. Si ninguno de los grupos indicados clasificó, la función `resolver_por_etiqueta` cae de vuelta al mejor tercero que todavía no haya sido asignado a otro cruce.

A partir de octavos de final, los cruces ya no usan etiquetas de grupo sino referencias al resultado de partidos anteriores: `"Ganador 73"`, `"Perdedor 101"`, etc., resueltas por `resolver_referencia` contra los diccionarios `ganadores_por_partido` / `perdedores_por_partido` que se van llenando partido a partido.

La progresión completa es:

1. **Dieciseisavos de final** — 16 partidos
2. **Octavos de final** — 8 partidos
3. **Cuartos de final** — 4 partidos
4. **Semifinales** — 2 partidos
5. **Partido por el tercer puesto** — entre los perdedores de semifinales
6. **Final** — entre los ganadores de semifinales

Todos estos partidos se juegan con `es_eliminatoria=True`, así que siempre hay un ganador (sin empates).

## Resultado final

Al terminar la final, el script imprime el podio (campeón, subcampeón y tercer puesto) en consola.

## Salida: `resumen_torneo_mundial2026.csv`

Cada evento relevante del torneo (cada partido, el cierre de cada grupo, la lista de mejores terceros y el podio final) se va guardando en una lista interna y, al final, `guardar_resumen_torneo()` la exporta a CSV con codificación `utf-8-sig` (para que los acentos se vean bien en Excel). Columnas del archivo:

| columna | contenido |
|---|---|
| `orden` | número secuencial del evento |
| `fase` | etapa del torneo (`Grupo A`, `Cierre Grupo A`, `Mejores terceros`, `DIECISEISAVOS`, `OCTAVOS DE FINAL`, `CUARTOS DE FINAL`, `SEMIFINALES`, `TERCER PUESTO`, `FINAL`, `Podio`...) |
| `fecha` | fecha del partido (vacío en eventos de resumen) |
| `sede` | ciudad sede |
| `estadio` | estadio |
| `equipo_a` / `equipo_b` | equipos enfrentados |
| `goles_a` / `goles_b` | marcador |
| `nota` | texto descriptivo adicional (clasificaciones, referencia al número de partido, etc.) |

## Cómo ejecutarlo

```bash
pip install pandas
python simulador_mundial.py
```

Asegúrate de tener `datos_selecciones.csv` en el mismo directorio que el script antes de ejecutarlo. Al terminar encontrarás `resumen_torneo_mundial2026.csv` junto al script.

## Personalización

- **Cambiar las fuerzas de los equipos**: edita o sustituye `datos_selecciones.csv` con otros valores de Elo.
- **Cambiar equipos o grupos**: modifica la lista `equipos_raw` y el diccionario `fixtures_grupos` (debes mantener la coherencia entre ambos: cada equipo debe tener su grupo y sus 6 partidos correspondientes).
- **Repetir la simulación**: el script no fija una semilla aleatoria (`random.seed`), así que cada ejecución produce un Mundial distinto. Si quieres resultados reproducibles, añade `random.seed(numero)` al principio de `jugar_mundial()`.

## Resultados de 10.000 simulaciones
 
Para tener una idea de qué tan bien refleja el modelo las fuerzas reales de cada selección, se ejecutó el torneo completo **10.000 veces** con `simular_multiples_mundiales` (Se puede modificar el valor en `TOTAL_SIMULACIONES`) y se contó cuántas veces resultó campeón cada equipo. Estos son los resultados:
 
| País | Veces campeón | Porcentaje |
|---|---|---|
| SPAIN | 2394 | 23.94% |
| ARGENTINA | 1811 | 18.11% |
| FRANCE | 1332 | 13.32% |
| ENGLAND | 545 | 5.45% |
| BRAZIL | 462 | 4.62% |
| PORTUGAL | 433 | 4.33% |
| NETHERLANDS | 404 | 4.04% |
| COLOMBIA | 356 | 3.56% |
| ECUADOR | 352 | 3.52% |
| GERMANY | 347 | 3.47% |
| CROATIA | 267 | 2.67% |
| TURKEY | 171 | 1.71% |
| URUGUAY | 167 | 1.67% |
| SWITZERLAND | 165 | 1.65% |
| BELGIUM | 132 | 1.32% |
| MEXICO | 107 | 1.07% |
| JAPAN | 103 | 1.03% |
| NORWAY | 78 | 0.78% |
| PARAGUAY | 70 | 0.70% |
| MOROCCO | 69 | 0.69% |
| AUSTRIA | 48 | 0.48% |
| SENEGAL | 38 | 0.38% |
| SOUTH KOREA | 27 | 0.27% |
| CANADA | 22 | 0.22% |
| IRAN | 19 | 0.19% |
| AUSTRALIA | 17 | 0.17% |
| SWEDEN | 13 | 0.13% |
| CZECH REPUBLIC | 11 | 0.11% |
| PANAMA | 8 | 0.08% |
| SCOTLAND | 8 | 0.08% |
| UNITED STATES | 5 | 0.05% |
| ALGERIA | 5 | 0.05% |
| UZBEKISTAN | 5 | 0.05% |
| EGYPT | 3 | 0.03% |
| IVORY COAST | 2 | 0.02% |
| DR CONGO | 2 | 0.02% |
| JORDAN | 1 | 0.01% |
| IRAQ | 1 | 0.01% |

## Limitaciones conocidas

- El desempate de grupo es una simplificación (puntos, diferencia de goles, goles a favor) y no incluye enfrentamiento directo, fair play ni sorteo, criterios que sí usa la FIFA en caso de triple empate exacto.
- Las etiquetas de "mejor tercero" (`3A/B/C/D/F`, etc.) replican la lógica del bracket oficial de 48 equipos, pero si ninguno de los grupos listados clasifica entre los 8 mejores terceros, el script asigna el mejor tercero libre disponible en su lugar, en vez de replicar exactamente la tabla oficial de combinaciones FIFA.
- Cualquier selección que no esté en `datos_selecciones.csv` arranca el torneo con un Elo neutral de 1500.