import pandas as pd
import LanusStats as ls
import numpy as np
import json
import os
import gc
import utils_dataframe as utils

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

## player_stats dataframe
def extract_stats(file_path):
    '''
    Extrae los stats de cada miembro del equipo en homeCompetitor y awayCompetitor.
    
    Parámetro:
    - file_path (str): La ruta del archivo JSON.
    
    Retorna:
    - Una lista con todos los valores de la clave "name" encontrados en "stats".
    '''
    lista_categorias_especiales = ['barridas_ganadas', 'centros', 'duelos_aereos_ganados', 'pases_completados', 'pases_largos_completados', 'duelos_en_el_suelo_ganados', 'regates',"penales_atajados"]
    lista_categorias = utils.name_stats(file_path)
    player_stats = pd.DataFrame(columns=lista_categorias)
    # Cargar el archivo JSON
    with open(file_path, 'r') as f:
        data = json.load(f)

    # Acceder a homeCompetitor y awayCompetitor
    match_id = int(data.get('id'))
    for competitor in ['homeCompetitor', 'awayCompetitor']:
        if competitor in data:
            team_id = int(data[competitor].get('id'))
            members = data[competitor].get('lineups', {}).get("members", [])
            # Recorrer cada miembro en members
            for member in members:
                stats = member.get('stats', {})

                # Crear un diccionario temporal para almacenar las estadísticas del jugador
                player_data = dict.fromkeys(lista_categorias, 0)  # Inicializa todo en 0
                player_data['player_id'] = member.get('id')  # Añadir el player_id a la fila
                player_data["team_id"] = team_id
                player_data['match_id'] = match_id
                # Recorrer cada entrada en stats y extraer el valor
                for stat_data in stats:
                    total_stat_name = False
                    stat_name = utils.reemplazar(stat_data.get('name'))
                    stat_value = stat_data.get('value', 0)
                    player_data[stat_name] = stat_value

                    if stat_name in lista_categorias_especiales:
                        if isinstance(stat_value, str) and '/' in stat_value:
                            # Dividir el valor "x/y" en dos partes
                            values = stat_value.split('/')
                            try:
                                stat_value = int(values[0])  # Valor anterior al "/"
                                total_stat_value = int(values[1].split()[0])  # Valor posterior al "/"
                                total_stat_name = utils.reemplazar_categoria(stat_name) 
                            except ValueError:
                                stat_value = 0
                                total_stat_value = 0

                    # Asignar los valores a player_data
                    if stat_name in player_data:
                        player_data[stat_name] = stat_value
                        if total_stat_name:
                            player_data[total_stat_name] = total_stat_value
                    
                    if stat_name == 'minutes':
                        try:
                            stat_value = int(stat_value.replace("'", ""))
                        except ValueError:
                            stat_value = 0  # Asignar 0 si el valor no es convertible a entero

                    if stat_name == "goles":
                        stat_value = int(stat_value.split("(")[0])
                    player_data[stat_name] = stat_value

                player_df = pd.DataFrame([player_data])
                player_stats.fillna(0, inplace=True)     
                # Añadir la fila al DataFrame principal usando pd.concat
                player_stats = pd.concat([player_stats, player_df], ignore_index=True)   
    return player_stats

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

def dataframe_teams(folder_path, season_id):
    '''
        Applies the function teams and positions to all the files in a folder.
        parameter: folder (str).
        return: Dataframe.
    '''
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

    return df_concat_teams

# constructor de player dataframe (positions + players)

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

