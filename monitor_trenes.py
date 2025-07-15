import requests
from google.transit import gtfs_realtime_pb2
import zipfile
import io
from rich.console import Console
from rich.table import Table
import unicodedata

import argparse

# URLs para los datos de FGC
FGC_GTFS_STATIC_URL = "https://www.fgc.cat/google/google_transit.zip"
FGC_GTFS_REALTIME_URL = "https://fgc.opendatasoft.com/api/explore/v2.1/catalog/datasets/trip-updates-gtfs_realtime/exports/json"

import csv

RODALIES_STATIONS_FILE = "rodalies_stations.csv"
rodalies_stations = {}

def normalize_string(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower()

def load_rodalies_stations():
    global rodalies_stations
    try:
        with open(RODALIES_STATIONS_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                rodalies_stations[normalize_string(row['DESCRIPCION'])] = row['CÓDIGO']
        print(f"Cargadas {len(rodalies_stations)} estaciones de Rodalies.")
    except FileNotFoundError:
        print(f"Info: El archivo {RODALIES_STATIONS_FILE} no se encontró. La búsqueda de estaciones de Rodalies no estará disponible.")
    except Exception as e:
        print(f"Error al cargar las estaciones de Rodalies: {e}")

def buscar_estaciones_adif(nombre_busqueda):
    """
    Busca estaciones de Rodalies en el archivo CSV local y muestra los resultados.
    """
    if not rodalies_stations:
        print("No se pudieron cargar las estaciones de Rodalies desde el archivo local.")
        return

    console = Console()
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Código", style="dim", width=12)
    table.add_column("Nombre")

    found_stations = []
    normalized_search = normalize_string(nombre_busqueda)

    for name, code in rodalies_stations.items():
        if normalized_search in name:
            found_stations.append({'code': code, 'name': name})
    
    if not found_stations:
        print(f"No se encontraron estaciones con el nombre '{nombre_busqueda}' en el archivo local.")
        return

    for station in found_stations:
        table.add_row(station['code'], station['name'].title())
    
    console.print(table)

def obtener_retrasos_fgc(id_parada):
    """
    Obtiene y muestra los retrasos de los trenes de FGC para una parada específica.
    """
    feed = gtfs_realtime_pb2.FeedMessage()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
    try:
        response_url_info = requests.get(FGC_GTFS_REALTIME_URL, headers=headers)
        response_url_info.raise_for_status()
        data = response_url_info.json()
        download_url = data[0]['file']['url']

        response = requests.get(download_url, headers=headers)
        response.raise_for_status()
        feed.ParseFromString(response.content)
    except requests.exceptions.RequestException as e:
        print(f"Error al descargar los datos en tiempo real de FGC: {e}")
        return

    retrasos = {}
    for entity in feed.entity:
        if entity.HasField('trip_update'):
            trip_id = entity.trip_update.trip.trip_id
            for update in entity.trip_update.stop_time_update:
                if update.HasField('departure') and update.departure.delay > 0:
                    retrasos[trip_id] = update.departure.delay
                    break

    print(f"Se encontraron {len(retrasos)} trenes con retraso en FGC.")
    try:
        response_static = requests.get(FGC_GTFS_STATIC_URL)
        response_static.raise_for_status()
        static_zip = zipfile.ZipFile(io.BytesIO(response_static.content))

        with static_zip.open('trips.txt') as f:
            trips_data = f.read().decode('utf-8')
        with static_zip.open('routes.txt') as f:
            routes_data = f.read().decode('utf-8')
        with static_zip.open('stop_times.txt') as f:
            stop_times_data = f.read().decode('utf-8')
        with static_zip.open('stops.txt') as f:
            stops_data = f.read().decode('utf-8')

    except requests.exceptions.RequestException as e:
        print(f"Error al descargar los datos estáticos de FGC: {e}")
        return
    except KeyError as e:
        print(f"Error: El archivo {e} no se encontró en el ZIP de FGC.")
        return

    stop_id_encontrado = None
    normalized_id_parada = normalize_string(id_parada)
    for line in stops_data.strip().splitlines():
        fields = line.strip().split(',')
        if len(fields) > 2 and normalized_id_parada in normalize_string(fields[2]):
            stop_id_encontrado = fields[3]
            print(f"ID de la parada '{fields[2]}' encontrado: {stop_id_encontrado}")
            break

    if not stop_id_encontrado:
        print(f"No se encontró ninguna parada con el nombre '{id_parada}'.")
        return

    trenes_en_parada = []
    for line in stop_times_data.strip().splitlines():
        fields = line.strip().split(',')
        if len(fields) > 3 and fields[3] == stop_id_encontrado:
            trip_id = fields[0]
            arrival_time = fields[1]
            departure_time = fields[2]
            
            detalles_viaje = {"trip_id": trip_id, "arrival_time": arrival_time, "departure_time": departure_time, "destino": "N/A", "linea": "N/A", "retraso_min": 0}
            
            for t_line in trips_data.strip().splitlines():
                t_fields = t_line.strip().split(',')
                if len(t_fields) > 2 and t_fields[2] == trip_id:
                    detalles_viaje["destino"] = t_fields[3] if len(t_fields) > 3 else "Sin destino"
                    route_id = t_fields[0]
                    for r_line in routes_data.strip().splitlines():
                        r_fields = r_line.strip().split(',')
                        if len(r_fields) > 2 and r_fields[0] == route_id:
                            detalles_viaje["linea"] = r_fields[2]
                            break
                    break
            
            if trip_id in retrasos:
                detalles_viaje["retraso_min"] = retrasos[trip_id] // 60
            
            trenes_en_parada.append(detalles_viaje)

    if not trenes_en_parada:
        print("No hay trenes programados para esta parada en este momento.")
        return

    console = Console()
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Línea", style="dim", width=12)
    table.add_column("Destino")
    table.add_column("Salida Programada")
    table.add_column("Retraso (min)", justify="right")

    for tren in trenes_en_parada:
        table.add_row(
            tren['linea'],
            tren['destino'],
            tren['departure_time'],
            str(tren['retraso_min'])
        )

    console.print(table)



def main_interactivo():
    while True:
        print("\nBienvenido al monitor de trenes.")
        print("¿Qué deseas hacer?")
        print("1. Consultar retrasos FGC")
        print("2. Buscar estación de Rodalies/Renfe")
        print("3. Salir")
        
        opcion = input("Elige una opción: ")

        if opcion == '1':
            id_parada_fgc = input("Introduce el nombre de la parada de FGC (ej: Plaça Catalunya): ")
            if id_parada_fgc:
                print(f"Consultando retrasos para la parada FGC: {id_parada_fgc}")
                obtener_retrasos_fgc(id_parada_fgc)
        elif opcion == '2':
            nombre_estacion = input("Introduce el nombre de la estación a buscar: ")
            if nombre_estacion:
                buscar_estaciones_adif(nombre_estacion)
        elif opcion == '3':
            print("Saliendo del monitor de trenes.")
            break
        else:
            print("Opción no válida. Por favor, elige una de las opciones.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor de trenes de FGC y Rodalies/Renfe.")
    parser.add_argument('--buscar', nargs='+', help='Busca el código de una estación de Renfe por su nombre.')
    
    args = parser.parse_args()

    load_rodalies_stations()

    if args.buscar:
        nombre_busqueda = " ".join(args.buscar)
        print(f"Buscando estaciones con el nombre: '{nombre_busqueda}'...")
        buscar_estaciones_adif(nombre_busqueda)
    else:
        main_interactivo()
