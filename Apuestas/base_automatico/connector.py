import pymysql as sql
import dataframe_builder as sc
import pandas as pd
from datetime import datetime
import json
import gc

with open('/home/sp3767/Documents/files/credentials.json') as f:
    config = json.load(f)

connection = sql.connect(
    user=config['DB_USER'],
    password=config['DB_PASSWORD'],
    host=config['DB_HOST'],
    database=config['DB_NAME']
    )

# Competition 

def insert_competitions(connection, league):
    # Paso 1: Formatear el nombre de la liga
    formatted_league = league.lower().replace(' ', '_')
    
    # Paso 2: Crear el cursor y la consulta SQL
    cursor = connection.cursor()
    insert_query = "INSERT INTO competition (competition_name) VALUES (%s)"
    
    try:
        # Paso 3: Ejecutar la consulta con el nombre formateado
        cursor.execute(insert_query, (formatted_league,))
        connection.commit()
        print(f"La liga '{formatted_league.replace('_', ' ').title()}' ha sido insertada correctamente.")
        
    except Exception as e:
        print(f"Error al insertar la liga: {e}")
    
    finally:
        cursor.close()

# Season 

def insert_season(connection, competition_id, season_name):
    cursor = connection.cursor()
    insert_query = """
    INSERT INTO season (competition_id, season_name)
    VALUES (%s, %s)
    """
    
    try:
        cursor.execute(insert_query, (competition_id, season_name))
        connection.commit()
        print(f"Se ha agregado la temporada {season_name} para la competencia con ID {competition_id}.")
        
    except Exception as e:
        print(f"Error al insertar la temporada: {e}")
    
    finally:
        cursor.close()
        print(f"Temporada '{season_name.replace('_', '/')}' ha sido creada exitosamente.")

# Teams
def insert_teams(connection, competition_name, season_name, season_id):
    """
    Inserta datos del DataFrame `teams` en la tabla `team` usando pymysql.

    Parámetros:
    - connection: Conexión a la base de datos usando pymysql.
    - teams: DataFrame de pandas que contiene los datos a insertar.
    """
    try:
        teams = sc.dataframe_teams((f"/home/sp3767/Documents/football_data/{competition_name}/{season_name}/match_data"), season_id)
        # Crear un cursor para realizar la inserción
        cursor = connection.cursor()

        # Crear la consulta de inserción
        insert_query = """
        INSERT INTO team (team_id, team_name, season_id)
        VALUES (%s, %s, %s)
        """

        # Convertir el DataFrame a una lista de tuplas para la inserción masiva
        data_to_insert = list(teams[['team_id', 'team_name', 'season_id']].itertuples(index=False, name=None))

        # Insertar los datos en la tabla
        cursor.executemany(insert_query, data_to_insert)
        connection.commit()

        print(f"{len(data_to_insert)} filas insertadas correctamente en la tabla 'team'.")

    except Exception as e:
        print(f"Error al insertar los datos: {e}")
        connection.rollback()  # Revertir los cambios en caso de error

    finally:
        cursor.close()  # Cerrar el cursor

# MatchDays

def insert_matchdays(connection, weeks, season_id):
    try:
        # Crear cursor
        cursor = connection.cursor()

        # Consulta SQL para insertar los datos
        insert_query = """
        INSERT INTO matchday (matchday_id, season_id)
        VALUES (%s, %s)
        """

        # Crear una lista con las jornadas
        matchdays = [(season_id * 50 + i, season_id) for i in range(1, weeks + 1)]

        # Inserción masiva usando executemany
        cursor.executemany(insert_query, matchdays)
        connection.commit()  # Hacer commit después de insertar

        print(f"{len(matchdays)} jornadas insertadas correctamente en la base de datos.")
    
    except Exception as e:
        print(f"Error al insertar las jornadas: {e}")
    
    finally:
        cursor.close()  # Cerrar el cursor

# Players.

def insert_players(connection, player_data):
    """
    Inserta un DataFrame en una tabla SQL. Maneja duplicados verificando los IDs existentes en la base de datos.
    
    Parámetros:
    - connection: Conexión a la base de datos.
    - player_data (pd.DataFrame): DataFrame a insertar.
    """
    # Crear un cursor
    cursor = connection.cursor()

    # Obtener IDs existentes
    existing_ids_query = "SELECT player_id FROM player"
    cursor.execute(existing_ids_query)
    existing_ids = set(row[0] for row in cursor.fetchall())

    # Filtrar el DataFrame para eliminar duplicados
    player_data = player_data[~player_data['player_id'].isin(existing_ids)]

    insert_query = """
    INSERT INTO player (team_id, player_id, player_name, jersey_number, position, season_id)  # Reemplaza con las columnas correctas
    VALUES (%s, %s, %s, %s, %s, %s)
    """

    try:
        for index, row in player_data.iterrows():
            try:
                cursor.execute(insert_query, (row['team_id'], row['player_id'], row['player_name'], row['jersey_number'], row['position'], row['season_id']))  # Ajusta según sea necesario
            except Exception as e:
                print(f"Error al insertar el jugador con ID {row['player_id']}: {e}")

        connection.commit()
        print(f"{len(player_data)} filas insertadas correctamente en la tabla players.")

    except Exception as e:
        print(f"Error general al insertar los datos: {e}")
        connection.rollback()

    finally:
        cursor.close()
        print("Cursor cerrado.")

