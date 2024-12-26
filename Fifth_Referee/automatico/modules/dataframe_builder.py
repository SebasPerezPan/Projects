import json
import os
import gc
from modules.utils_dataframe import name_stats, reemplazar, reemplazar_categoria, obtener_dataframe_liga, emparejar_equipos

import LanusStats as ls
import numpy as np
import pandas as pd

pd.set_option('display.max_columns', None)

scraper = ls.ThreeSixFiveScores()

def extract_football_game(file_path, season_id):

    """
    Builds the football_game dataframe with the match details.
    """
    match_details = pd.DataFrame(columns=['match_id', 'matchday_id', 'home_team_id', 'away_team_id', 'home_score', 'away_score', 'duration'])
    with open(file_path, 'r') as f:
        data = json.load(f)
        match_id = data.get("id")
        matchday_id = (data.get('roundNum')+ season_id * 50)
        home_team_id = data.get('homeCompetitor', {}).get('id')
        away_team_id = data.get('awayCompetitor', {}).get('id')
        home_score = int(data.get('homeCompetitor', {}).get('score'))       
        away_score = int(data.get('awayCompetitor', {}).get('score'))

        # Extraer duration desde actualPlayTime -> totalTime["name"]
        actual_play_time = data.get('actualPlayTime', {}).get("totalTime", {}).get('name', '')

        if actual_play_time:
            time_parts = actual_play_time.split(' ')[-1]  # Obtiene la parte de tiempo "99:06"
            minutes, seconds = map(int, time_parts.split(':'))  # Separa minutos y segundos
            duration = int(minutes + seconds / 60.0)  # Convierte a minutos con decimal
        else: 
            duration = int(data.get("gameTime"))
    match_details.loc[0] = [match_id, matchday_id, home_team_id, away_team_id, home_score, away_score, duration]
    return match_details

## player dataframe & team dataframe

# Constructor de positions y players dataframe. Players está perfecto.

def players(file):
    '''
    Extracts player_names, teams id, player id and jersey number from a matchday.
    parameter: text file. (str)
    return: Dataframe.
    '''
    df_concat = pd.DataFrame()
    with open(file, 'r') as reader:
        for line in reader:
            if line:
                match = scraper.get_players_info(line)
                df = pd.DataFrame(match)
                df = df.drop(df.columns[[2, 4, 6, 7]], axis=1)
                df_concat = pd.concat([df_concat, df], axis=0)
        reader.close()

    if 'jerseyNumber' in df_concat.columns:
        df_concat['jerseyNumber'].fillna(0)
        return df_concat

    else:
        print("Advertencia: 'jerseyNumber' no se encuentra en df_concat")
        return pd.DataFrame(columns=['competitorId', 'id', 'name', 'jerseyNumber'])

def dataframe_players(folder_path, matchday):
    '''
        Applies the function players_in_match to all the files in a folder.
        parameter: folder (str).
        return: Dataframe.
    '''
    df_concat = pd.DataFrame()

    for file_name in os.listdir(folder_path):        
        file_matchday = int(os.path.splitext(file_name)[0])  
        if file_matchday > matchday and file_name.endswith('.txt'):
            file_path = os.path.join(folder_path, file_name)
            if os.path.isfile(file_path):
                try:
                    player_data = players(file_path)
                    print(f"Dataframe {file_name} recorrido. ")
                    if not player_data.empty:
                        df_concat = pd.concat([df_concat, player_data], axis=0)
                except Exception as e:
                    print(f"Error procesando {file_path}: {e}")

    df_unique = df_concat.drop_duplicates(subset=['id'])
    df_unique.rename(columns={'competitorId': 'team_id'}, inplace=True)

    return df_unique

def positions (file_path):
    '''
    Extracts player_id, and position from a json file.
    parameter: json file. (str)
    return: Dataframe.
    '''
    positions_df = pd.DataFrame(columns=['id', 'position'])
    with open(file_path, 'r') as f:
        data = json.load(f)
        home_competitor = data.get('homeCompetitor', {})
        away_competitor = data.get('awayCompetitor', {})
        teams = [home_competitor, away_competitor]
        for team in teams:
            for player in team.get('lineups', {}).get('members', []):
                player_id = player.get('id')
                position = player.get('position', {}).get('shortName')
                if position == None:
                    position = "Couch"
                positions_df.loc[len(positions_df)] = [player_id, position]
    return positions_df
