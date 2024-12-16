import pymysql as sql
import os
import LanusStats as ls 
import json

scraper = ls.ThreeSixFiveScores()

connection = sql.connect(user='root', password="1104",host="localhost",database="football_project")

def extractor_data_match(competition_name, season_name, folder_path, matchday):
    """
    Procesa archivos .txt con nombres mayores al matchday y genera archivos JSON para los datos de los partidos.

    Parámetros:
    - competition_name (str): Nombre de la competición.
    - season_name (str): Nombre de la temporada.
    - folder_path (str): Ruta de la carpeta donde se encuentran los archivos .txt.
    - matchday (int): Matchday de referencia. Solo se procesan archivos con números mayores.

    Retorno:
    - None: Genera archivos JSON en las carpetas correspondientes.
    """
    # Recorrer los archivos en la carpeta
    for file_name in os.listdir(folder_path):
        # Intentar extraer el número del nombre del archivo
        try:
            file_matchday = int(os.path.splitext(file_name)[0])  # Extraer número antes del .txt
        except ValueError:
            # Si no es un número, ignorar el archivo
            continue

        if file_matchday > matchday and file_name.endswith('.txt'):
            file_path = os.path.join(folder_path, file_name)
            if os.path.isfile(file_path):
                try:
                    # Leer el archivo y procesar cada línea
                    with open(file_path, 'r') as reader:
                        output_folder = f"/home/sp3767/Documents/football_data/{competition_name}/{season_name}/match_data/{file_matchday}"
                        os.makedirs(output_folder, exist_ok=True)  # Crear la carpeta si no existe

                        id = 1
                        for line in reader:
                            output_file = os.path.join(output_folder, f"{id}.json")
                            match = scraper.get_match_data(line)
                            with open(output_file, 'w') as archivo:
                                json.dump(match, archivo, indent=4)  # Guardar en formato JSON
                                id += 1
                        print(f"la jornada {file_matchday} fue extraída exitosamente.")
                except Exception as e:
                    print(f"Error procesando {file_path}: {e}")


def folder_creation_competition(competition_id):
    ruta_carpeta = f'/home/sp3767/Documents/football_data/{competition_id}' 
    os.makedirs(ruta_carpeta, exist_ok=True)  # Crea la carpeta si no existe

def folder_creation_season(competition_id, season_name):
    ruta_carpeta = f'/home/sp3767/Documents/football_data/{competition_id}/{season_name}/jornadas'
    os.makedirs(ruta_carpeta, exist_ok=True)  # Crea la carpeta si no existe
    ruta_carpeta = f'/home/sp3767/Documents/football_data/{competition_id}/{season_name}/match_data'
    os.makedirs(ruta_carpeta, exist_ok=True)  # Crea la carpeta si no existe

## Utilidades:

def reemplazar(texto):
    """
    Reemplaza caracteres especiales y espacios en blanco por guiones bajos.
    Parametro: texto (str)
    Retorna: texto (str) con los caracteres reemplazados.
    """
    texto = texto.lower()
    texto = texto.replace("á", "a")
    texto = texto.replace("é", "e")
    texto = texto.replace("í", "i")
    texto = texto.replace("ó", "o")
    texto = texto.replace("ú", "u")
    texto = texto.replace("Á", "A")
    texto = texto.replace("É", "E")
    texto = texto.replace("Í", "I")
    texto = texto.replace("Ó", "O")
    texto = texto.replace("Ú", "U")
    texto = texto.replace("ñ", "n")
    texto = texto.replace("Ñ", "N")
    texto = texto.replace(" ", "_")
    texto = texto.replace("(", "")
    texto = texto.replace(")", "")
    return texto

def reemplazar_categoria(texto):
    texto = texto.replace("_ganadas","_totales")
    texto = texto.replace("centros","centros_totales")
    texto = texto.replace("_ganados","_totales")
    texto = texto.replace("_completados","_totales")
    texto = texto.replace("regates","regates_totales")
    texto = texto.replace("penales_atajados","penales_totales")
    return texto

def extract_stats_names(file_path):
    '''
    Extrae los valores bajo la clave "name" dentro de "stats" para cada miembro del equipo en homeCompetitor y awayCompetitor.
    
    Parámetro:
    - file_path (str): La ruta del archivo JSON.
    
    Retorna:
    - Una lista con todos los valores de la clave "name" encontrados en "stats".
    '''

    stats_names = []

    # Cargar el archivo JSON
    with open(file_path, 'r') as f:
        data = json.load(f)

    # Acceder a homeCompetitor y awayCompetitor
    for competitor in ['homeCompetitor', 'awayCompetitor']:
        if competitor in data:
            members = data[competitor].get('lineups', {}).get("members", [])
            # Recorrer cada miembro en members
            for member in members:
                stats = member.get('stats', {})
                # Recorrer cada entrada en stats y extraer el valor de "name"
                for stat_data in stats:
                    stat_name = stat_data.get('name')
                    stat_name = reemplazar(stat_name)
                    if stat_name:
                        stats_names.append(stat_name)

    return stats_names

def name_stats(folder_path):
    '''
        Applies the function teams and positions to all the files in a folder.
        parameter: folder (str).
        return: Dataframe.
    '''
    all_stats_names = set()
    for root, _, files in os.walk(folder_path):
        for file_name in files:
            if file_name.endswith('.json'):
                file_path = os.path.join(root, file_name)  # Ruta completa al archivo
                stats_names = extract_stats_names(file_path)
                all_stats_names.update(stats_names)
    final = ["player_id","match_id","barridas_totales","centros_totales", "duelos_aereos_totales","pases_totales","pases_largos_totales", "duelos_en_el_suelo_totales","regates_totales","penales_totales","match_id"]
    all_stats_names.update(final)
    final_list = list(all_stats_names)
    return sorted(final_list)

def filter_existing_players(connection, df):
    """
    Filtra el DataFrame para incluir solo registros donde (player_id, team_id) existe en la tabla `player`.
    """
    cursor = connection.cursor()
    query = "SELECT player_id, team_id FROM player"
    cursor.execute(query)
    existing_pairs = set(cursor.fetchall())  # Guardar todas las combinaciones (player_id, team_id) existentes
    cursor.close()

    # Filtrar el DataFrame para mantener solo los registros que existen en `existing_pairs`
    df_filtered = df[df[['player_id', 'team_id']].apply(tuple, axis=1).isin(existing_pairs)]
    
    return df_filtered