def insert_player_stats(connection, dataframe):
    """
    Inserta los datos de un DataFrame en la tabla 'player_stats' de la base de datos,
    verificando previamente la existencia de registros y eliminando duplicados internos.

    Parámetros:
    - connection: Conexión a la base de datos usando pymysql.
    - dataframe: DataFrame de pandas que contiene los datos a insertar.
    """
    try:
        # Asegurarse de que NaNs son reemplazados con 0
        dataframe = dataframe.fillna(0)

        # Asegurarse de que la columna 'season_id' esté presente
        if 'season_id' not in dataframe.columns:
            raise ValueError("La columna 'season_id' no está presente en el DataFrame.")

        cursor = connection.cursor()

        # Obtener combinaciones válidas (player_id, team_id) de la tabla player
        cursor.execute("SELECT player_id, team_id FROM player")
        valid_players = set(cursor.fetchall())
        
        # Filtrar el DataFrame para conservar solo combinaciones válidas
        dataframe['key'] = list(zip(dataframe['player_id'], dataframe['team_id']))
        dataframe = dataframe[dataframe['key'].isin(valid_players)]
        dataframe.drop(columns=['key'], inplace=True)
        
        # Eliminar duplicados internos en el DataFrame basado en las claves primarias
        dataframe.drop_duplicates(subset=['player_id', 'team_id', 'match_id'], inplace=True)

        # Obtener registros ya existentes en la base de datos para evitar duplicados
        cursor.execute("SELECT player_id, team_id, match_id FROM player_stats")
        existing_stats = set(cursor.fetchall())
        
        # Filtrar filas en `dataframe` que no están en los registros existentes
        dataframe['key'] = list(zip(dataframe['player_id'], dataframe['team_id'], dataframe['match_id']))
        dataframe = dataframe[~dataframe['key'].isin(existing_stats)]
        dataframe.drop(columns=['key'], inplace=True)

        # Insertar filas si existen registros nuevos
        if not dataframe.empty:
            insert_query = """
            INSERT INTO player_stats (player_id, team_id, match_id, goles, asistencias, pases_claves, goles_recibidos, season_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            data_to_insert = dataframe[['player_id', 'team_id', 'match_id', 'goles', 'asistencias', 'pases_claves', 'goles_recibidos', 'season_id']].values.tolist()
            cursor.executemany(insert_query, data_to_insert)
            connection.commit()
            print(f"{len(data_to_insert)} filas insertadas correctamente en la tabla 'player_stats'.")
        else:
            print("No hay filas nuevas para insertar en 'player_stats'.")

    except sql.IntegrityError as ie:
        print("Error de integridad de datos (posiblemente un duplicado o falta de referencia). Detalles:", ie)
        connection.rollback()
    except Exception as e:
        print(f"Error al insertar los datos: {e}")
        connection.rollback()
    finally:
        cursor.close()

# Match Stats

def delete_season_data(connection, season_id):
    try:
        with connection.cursor() as cursor:
            delete_player_stats = """
            DELETE FROM player_stats
            WHERE match_id IN (
                SELECT match_id 
                FROM football_game
                WHERE matchday_id IN (
                    SELECT matchday_id
                    FROM matchday
                    WHERE season_id = %s
                )
            );
            """
            cursor.execute(delete_player_stats, (season_id,))

            delete_football_game = """
            DELETE FROM football_game
            WHERE matchday_id IN (
                SELECT matchday_id
                FROM matchday
                WHERE season_id = %s
            );
            """
            cursor.execute(delete_football_game, (season_id,))

            # Paso 3: Eliminar datos de player
            delete_player = """
            DELETE FROM player
            WHERE team_id IN (
                SELECT team_id
                FROM team
                WHERE season_id = %s
            );
            """
            cursor.execute(delete_player, (season_id,))

            connection.commit()
            print("Datos eliminados exitosamente para la temporada y competición especificadas.")
    
    except pymysql.MySQLError as e:
        # Si ocurre un error, hacer rollback y mostrar el error
        connection.rollback()
        print("Error al eliminar los datos:", e)

def insert_match_details(connection, dataframe):
    """
    Inserta un DataFrame en una tabla SQL. Maneja duplicados eliminándolos en el DataFrame 
    y utiliza inserciones individuales para evitar problemas con claves primarias duplicadas.
    
    Parámetros:
    - connection: Conexión a la base de datos.
    - dataframe (pd.DataFrame): DataFrame a insertar.
    """
    # Eliminar duplicados en el DataFrame basado en la clave primaria
    dataframe = dataframe.drop_duplicates(subset=["match_id"])

    # Crear un cursor
    cursor = connection.cursor()

    insert_query = """
    INSERT INTO football_game (match_id, matchday_id, home_team_id, away_team_id, home_score, away_score, duration , season_id )  # Reemplaza con las columnas correctas
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)  
    """

    try:
        # Convertir valores NaN a None para SQL
        dataframe = dataframe.where(pd.notnull(dataframe), None)

        for index, row in dataframe.iterrows():
            try:
                cursor.execute(insert_query, (row['match_id'], row['matchday_id'], row['home_team_id'], row['away_team_id'], row['home_score'], row['away_score'], row['duration'], row['season_id']))  # Ajusta las columnas según sea necesario
            except Exception as e:
                print(f"Error al insertar el partido con ID {row['match_id']}: {e}")
        
        connection.commit()  # Confirmar los cambios en la base de datos
        print("Todos los datos insertados correctamente en la tabla football_game.")

    except Exception as e:
        print(f"Error general al insertar los datos: {e}")
        connection.rollback()  # Revertir cambios en caso de error

    finally:
        cursor.close()
        print("Cursor cerrado.")

## Extraction functions

# Competition

def get_competitions(connection):
    cursor = connection.cursor()
    select_query = "SELECT * FROM competition"
    cursor.execute(select_query)
    leagues = cursor.fetchall()
    cursor.close()
    return list(leagues)

# Season
    
def get_seasons(connection, competition_id):
    ## PENDIENTE, POSIBLE BORRADO.
    cursor = connection.cursor()
    # Modificar la consulta para filtrar por competition_id
    select_query = "SELECT * FROM season WHERE competition_id = %s"
    # Ejecutar la consulta con el argumento competition_id
    cursor.execute(select_query, (competition_id,))
    seasons = cursor.fetchall()
    cursor.close()
    return list(seasons)
    
def update_season( connection, competition_name, season_name, season_id, matchday):
    cursor = connection.cursor()
    dataframe_players = sc.create_player_dataframe(competition_name, season_name, season_id, matchday)
    stats, match = sc.dataframe_stats_match(competition_name,season_name, season_id, matchday)
    insert_players(connection, dataframe_players)
    insert_match_details(connection, match) 
    insert_player_stats(connection, stats)
    cursor.close()
    del dataframe_players
    del stats
    del match
    gc.collect()

# Matchdays

def get_matchday(connection, season_id):
    cursor = connection.cursor()
    try:
        select_query = "SELECT matchday_id FROM matchday WHERE season_id = %s"
        cursor.execute(select_query, (season_id,))
        matchdays = cursor.fetchall()
        return [md[0] for md in matchdays]  # Extrae solo los IDs de matchday
    except Exception as e:
        print(f"Error al obtener matchdays: {e}")
        return []
    finally:
        cursor.close()

def get_matchday_information(connection, season_id):
    """
    Obtiene el último matchday registrado, su fecha de inserción más reciente,
    y calcula hace cuántos días se realizó la última actualización.

    Parámetros:
    - connection: Conexión a la base de datos.
    - season_id: ID de la temporada a consultar.

    Retorna:
    - Una tupla (matchday_id, last_insert_date, days_since_update) o (None, None, None) si no hay registros.
    """
    cursor = connection.cursor()
    query = """
    SELECT matchday_id, insert_date
    FROM football_game
    WHERE season_id = %s
    ORDER BY matchday_id DESC, insert_date DESC
    LIMIT 1;
    """
    cursor.execute(query, (season_id,))
    result = cursor.fetchone()
    cursor.close()
    
    if result:
        matchday_id, last_insert_date = result
        # Calcular la diferencia en días entre hoy y la última fecha de inserción
        last_insert_date = last_insert_date.date()  # Convertir a tipo `date` para comparación
        today = datetime.now().date()
        days_since_update = (today - last_insert_date).days
        return matchday_id, last_insert_date, days_since_update
    else:
        print(f"No se encontraron registros para la temporada con ID {season_id}.")
        return None, None, None