def extract_stats(file_path):
    """
    Extrae estadísticas de jugadores de cada equipo en homeCompetitor y awayCompetitor de un archivo JSON.

    Parámetro:
        - file_path (str): Ruta del archivo JSON.

    Retorna:
        - pd.DataFrame: Un DataFrame con estadísticas de jugadores.
    """
    # Categorías especiales y todas las posibles estadísticas
    lista_categorias_especiales = [
        'barridas_ganadas', 'centros', 'duelos_aereos_ganados',
        'pases_completados', 'pases_largos_completados',
        'duelos_en_el_suelo_ganados', 'regates', "penales_atajados"
    ]
    lista_categorias = name_stats(file_path) 
    lista_categorias.extend(lista_categorias_especiales)
    player_stats = pd.DataFrame(columns=lista_categorias)  # DataFrame principal

    # Cargar el archivo JSON
    with open(file_path, 'r') as f:
        data = json.load(f)

    match_id = int(data.get('id', 0))  # ID del partido
    for competitor in ['homeCompetitor', 'awayCompetitor']:
        if competitor in data:
            team_id = int(data[competitor].get('id', 0))  # ID del equipo
            members = data[competitor].get('lineups', {}).get("members", [])
            
            for member in members:
                player_data = dict.fromkeys(lista_categorias, 0)  # Inicializar con 0
                player_data.update({
                    'player_id': member.get('id'),
                    'team_id': team_id,
                    'match_id': match_id
                })

                stats = member.get('stats', [])
                for stat_data in stats:
                    stat_name = reemplazar(stat_data.get('name', ''))
                    stat_value = stat_data.get('value', 0)

                    if stat_name in lista_categorias_especiales and isinstance(stat_value, str) and '/' in stat_value:
                        try:
                            values = stat_value.split('/')
                            player_data[stat_name] = int(values[0])
                            player_data[reemplazar_categoria(stat_name)] = int(values[1].split()[0])
                        except ValueError:
                            player_data[stat_name] = 0
                            player_data[reemplazar_categoria(stat_name)] = 0
                    elif stat_name == 'minutes':
                        try:
                            player_data[stat_name] = int(stat_value.replace("'", ""))
                        except ValueError:
                            player_data[stat_name] = 0
                    elif stat_name == 'goles':
                        try:
                            player_data[stat_name] = int(stat_value.split("(")[0])
                        except ValueError:
                            player_data[stat_name] = 0
                    else:
                        try:
                            player_data[stat_name] = float(stat_value)
                        except ValueError:
                            player_data[stat_name] = 0

                # Crear DataFrame temporal y concatenar
                player_df = pd.DataFrame([player_data])
                player_stats = pd.concat([player_stats, player_df], ignore_index=True)
    with open("dataframe.csv" , "w") as writer:
        player_stats.to_csv(writer)
    return player_stats.fillna(0)  # Retornar DataFrame final

extract_stats("/home/sp3767/Documents/football_data/bundesliga/2024_2025/match_data/1/1.json")

# Constructor de team dataframe
def teams(file_path, season_id):
    '''
    Extracts football team names and ids from a file.
    parameter: json file. (str)
    return: Dataframe.
    '''
    teams_df = pd.DataFrame(columns=['team_id', 'team_name',"season_id"])
    with open(file_path, 'r') as f:
        data = json.load(f)
        home_competitor = data.get('homeCompetitor', {})
        away_competitor = data.get('awayCompetitor', {})
        home_id = int(home_competitor.get('id'))
        away_id = int(away_competitor.get('id'))
        home_team = str(home_competitor.get('name'))
        away_team = str(away_competitor.get('name'))
        teams_df.loc[len(teams_df)] = [home_id, home_team, season_id]
        teams_df.loc[len(teams_df)] = [away_id, away_team, season_id]

