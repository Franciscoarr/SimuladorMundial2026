import pandas as pd
import random
import csv
import math

# --- 1. CARGAR DATOS DESDE EL CSV ---
def cargar_elos(ruta_csv, emit=print):
    emit("Cargando CSV...")
    df = pd.read_csv(ruta_csv)
    
    # Ordenamos por fecha para asegurarnos de que el último registro sea el más actual
    df = df.sort_values(by="date")
    
    # Extraemos el último ELO registrado para cada equipo y lo pasamos a un diccionario
    diccionario_elo = df.groupby("team")["elo"].last().to_dict()
    return diccionario_elo


def guardar_resumen_torneo(registro, ruta_salida):
    # Exporta un resumen limpio para no repetir toda la salida de consola en el CSV
    with open(ruta_salida, "w", newline="", encoding="utf-8-sig") as archivo:
        escritor = csv.DictWriter(
            archivo,
            fieldnames=["orden", "fase", "fecha", "sede", "estadio", "equipo_a", "goles_a", "goles_b", "equipo_b", "nota"]
        )
        escritor.writeheader()
        escritor.writerows(registro)

# --- 2. CLASE EQUIPO ---
class Equipo:
    def __init__(self, nombre, grupo, diccionario_elos):
        self.nombre = nombre
        self.grupo = grupo
        # Usa el ELO del CSV; si falta el equipo, se le asigna uno por defecto
        self.elo = diccionario_elos.get(nombre, 1500)
        
        # Estadísticas que se actualizarán durante el torneo
        self.puntos = 0
        self.gf = 0 # Goles a favor
        self.gc = 0 # Goles en contra
        
    @property
    def dif_goles(self):
        return self.gf - self.gc

# --- 3. EL MOTOR DEL PARTIDO ---
def _mu_goles(equipo_favor, equipo_contra, es_eliminatoria=False):
    # La fuerza relativa del ELO mueve un poco la media de goles esperada
    base = 1.15 if es_eliminatoria else 1.35
    ajuste = (equipo_favor.elo - equipo_contra.elo) / 900
    return max(0.2, min(base + ajuste, 3.8))


def _poisson(lam):
    # Generador Poisson simple sin dependencias externas
    limite = math.exp(-lam)
    producto = 1.0
    goles = 0

    while producto > limite:
        goles += 1
        producto *= random.random()

    return goles - 1


def _elegir_resultado_por_elo(equipo_a, equipo_b, es_eliminatoria=False):
    prob_a_ganar = 1 / (1 + 10 ** ((equipo_b.elo - equipo_a.elo) / 400))

    if es_eliminatoria:
        return random.choices(["A", "B"], weights=[prob_a_ganar, 1 - prob_a_ganar])[0]

    prob_empate = max(0.12, min(0.30, 0.30 - abs(prob_a_ganar - 0.5) * 0.4))
    prob_a = (1 - prob_empate) * prob_a_ganar
    prob_b = (1 - prob_empate) * (1 - prob_a_ganar)
    return random.choices(["A", "Empate", "B"], weights=[prob_a, prob_empate, prob_b])[0]


def _marcador_con_elo(equipo_a, equipo_b, resultado, es_eliminatoria=False):
    mu_a = _mu_goles(equipo_a, equipo_b, es_eliminatoria)
    mu_b = _mu_goles(equipo_b, equipo_a, es_eliminatoria)

    for _ in range(12):
        goles_a = _poisson(mu_a)
        goles_b = _poisson(mu_b)

        if resultado == "A" and goles_a > goles_b:
            return goles_a, goles_b
        if resultado == "B" and goles_b > goles_a:
            return goles_a, goles_b
        if resultado == "Empate" and goles_a == goles_b:
            return goles_a, goles_b

    if resultado == "A":
        goles_b = random.randint(0, 2)
        goles_a = goles_b + random.randint(1, 3)
        return goles_a, goles_b
    if resultado == "B":
        goles_a = random.randint(0, 2)
        goles_b = goles_a + random.randint(1, 3)
        return goles_a, goles_b

    goles = random.choices([0, 1, 2], weights=[45, 40, 15])[0]
    return goles, goles


def simular_partido(equipo_a, equipo_b, es_eliminatoria=False):
    """Usa ELO para decidir el resultado y Poisson para construir el marcador."""

    resultado = _elegir_resultado_por_elo(equipo_a, equipo_b, es_eliminatoria=es_eliminatoria)
    return _marcador_con_elo(equipo_a, equipo_b, resultado, es_eliminatoria=es_eliminatoria)

