"""
Traduce el nombre comun de cada especie (viene en ingles en el
dataset original) y reescribe la columna nombre_comun de
especies.csv. Traduccion hecha a mano, sin API, asi que hay que
correrlo despues de preparar_especies_csv.py.
"""

import csv
import os

RUTA_CSV = os.path.join(
    os.path.dirname(__file__), "..", "servidor", "infraestructura", "especies.csv"
)

# especie (clave tal como queda en el CSV) -> nombre comun en espanol.
TRADUCCIONES = {
    "monstera deliciosa": "Costilla de Adan",
    "epipremnum aureum": "Potos dorado",
    "philodendron hederaceum": "Filodendro de hoja de corazon",
    "spathiphyllum wallisii": "Lirio de la paz",
    "anthurium andraeanum": "Anturio",
    "zamioculcas zamiifolia": "Planta ZZ",
    "aglaonema commutatum": "Siempreverde chino",
    "syngonium podophyllum": "Singonio",
    "dieffenbachia seguine": "Difenbaquia",
    "dracaena trifasciata": "Lengua de suegra",
    "chlorophytum comosum": "Cinta",
    "dracaena fragrans": "Tronco del Brasil",
    "yucca gigantea": "Yuca sin espinas",
    "beaucarnea recurvata": "Pata de elefante",
    "asparagus setaceus": "Helecho esparrago",
    "ficus lyrata": "Ficus lira",
    "ficus elastica": "Arbol del caucho",
    "ficus benjamina": "Ficus benjamina",
    "ficus pumila": "Higuera trepadora",
    "schlumbergera truncata": "Cactus de Navidad",
    "opuntia microdasys": "Nopal orejas de conejo",
    "kroenleinia grusonii": "Cactus bola de oro",
    "mammillaria hahniana": "Cactus viejita",
    "crassula ovata": "Arbol de jade",
    "echeveria elegans": "Bola de nieve mexicana",
    "sedum morganianum": "Cola de burro",
    "kalanchoe tomentosa": "Planta panda",
    "maranta leuconeura": "Planta oracion",
    "goeppertia insignis": "Calatea serpiente de cascabel",
    "peperomia obtusifolia": "Peperomia de hoja redonda",
    "peperomia argyreia": "Peperomia sandia",
    "streptocarpus ionanthus": "Violeta africana",
    "aeschynanthus radicans": "Planta del lapiz labial",
    "guzmania lingulata": "Bromelia estrella escarlata",
    "wallisia cyanea": "Bromelia pluma rosa",
    "ludisia discolor": "Orquidea joya",
    "nephrolepis exaltata": "Helecho de Boston",
    "platycerium bifurcatum": "Helecho cuerno de ciervo",
    "phlebodium aureum": "Helecho azul",
    "chamaedorea elegans": "Palmera de salon",
    "dypsis lutescens": "Palmera areca",
    "ravenea rivularis": "Palmera majestad",
    "begonia maculata": "Begonia lunares",
    "begonia rex-cultorum": "Begonia rex",
    "pilea peperomioides": "Planta china del dinero",
    "pilea involucrata": "Planta de la amistad",
    "euphorbia trigona": "Cactus africano de leche",
    "codiaeum variegatum": "Croton",
    "plectranthus verticillatus": "Hiedra sueca",
    "coleus scutellarioides": "Coleo",
    "hoya carnosa": "Flor de cera",
    "ceropegia woodii": "Collar de corazones",
    "hedera helix": "Hiedra comun",
    "tradescantia zebrina": "Amor de hombre",
    "tradescantia fluminensis": "Amor de hombre de hoja pequena",
    "oxalis triangularis": "Trebol morado",
    "aloe vera": "Sabila",
    "fittonia albivenis": "Fitonia",
    "hypoestes phyllostachya": "Planta polka dot",
    "bougainvillea glabra": "Buganvilia",
    "hibiscus rosa-sinensis": "Cayena",
    "pachira aquatica": "Arbol del dinero",
    "cyclamen persicum": "Ciclamen",
    "aphelandra squarrosa": "Planta cebra",
    "justicia brandegeeana": "Planta camaron",
    "ruellia makoyana": "Ruellia terciopelo",
    "strobilanthes auriculata dyeriana": "Escudo persa",
    "chamaedorea seifrizii": "Palmera bambu",
    "senecio macroglossus": "Hiedra de cera",
}


def traducir():
    with open(RUTA_CSV, newline="", encoding="utf-8") as archivo:
        filas = list(csv.DictReader(archivo))

    sin_traduccion = []
    for fila in filas:
        clave = fila["especie"]
        if clave in TRADUCCIONES:
            fila["nombre_comun"] = TRADUCCIONES[clave]
        else:
            sin_traduccion.append(clave)

    with open(RUTA_CSV, "w", newline="", encoding="utf-8") as archivo:
        columnas = list(filas[0].keys())
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerows(filas)

    print(f"Filas actualizadas: {len(filas)}")
    if sin_traduccion:
        print(f"Sin traduccion en el diccionario ({len(sin_traduccion)}):")
        for clave in sin_traduccion:
            print(f"  - {clave!r}")


if __name__ == "__main__":
    traducir()
