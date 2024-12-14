import pymysql as sql
import csv
import os
import json

connection = sql.connect(user='root', password="1104",host="localhost",database="football_competition")


cursor = connection.cursor()

def insert_players_from_csv(file_path):
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  
        for row in reader:
            player_id, player_name, team_name, jersey_number = row  # Ensure CSV has all columns
            query = """
                INSERT INTO player (player_id, player_name, team_name, jersey_number)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (player_id, player_name, team_name, jersey_number))
    
    connection.commit()
    print("Datos de Players insertados correctamente.")

# insert_players_from_csv('/home/sp3767/Practice/Python/Projects/Apuestas/datos/jornadas/jornada6.csv')

# with connection.cursor() as cursor:
# #         # Insertar datos en la tabla MatchDay
#     for week_number in range(1, 39):  # Semana 1 a 38
#           season_id = 1  # Establecemos season_id como 1 para todos
#           query = "INSERT INTO matchDay (week_number, season_id) VALUES (%s, %s)"
#           cursor.execute(query, (week_number, season_id))
#           connection.commit()
#           print("Datos de MatchDay insertados correctamente.")

# finally:
#     connection.close()

# # Cerrar la conexión
# cursor.close()
# connection.close()
def football_match (file_path, x, footballMatch_id):
    with open(file_path, 'r') as f:
        data = json.load(f)

    # Extraer team_home, team_away, home_score, away_score
    home_competitor = data.get('homeCompetitor', {})
    away_competitor = data.get('awayCompetitor', {})

    team_home = str(home_competitor.get('name'))
    team_away = str(away_competitor.get('name'))
    home_score = int(home_competitor.get('score'))
    away_score = int(away_competitor.get('score'))

    duration = 0

    # Extraer duration desde actualPlayTime -> totalTime["name"]
    actual_play_time = data.get('actualPlayTime', {})
    total_time_str = actual_play_time.get('totalTime', {}).get('name', '')

    if total_time_str:
        time_parts = total_time_str.split(' ')[-1]  # Obtiene la parte de tiempo "99:06"
        minutes, seconds = map(int, time_parts.split(':'))  # Separa minutos y segundos
        duration = int(minutes + seconds / 60.0)  # Convierte a minutos con decimal
    query = """
                INSERT INTO footballMatch (footballMatch_id, matchday_id, team_home, team_away, home_score, away_score, duration)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
    cursor.execute(query,(footballMatch_id, x, team_home, team_away, home_score, away_score, duration))
    
    connection.commit()
    print("Datos de FootballMatch han insertados correctamente.")
    
    def extract_player_stats(team, footballMatch_id):
        for player in team.get('lineups', {}).get('members', []):
            player_id = player.get('id')

            # Extraer estadísticas desde stats
            stats = player.get('stats', {})
            stat_values = []
            for i in range(27):  # Del 0 al 26
                stat_values.append(stats.get(str(i), {}).get('value', 0))  # Obtener el valor o 0 si no existe

            # Insertar los datos de stats en la tabla playerStats usando footballMatch_id
            query_stats = """
                INSERT INTO playerStats (footballMatch_id, player_id,  minutes_played, saves, goals, assists, goals_received, total_shots, offsides, assists_expected, passes_key, 
                                         passes_third, passes_back, passes_completed, passes_long, touch, fouls_received, goals_expected_ontarget, goals_expected_prevented, fouls_commited, possesion_lost, 
                                         stat_19, stat_20, stat_21, stat_22, stat_23, stat_24, stat_25, stat_26)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query_stats, (footballMatch_id, player_id,  *stat_values))
            connection.commit()

    # Extraer y procesar jugadores para homeCompetitor y awayCompetitor
    extract_player_stats(home_competitor, footballMatch_id)
    extract_player_stats(away_competitor, footballMatch_id)

    print(f"Datos de PlayerStats han sido insertados correctamente para {team_home} vs {team_away}.")
    return f"{team_home} vs {team_away} Final Score: ({home_score} - {away_score})"


# Función para recorrer la carpeta y procesar los archivos
def football_match_folder(folder_path, x):
    footballMatch_id = int(input("Ingrese el limite inferior del id de partido: "))
    # Recorrer todos los archivos JSON en la carpeta
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        match_data = football_match(file_path, x, footballMatch_id)
        print(f"Datos de partido insertados correctamente: {match_data}")
        footballMatch_id += 1
# jornada = int(input("Ingrese el número de jornada: "))
# football_match_folder('/home/sp3767/Practice/Python/Projects/Apuestas/datos/Detailer_match_stats/Jornada3', jornada)
# football_match('/home/sp3767/Practice/Python/Projects/Apuestas/datos/Detailer_match_stats/6.json')