def teams(file_path, season_id):
    '''
    Extracts football team names and ids from a file.
    parameter: json file. (str)
    return: Dataframe.
    '''
    teams_df = pd.DataFrame(columns=['team_id', 'team_name', "season_id"])
    with open(file_path, 'r') as f:
        data = json.load(f)

        # Extraer datos de los equipos
        home_competitor = data.get('homeCompetitor', {})
        away_competitor = data.get('awayCompetitor', {})
        
        home_id = int(home_competitor.get('id', 0))  # Valor por defecto si no existe
        away_id = int(away_competitor.get('id', 0))
        home_team = str(home_competitor.get('name', 'Unknown'))
        away_team = str(away_competitor.get('name', 'Unknown'))
        
        teams_df.loc[len(teams_df)] = [home_id, home_team, season_id]
        teams_df.loc[len(teams_df)] = [away_id, away_team, season_id]
        
        # Obtener league_name de forma segura
        league_name = data.get('competitionDisplayName', None)
        
        if isinstance(league_name, str):  # Solo procesar si es una cadena
            league_name = league_name.split()[-1]
        else:
            print(f"Clave 'competitionDisplayName' no es una cadena en el archivo {file_path}")
            league_name = "Unknown"

    return teams_df


# Teams and positions Check if they work:
 
def dataframe_positions(folder_path, matchday):
    '''
        Applies the function positions to all the files in a folder.
        parameter: folder (str).
        return: Dataframe.
    '''
    df_concat_positions = pd.DataFrame()

    # Recorrer las carpetas en el directorio base
    for folder_name in sorted(os.listdir(folder_path)):
        try:
            # Intentar convertir el nombre de la carpeta en un entero
            folder_matchday = int(folder_name)
        except ValueError:
            # Si no es un número, ignorar esta carpeta
            continue

        # Procesar solo carpetas cuyo matchday sea mayor al dado
        if folder_matchday > matchday:
            folder_full_path = os.path.join(folder_path, folder_name)
            
            if os.path.isdir(folder_full_path):
                # Recorrer los archivos JSON en la carpeta
                for file_name in os.listdir(folder_full_path):
                    if file_name.endswith('.json'):
                        file_path = os.path.join(folder_full_path, file_name)
                        try:
                            # Procesar el archivo JSON
                            position_data = positions(file_path)
                            df_concat_positions = pd.concat([df_concat_positions, position_data], axis=0)
                        except Exception as e:
                            print(f"Error procesando {file_path}: {e}")

    # Eliminar duplicados basado en el ID del equipo
    df_concat_positions.drop_duplicates(subset=['id'], inplace=True)
    return df_concat_positions

def dataframe_teams(folder_path, season_id, league_name):
    '''
    Processes all JSON files in a folder to extract team information,
    updates city and stadium data with matched team names, and merges both DataFrames.

    Parameters:
        folder_path (str): Path to the folder containing JSON files.
        season_id (int): Season ID for the data being processed.
        league_name (str): Name of the league for API lookup.

    Returns:
        pd.DataFrame: Final merged DataFrame with team_id, team_name, season_id, city, and stadium.
    '''
    # Paso 1: Crear DataFrame vacío y extraer equipos desde archivos JSON
    df_concat_teams = pd.DataFrame()

    for root, _, files in os.walk(folder_path):
        for file_name in files:
            if file_name.endswith('.json'):
                file_path = os.path.join(root, file_name)
                try:
                    team_data = teams(file_path, season_id)
                    df_concat_teams = pd.concat([df_concat_teams, team_data], axis=0)
                except Exception as e:
                    print(f"Error procesando {file_path}: {e}")

    df_concat_teams.drop_duplicates(subset=['team_id'], inplace=True)
    df_city_stadium = obtener_dataframe_liga(league_name.replace("_", " "))
    matches = emparejar_equipos(df_city_stadium, df_concat_teams, "team", "team_name")

    team_name_mapping = dict(zip(matches['team'], matches['team_name']))
    df_city_stadium = df_city_stadium.rename(columns={"team": "team_name"})
    df_city_stadium['team_name'] = df_city_stadium['team_name'].replace(team_name_mapping)
    # Paso 4: Fusionar los DataFrames actualizados
    df_teams = pd.merge(
        df_concat_teams, 
        df_city_stadium, 
        on="team_name", 
        how="left"
    )
    df_teams = df_teams.drop_duplicates(subset=['team_id', 'season_id'])
    return df_teams