# --- 4. LA LÓGICA DEL MUNDIAL 2026 ---
def jugar_mundial():
    registro_resumen = []

    def emit(texto=""):
        linea = str(texto)
        print(linea)

    def registrar_evento(fase, fecha="", sede="", estadio="", equipo_a="", goles_a="", goles_b="", equipo_b="", nota=""):
        # Cada evento se guarda ya estructurado para poder exportarlo luego a CSV
        registro_resumen.append(
            {
                "orden": len(registro_resumen) + 1,
                "fase": fase,
                "fecha": fecha,
                "sede": sede,
                "estadio": estadio,
                "equipo_a": equipo_a,
                "goles_a": goles_a,
                "goles_b": goles_b,
                "equipo_b": equipo_b,
                "nota": nota,
            }
        )

    def separador(titulo):
        # Mejora la lectura de la consola agrupando bloques grandes
        emit("")
        emit("=" * 90)
        emit(titulo.center(90))
        emit("=" * 90)
        emit("")

    # 1. Cargamos el CSV que subiste
    diccionario_elos = cargar_elos("datos_selecciones.csv", emit=emit)
    
    # Plantilla fija de 48 selecciones repartidas en 12 grupos
    equipos_raw = [
        ("Mexico", "A"), ("South Africa", "A"), ("South Korea", "A"), ("Czech Republic", "A"),
        ("Canada", "B"), ("Bosnia and Herzegovina", "B"), ("Qatar", "B"), ("Switzerland", "B"),
        ("Brazil", "C"), ("Morocco", "C"), ("Haiti", "C"), ("Scotland", "C"),
        ("United States", "D"), ("Paraguay", "D"), ("Australia", "D"), ("Turkey", "D"),
        ("Germany", "E"), ("Curaçao", "E"), ("Ivory Coast", "E"), ("Ecuador", "E"),
        ("Netherlands", "F"), ("Japan", "F"), ("Sweden", "F"), ("Tunisia", "F"),
        ("Belgium", "G"), ("Egypt", "G"), ("Iran", "G"), ("New Zealand", "G"),
        ("Spain", "H"), ("Cape Verde", "H"), ("Saudi Arabia", "H"), ("Uruguay", "H"),
        ("France", "I"), ("Senegal", "I"), ("Iraq", "I"), ("Norway", "I"),
        ("Argentina", "J"), ("Algeria", "J"), ("Austria", "J"), ("Jordan", "J"),
        ("Portugal", "K"), ("DR Congo", "K"), ("Uzbekistan", "K"), ("Colombia", "K"),
        ("England", "L"), ("Croatia", "L"), ("Ghana", "L"), ("Panama", "L")
    ]
    
    # Convertimos la lista de texto en Objetos "Equipo"
    equipos = [Equipo(nombre, grupo, diccionario_elos) for nombre, grupo in equipos_raw]
    equipos_por_nombre = {equipo.nombre: equipo for equipo in equipos}

    # Calendario oficial de la fase de grupos, partido por partido
    fixtures_grupos = {
        "A": [
            ("11 de junio de 2026", "Ciudad de México", "Estadio Azteca", "Mexico", "South Africa"),
            ("11 de junio de 2026", "Guadalajara", "Estadio Akron", "South Korea", "Czech Republic"),
            ("18 de junio de 2026", "Atlanta", "Mercedes-Benz Stadium", "Czech Republic", "South Africa"),
            ("18 de junio de 2026", "Guadalajara", "Estadio Akron", "Mexico", "South Korea"),
            ("24 de junio de 2026", "Ciudad de México", "Estadio Azteca", "Czech Republic", "Mexico"),
            ("24 de junio de 2026", "Monterrey", "Estadio BBVA", "South Africa", "South Korea"),
        ],
        "B": [
            ("12 de junio de 2026", "Toronto", "BMO Field", "Canada", "Bosnia and Herzegovina"),
            ("13 de junio de 2026", "San Francisco", "Levi's Stadium", "Qatar", "Switzerland"),
            ("18 de junio de 2026", "Los Ángeles", "SoFi Stadium", "Switzerland", "Bosnia and Herzegovina"),
            ("18 de junio de 2026", "Vancouver", "BC Place", "Canada", "Qatar"),
            ("24 de junio de 2026", "Vancouver", "BC Place", "Switzerland", "Canada"),
            ("24 de junio de 2026", "Seattle", "Lumen Field", "Bosnia and Herzegovina", "Qatar"),
        ],
        "C": [
            ("13 de junio de 2026", "Nueva York/Nueva Jersey", "MetLife Stadium", "Brazil", "Morocco"),
            ("13 de junio de 2026", "Boston", "Gillette Stadium", "Haiti", "Scotland"),
            ("19 de junio de 2026", "Filadelfia", "Lincoln Financial Field", "Brazil", "Haiti"),
            ("19 de junio de 2026", "Boston", "Gillette Stadium", "Scotland", "Morocco"),
            ("24 de junio de 2026", "Miami", "Hard Rock Stadium", "Scotland", "Brazil"),
            ("24 de junio de 2026", "Atlanta", "Mercedes-Benz Stadium", "Morocco", "Haiti"),
        ],
        "D": [
            ("12 de junio de 2026", "Los Ángeles", "SoFi Stadium", "United States", "Paraguay"),
            ("13 de junio de 2026", "Vancouver", "BC Place", "Australia", "Turkey"),
            ("19 de junio de 2026", "San Francisco", "Levi's Stadium", "Turkey", "Paraguay"),
            ("19 de junio de 2026", "Seattle", "Lumen Field", "United States", "Australia"),
            ("25 de junio de 2026", "Los Ángeles", "SoFi Stadium", "Turkey", "United States"),
            ("25 de junio de 2026", "San Francisco", "Levi's Stadium", "Paraguay", "Australia"),
        ],
        "E": [
            ("14 de junio de 2026", "Houston", "NRG Stadium", "Germany", "Curaçao"),
            ("14 de junio de 2026", "Filadelfia", "Lincoln Financial Field", "Ivory Coast", "Ecuador"),
            ("20 de junio de 2026", "Toronto", "BMO Field", "Germany", "Ivory Coast"),
            ("20 de junio de 2026", "Kansas City", "Arrowhead Stadium", "Ecuador", "Curaçao"),
            ("25 de junio de 2026", "Nueva York/Nueva Jersey", "MetLife Stadium", "Ecuador", "Germany"),
            ("25 de junio de 2026", "Filadelfia", "Lincoln Financial Field", "Curaçao", "Ivory Coast"),
        ],
        "F": [
            ("14 de junio de 2026", "Dallas", "AT&T Stadium", "Netherlands", "Japan"),
            ("14 de junio de 2026", "Monterrey", "Estadio BBVA", "Sweden", "Tunisia"),
            ("20 de junio de 2026", "Houston", "NRG Stadium", "Netherlands", "Sweden"),
            ("20 de junio de 2026", "Monterrey", "Estadio BBVA", "Tunisia", "Japan"),
            ("25 de junio de 2026", "Dallas", "AT&T Stadium", "Japan", "Sweden"),
            ("25 de junio de 2026", "Kansas City", "Arrowhead Stadium", "Tunisia", "Netherlands"),
        ],
        "G": [
            ("15 de junio de 2026", "Seattle", "Lumen Field", "Belgium", "Egypt"),
            ("15 de junio de 2026", "Los Ángeles", "SoFi Stadium", "Iran", "New Zealand"),
            ("21 de junio de 2026", "Los Ángeles", "SoFi Stadium", "Belgium", "Iran"),
            ("21 de junio de 2026", "Vancouver", "BC Place", "New Zealand", "Egypt"),
            ("26 de junio de 2026", "Vancouver", "BC Place", "New Zealand", "Belgium"),
            ("26 de junio de 2026", "Seattle", "Lumen Field", "Egypt", "Iran"),
        ],
        "H": [
            ("15 de junio de 2026", "Atlanta", "Mercedes-Benz Stadium", "Spain", "Cape Verde"),
            ("15 de junio de 2026", "Miami", "Hard Rock Stadium", "Saudi Arabia", "Uruguay"),
            ("21 de junio de 2026", "Atlanta", "Mercedes-Benz Stadium", "Spain", "Saudi Arabia"),
            ("21 de junio de 2026", "Miami", "Hard Rock Stadium", "Uruguay", "Cape Verde"),
            ("26 de junio de 2026", "Guadalajara", "Estadio Akron", "Uruguay", "Spain"),
            ("26 de junio de 2026", "Houston", "NRG Stadium", "Cape Verde", "Saudi Arabia"),
        ],
        "I": [
            ("16 de junio de 2026", "Nueva York/Nueva Jersey", "MetLife Stadium", "France", "Senegal"),
            ("16 de junio de 2026", "Boston", "Gillette Stadium", "Iraq", "Norway"),
            ("22 de junio de 2026", "Nueva York/Nueva Jersey", "MetLife Stadium", "Norway", "Senegal"),
            ("22 de junio de 2026", "Filadelfia", "Lincoln Financial Field", "France", "Iraq"),
            ("26 de junio de 2026", "Boston", "Gillette Stadium", "Norway", "France"),
            ("26 de junio de 2026", "Toronto", "BMO Field", "Senegal", "Iraq"),
        ],
        "J": [
            ("16 de junio de 2026", "Kansas City", "Arrowhead Stadium", "Argentina", "Algeria"),
            ("16 de junio de 2026", "San Francisco", "Levi's Stadium", "Austria", "Jordan"),
            ("22 de junio de 2026", "Dallas", "AT&T Stadium", "Argentina", "Austria"),
            ("22 de junio de 2026", "San Francisco", "Levi's Stadium", "Jordan", "Algeria"),
            ("27 de junio de 2026", "Dallas", "AT&T Stadium", "Jordan", "Argentina"),
            ("27 de junio de 2026", "Kansas City", "Arrowhead Stadium", "Algeria", "Austria"),
        ],
        "K": [
            ("17 de junio de 2026", "Houston", "NRG Stadium", "Portugal", "DR Congo"),
            ("17 de junio de 2026", "Ciudad de México", "Estadio Azteca", "Uzbekistan", "Colombia"),
            ("23 de junio de 2026", "Houston", "NRG Stadium", "Portugal", "Uzbekistan"),
            ("23 de junio de 2026", "Guadalajara", "Estadio Akron", "Colombia", "DR Congo"),
            ("27 de junio de 2026", "Miami", "Hard Rock Stadium", "Colombia", "Portugal"),
            ("27 de junio de 2026", "Atlanta", "Mercedes-Benz Stadium", "DR Congo", "Uzbekistan"),
        ],
        "L": [
            ("17 de junio de 2026", "Dallas", "AT&T Stadium", "England", "Croatia"),
            ("17 de junio de 2026", "Toronto", "BMO Field", "Ghana", "Panama"),
            ("23 de junio de 2026", "Boston", "Gillette Stadium", "England", "Ghana"),
            ("23 de junio de 2026", "Toronto", "BMO Field", "Panama", "Croatia"),
            ("27 de junio de 2026", "Nueva York/Nueva Jersey", "MetLife Stadium", "Panama", "England"),
            ("27 de junio de 2026", "Filadelfia", "Lincoln Financial Field", "Croatia", "Ghana"),
        ],
    }
    
    separador("FASE DE GRUPOS")
    
    clasificados_primeros = []
    clasificados_segundos = []
    terceros = []
    posicion_por_equipo = {}
    
    letras_grupos = "ABCDEFGHIJKL"
    for letra in letras_grupos:
        equipos_grupo = [e for e in equipos if e.grupo == letra]
        emit(f"GRUPO {letra}".center(90, "-"))
        emit("")
        
        for fecha, sede, estadio, nombre_a, nombre_b in fixtures_grupos[letra]:
            eq_a = equipos_por_nombre[nombre_a]
            eq_b = equipos_por_nombre[nombre_b]
            ga, gb = simular_partido(eq_a, eq_b, es_eliminatoria=False)

            emit(f"{fecha}  |  {sede}  |  {estadio}")
            emit(f"   {eq_a.nombre:<22} {ga} - {gb} {eq_b.nombre}")
            emit("")
            registrar_evento(
                fase=f"Grupo {letra}",
                fecha=fecha,
                sede=sede,
                estadio=estadio,
                equipo_a=eq_a.nombre,
                goles_a=ga,
                goles_b=gb,
                equipo_b=eq_b.nombre,
                nota=f"Jornada del Grupo {letra}",
            )
                
            # Sumamos goles
            eq_a.gf += ga; eq_a.gc += gb
            eq_b.gf += gb; eq_b.gc += ga
            
            # Sumamos puntos
            if ga > gb: eq_a.puntos += 3
            elif gb > ga: eq_b.puntos += 3
            else: eq_a.puntos += 1; eq_b.puntos += 1
                
        # Desempate FIFA: puntos, diferencia de goles y goles a favor
        equipos_grupo.sort(key=lambda x: (x.puntos, x.dif_goles, x.gf), reverse=True)
        
        # Guardamos en listas para la siguiente fase
        clasificados_primeros.append(equipos_grupo[0])
        clasificados_segundos.append(equipos_grupo[1])
        terceros.append(equipos_grupo[2])
        posicion_por_equipo[equipos_grupo[0].nombre] = f"1º{letra}"
        posicion_por_equipo[equipos_grupo[1].nombre] = f"2º{letra}"
        posicion_por_equipo[equipos_grupo[2].nombre] = f"3º{letra}"
        posicion_por_equipo[equipos_grupo[3].nombre] = f"4º{letra}"
        
        emit(f"Clasificación final del Grupo {letra}")
        emit(f"  1º {equipos_grupo[0].nombre:<22} {equipos_grupo[0].puntos:>2} pts | DG {equipos_grupo[0].dif_goles:+d} | GF {equipos_grupo[0].gf}")
        emit(f"  2º {equipos_grupo[1].nombre:<22} {equipos_grupo[1].puntos:>2} pts | DG {equipos_grupo[1].dif_goles:+d} | GF {equipos_grupo[1].gf}")
        emit(f"  3º {equipos_grupo[2].nombre:<22} {equipos_grupo[2].puntos:>2} pts | DG {equipos_grupo[2].dif_goles:+d} | GF {equipos_grupo[2].gf}")
        emit(f"  4º {equipos_grupo[3].nombre:<22} {equipos_grupo[3].puntos:>2} pts | DG {equipos_grupo[3].dif_goles:+d} | GF {equipos_grupo[3].gf}")
        emit("")
        registrar_evento(
            fase=f"Cierre Grupo {letra}",
            nota=(
                f"1º {equipos_grupo[0].nombre}; 2º {equipos_grupo[1].nombre}; "
                f"3º {equipos_grupo[2].nombre}; 4º {equipos_grupo[3].nombre}"
            ),
        )
        
    # Solo los 8 mejores terceros pasan a la siguiente ronda
    terceros.sort(key=lambda x: (x.puntos, x.dif_goles, x.gf), reverse=True)
    mejores_terceros = terceros[:8]
    emit("MEJORES TERCEROS CLASIFICADOS".center(90, "-"))
    for indice, equipo in enumerate(mejores_terceros, start=1):
        emit(f"{indice:02d}. {equipo.nombre:<22} ({posicion_por_equipo[equipo.nombre]}) | {equipo.puntos} pts | DG {equipo.dif_goles:+d} | GF {equipo.gf}")
    emit("")
    registrar_evento(
        fase="Mejores terceros",
        nota="; ".join(
            f"{indice}. {equipo.nombre} ({posicion_por_equipo[equipo.nombre]})"
            for indice, equipo in enumerate(mejores_terceros, start=1)
        ),
    )
    
    separador("FASE ELIMINATORIA")
    
    primeros_por_grupo = {equipo.grupo: equipo for equipo in clasificados_primeros}
    segundos_por_grupo = {equipo.grupo: equipo for equipo in clasificados_segundos}
    terceros_por_grupo = {equipo.grupo: equipo for equipo in mejores_terceros}
    ganadores_por_partido = {}
    perdedores_por_partido = {}

    def resolver_por_etiqueta(etiqueta, terceros_usados):
        # Interpreta etiquetas oficiales como 1A, 2B o 3A/B/C/D/F
        if etiqueta.startswith("1"):
            grupo = etiqueta[1:]
            return primeros_por_grupo[grupo]
        if etiqueta.startswith("2"):
            grupo = etiqueta[1:]
            return segundos_por_grupo[grupo]

        grupos_permitidos = etiqueta[1:].split("/")
        for grupo in grupos_permitidos:
            equipo = terceros_por_grupo.get(grupo)
            if equipo is not None and equipo.nombre not in terceros_usados:
                terceros_usados.add(equipo.nombre)
                return equipo

        # Si la combinación exacta no está disponible, tomamos el mejor tercero aún libre
        for equipo in mejores_terceros:
            if equipo.nombre not in terceros_usados:
                terceros_usados.add(equipo.nombre)
                return equipo

        raise ValueError(f"No se pudo resolver el tercer puesto para {etiqueta}")

    def resolver_referencia(referencia, terceros_usados=None):
        if isinstance(referencia, Equipo):
            return referencia

        if referencia.startswith("Ganador "):
            return ganadores_por_partido[int(referencia.split()[1])]
        if referencia.startswith("Perdedor "):
            return perdedores_por_partido[int(referencia.split()[1])]
        if referencia.startswith("1") or referencia.startswith("2"):
            return resolver_por_etiqueta(referencia, terceros_usados if terceros_usados is not None else set())
        if referencia.startswith("3"):
            return resolver_por_etiqueta(referencia, terceros_usados if terceros_usados is not None else set())

        return equipos_por_nombre[referencia]

    def jugar_ronda(ronda, nombre_ronda):
        emit(f"{nombre_ronda}".center(90, "-"))
        emit("")
        ganadores = []
        perdedores = []
        # Solo en dieciseisavos se muestra el puesto de grupo junto al país
        mostrar_posicion_grupo = nombre_ronda == "DIECISEISAVOS"
        terceros_usados_ronda = set() if mostrar_posicion_grupo else None

        for partido in ronda:
            fecha, sede, estadio, dato_a, dato_b, numero_partido = partido
            eq_a = resolver_referencia(dato_a, terceros_usados_ronda)
            eq_b = resolver_referencia(dato_b, terceros_usados_ronda)
            prefijo = f"{fecha} - {sede} - {estadio}: "
            etiqueta_a = (
                f"{eq_a.nombre} ({posicion_por_equipo.get(eq_a.nombre, eq_a.nombre)})"
                if mostrar_posicion_grupo
                else eq_a.nombre
            )
            etiqueta_b = (
                f"{eq_b.nombre} ({posicion_por_equipo.get(eq_b.nombre, eq_b.nombre)})"
                if mostrar_posicion_grupo
                else eq_b.nombre
            )

            ga, gb = simular_partido(eq_a, eq_b, es_eliminatoria=True)

            if ga > gb:
                ganador, perdedor = eq_a, eq_b
            else:
                ganador, perdedor = eq_b, eq_a

            emit(f"{prefijo}{etiqueta_a} [{ga} - {gb}] {etiqueta_b}")
            emit("")
            registrar_evento(
                fase=nombre_ronda,
                fecha=fecha,
                sede=sede,
                estadio=estadio,
                equipo_a=eq_a.nombre,
                goles_a=ga,
                goles_b=gb,
                equipo_b=eq_b.nombre,
                nota=f"{nombre_ronda} - partido {numero_partido}",
            )
            ganadores.append(ganador)
            perdedores.append(perdedor)
            ganadores_por_partido[numero_partido] = ganador
            perdedores_por_partido[numero_partido] = perdedor

        return ganadores, perdedores

    dieciseisavos = [
        ("28 de junio de 2026", "Los Ángeles", "SoFi Stadium", "2A", "2B", 73),
        ("29 de junio de 2026", "Boston", "Gillette Stadium", "1E", "3A/B/C/D/F", 74),
        ("29 de junio de 2026", "Monterrey", "Estadio Monterrey", "1F", "2C", 75),
        ("29 de junio de 2026", "Houston", "NRG Stadium", "1C", "2F", 76),
        ("30 de junio de 2026", "Nueva York/Nueva Jersey", "MetLife Stadium", "1I", "3C/D/F/G/H", 77),
        ("30 de junio de 2026", "Dallas", "AT&T Stadium", "2E", "2I", 78),
        ("30 de junio de 2026", "Ciudad de México", "Estadio Azteca", "1A", "3C/E/F/H/I", 79),
        ("1 de julio de 2026", "Atlanta", "Mercedes-Benz Stadium", "1L", "3E/H/I/J/K", 80),
        ("1 de julio de 2026", "San Francisco", "Levi's Stadium", "1D", "3B/E/F/I/J", 81),
        ("1 de julio de 2026", "Seattle", "Lumen Field", "1G", "3A/E/H/I/J/L", 82),
        ("2 de julio de 2026", "Toronto", "Estadio Nacional de Canadá", "2K", "2L", 83),
        ("2 de julio de 2026", "Los Ángeles", "SoFi Stadium", "1H", "2J", 84),
        ("2 de julio de 2026", "Vancouver", "BC Place", "1B", "3E/F/G/I/J", 85),
        ("3 de julio de 2026", "Miami", "Hard Rock Stadium", "1J", "2H", 86),
        ("3 de julio de 2026", "Kansas City", "Arrowhead Stadium", "1K", "3D/E/I/J/L", 87),
        ("3 de julio de 2026", "Dallas", "AT&T Stadium", "2D", "2G", 88),
    ]

    ganadores, _ = jugar_ronda(dieciseisavos, "DIECISEISAVOS")
    octavos = [
        ("4 de julio de 2026", "Filadelfia", "Lincoln Financial Field", "Ganador 74", "Ganador 77", 89),
        ("4 de julio de 2026", "Houston", "NRG Stadium", "Ganador 73", "Ganador 75", 90),
        ("5 de julio de 2026", "Nueva York/Nueva Jersey", "MetLife Stadium", "Ganador 76", "Ganador 78", 91),
        ("5 de julio de 2026", "Ciudad de México", "Estadio Azteca", "Ganador 79", "Ganador 80", 92),
        ("6 de julio de 2026", "Dallas", "AT&T Stadium", "Ganador 83", "Ganador 84", 93),
        ("6 de julio de 2026", "Seattle", "Lumen Field", "Ganador 81", "Ganador 82", 94),
        ("7 de julio de 2026", "Atlanta", "Mercedes-Benz Stadium", "Ganador 86", "Ganador 88", 95),
        ("7 de julio de 2026", "Vancouver", "BC Place", "Ganador 85", "Ganador 87", 96),
    ]

    ganadores, _ = jugar_ronda(octavos, "OCTAVOS DE FINAL")
    cuartos = [
        ("9 de julio de 2026", "Boston", "Gillette Stadium", "Ganador 89", "Ganador 90", 97),
        ("10 de julio de 2026", "Los Ángeles", "SoFi Stadium", "Ganador 93", "Ganador 94", 98),
        ("11 de julio de 2026", "Miami", "Hard Rock Stadium", "Ganador 91", "Ganador 92", 99),
        ("11 de julio de 2026", "Kansas City", "Arrowhead Stadium", "Ganador 95", "Ganador 96", 100),
    ]

    ganadores, _ = jugar_ronda(cuartos, "CUARTOS DE FINAL")
    semifinales = [
        ("14 de julio de 2026", "Dallas", "AT&T Stadium", "Ganador 97", "Ganador 98", 101),
        ("15 de julio de 2026", "Atlanta", "Mercedes-Benz Stadium", "Ganador 99", "Ganador 100", 102),
    ]

    finalistas, semifinalistas_perdedores = jugar_ronda(semifinales, "SEMIFINALES")

    tercer_partido = [("18 de julio de 2026", "Miami", "Hard Rock Stadium", "Perdedor 101", "Perdedor 102", 103)]
    ganadores_tercer_puesto, perdedores_tercer_puesto = jugar_ronda(tercer_partido, "TERCER PUESTO")
    tercero = ganadores_tercer_puesto[0]
    cuarto = perdedores_tercer_puesto[0]

    final_partido = [("19 de julio de 2026", "Nueva York/Nueva Jersey", "MetLife Stadium", "Ganador 101", "Ganador 102", 104)]
    ganadores_final, perdedores_final = jugar_ronda(final_partido, "FINAL")
    campeon = ganadores_final[0]
    subcampeon = perdedores_final[0]

    separador("PODIO FINAL")
    emit(f"🏆 CAMPEÓN DEL MUNDO 2026: {campeon.nombre.upper()} 🏆")
    emit(f"1º {campeon.nombre}")
    emit(f"2º {subcampeon.nombre}")
    emit(f"3º {tercero.nombre}")
    emit("")
    registrar_evento(
        fase="Podio",
        nota=f"1º {campeon.nombre}; 2º {subcampeon.nombre}; 3º {tercero.nombre}",
    )

    guardar_resumen_torneo(registro_resumen, "resumen_torneo_mundial2026.csv")
    emit("Resumen guardado en resumen_torneo_mundial2026.csv")

# Punto de entrada de Python
if __name__ == "__main__":
    jugar_mundial()