def create_player_dataframe(competition_name, season_name, season_id, matchday):
    try:
        # Obtener los DataFrames de posiciones y jugadores
        positions = dataframe_positions(f"/home/sp3767/Documents/football_data/{competition_name}/{season_name}/match_data", matchday)
        players = dataframe_players(f'/home/sp3767/Documents/football_data/{competition_name}/{season_name}/jornadas', matchday)
        # Comprobar que ambos DataFrames tienen la columna 'id'
        if 'id' not in positions.columns:
            raise KeyError("El DataFrame 'positions' no contiene la columna 'id'.")
        if 'id' not in players.columns:
            raise KeyError("El DataFrame 'players' no contiene la columna 'id'.")

        # Merge de DataFrames
        player_df = pd.merge(players, positions, on='id', how='left')
        player_df['season_id'] = season_id

        # Renombrar columnas para adaptarse al esquema de la base de datos
        player_df.rename(columns={
            'id': 'player_id',
            'jerseyNumber': 'jersey_number',
            'name': 'player_name',
            "competitorId": "team_id"
        }, inplace=True)

        # Manejo de valores nulos y conversión de columnas relevantes a enteros
        player_df = player_df.where(pd.notnull(player_df), None)
        player_df[['team_id', 'player_id', 'jersey_number', "season_id"]] = (
            player_df[['team_id', 'player_id', 'jersey_number', "season_id"]]
            .fillna(0)
            .astype(int)
        )

        # Eliminar duplicados basados en la columna clave primaria
        player_df = player_df.drop_duplicates(subset=['player_id'])
        print("Dataframe de players creado con éxito.")
        del players
        del positions
        gc.collect()

        return player_df

    except KeyError as ke:
        print(f"Error clave faltante: {ke}")
        return None
    except Exception as e:
        print(f"Error al crear el DataFrame de players: {e}")
        return None
#match details and player stats

def dataframe_stats_match(competition_name, season_name, season_id, matchday):
    """
    Recolecta datos de estadísticas de partidos y partidos de fútbol desde carpetas numeradas mayores al matchday dado.
    
    Parámetros:
    - folder_path (str): Ruta base donde se encuentran las carpetas numeradas por matchday.
    - season_id (int): ID de la temporada.
    - matchday (int): Matchday de referencia. Solo se procesarán carpetas con nombres mayores a este número.

    Retorno:
    - tuple: DataFrames (df_concat_match_stats, df_concat_football_game).
    """
    df_concat_match_stats = pd.DataFrame()
    df_concat_football_game = pd.DataFrame()
    folder_path = f"/home/sp3767/Documents/football_data/{competition_name}/{season_name}/match_data"
    # Recorrer las carpetas en el directorio base
    for folder_name in sorted(os.listdir(folder_path)):
        try:
            # Intentar convertir el nombre de la carpeta en un entero
            folder_matchday = int(folder_name)
        except ValueError:
            # Si no es un número, ignorar esta carpeta
            continue

        # Procesar solo carpetas cuyo matchday sea mayor al dado
        if folder_matchday > matchday:
            folder_full_path = os.path.join(folder_path, folder_name)

            if os.path.isdir(folder_full_path):
                # Recorrer los archivos JSON en la carpeta
                for file_name in os.listdir(folder_full_path):
                    if file_name.endswith('.json'):
                        file_path = os.path.join(folder_full_path, file_name)
                        try:
                            # Procesar datos de fútbol y estadísticas del partido
                            football_game = extract_football_game(file_path, season_id)
                            match_stats = extract_stats(file_path)

                            df_concat_football_game = pd.concat([df_concat_football_game, football_game], axis=0)
                            df_concat_match_stats = pd.concat([df_concat_match_stats, match_stats], axis=0)
                        except Exception as e:
                            print(f"Error procesando {file_path}: {e}")

    # Añadir el ID de la temporada a los DataFrames
    df_concat_football_game["season_id"] = season_id
    df_concat_match_stats["season_id"] = season_id

    return df_concat_match_stats, df_concat_football_game

