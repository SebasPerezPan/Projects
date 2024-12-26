import json
import os
from datetime import datetime

import pymysql as sql

from modules.connector import (
    get_competitions,
    get_matchday,
    get_matchday_information,
    get_seasons,
    insert_competitions,
    insert_matchdays,
    insert_season,
    insert_teams,
    update_season,
)
from modules.utils_dataframe import (
    extractor_data_match,
    extractor_data_match_checker,
    folder_creation_competition,
    folder_creation_season,
)


with open('/home/sp3767/Documents/files/credentials.json') as f:
    config = json.load(f)

connection = sql.connect(
    user=config['DB_USER'],
    password=config['DB_PASSWORD'],
    host=config['DB_HOST'],
    database=config['DB_NAME']
    )

cursor = connection.cursor()

def main_menu():
    while True:
        main_menu = input("App FutStats\n1. Cargar competición\n2. Crear competición.\n3. Salir\nSelecciona una opción: ")
        try:
            main_menu = int(main_menu)  # Convertir a entero
        except:
            print("Opción inválida. Por favor, ingresa un número.")
            continue

        if main_menu < 1 or main_menu > 3:
                print("Opción inválida. Inténtalo de nuevo.")
        else:
            competition_options(main_menu)

def competition_options(opcion):
    competition_list = get_competitions(connection)
    if opcion == 1:
        print("Competiciones disponibles:")
        contador = 0
        for competition in competition_list:
            contador += 1
            print(f"{contador}. {competition[1].replace('_', ' ').title()}")
        competition_choice = int(input("Selecciona una competición: "))
        competition_choice = competition_list[competition_choice - 1]
        print(f"La competicion {competition_choice[1].replace('_', ' ').title()} ha sido seleccionada.")
        season_options = int(input("1. Cargar temporada. \n2. Añadir temporada. \n3. Regresar al menu principal. \nSelecciona una opción: "))
        season_main_menu(season_options,competition_choice[0],competition_choice[1])
    
    elif opcion == 2:
        competition_name = input("Ingresa el nombre de la competición: ").replace(" ","_").lower() 
        existing_competitions = [competition[1] for competition in competition_list]
        if competition_name not in existing_competitions:
            insert_competitions(connection, competition_name)
            print(f"Competición '{competition_name.replace('_', ' ').title()}' ha sido creada exitosamente.")
            folder_creation_competition(competition_name)
        else:
            print(f"La competición '{competition_name.replace('_', ' ').title()}' ya existe.")
        main_menu()
    else:
        exit()

## Temporada:

def season_main_menu(season_options, competition_id, competition_name):
    season_list = get_seasons(connection, competition_id)
    if season_options == 3:
        main_menu()
    else:
        if season_options == 1:
            if len(season_list) < 1:
                print("No hay temporadas disponibles.")
                season_name = input("Ingresa la temporada con el formato XXXX/XXXX:").replace("/","_")
                insert_season(connection, competition_id, season_name)
                folder_creation_season(competition_name, season_name)
                season_main_menu(season_options,competition_id,competition_name)
            else:
                contador = 0
                for season in season_list:
                    contador += 1
                    print(f"{contador}. {season[2].replace('_', '/')}")
                season_choice = int(input("Selecciona una temporada: "))
                selected_season = list(season_list[season_choice - 1])
                matchdays = list(get_matchday(connection, selected_season[0]))
                if len(matchdays) < 1:
                    matchdays = int(input("Ingresa el número de jornadas: "))
                    insert_matchdays(connection, matchdays, selected_season[0])
                    
            selected_teams = [None, None]
            selected_season_menu(selected_season, selected_teams, competition_name)

        else:    
            season_name = input("Ingresa la temporada con el formato XXXX/XXXX:").replace("/","_")
            if season_list:
                existing_seasons = [season[2] for season in season_list]
                if season_name not in existing_seasons:
                    insert_season(connection, competition_id, season_name)
                    folder_creation_season(competition_name, season_name)
                else:
                    print(f"La temporada '{season_name.replace('_', ' ').title()}' ya existe.")

            else:
                insert_season(connection, competition_id, season_name)
                folder_creation_season(competition_name, season_name)

def selected_season_menu(selected_season, selected_teams, competition_name):
    season_id = int(selected_season[0])
    season_name = selected_season[2]
    folder_path = config['folder_path_matchday'].format(competition_name=competition_name,season_name=season_name)
    folder_path_checker = config['folder_path_match_data'].format(competition_name=competition_name,season_name=season_name)
    try:
        matchday_id, last_insert_date, days_since_update = get_matchday_information(connection, season_id)
        matchday = int(matchday_id) - season_id * 50
        print(f"Ultimo Matchday añadido: {matchday}\nFecha: {last_insert_date}\nDías desde última actualización:{days_since_update}")
    except:
        matchday = 0
        extractor_data_match(competition_name, season_name, folder_path, extractor_data_match_checker(folder_path_checker))
        insert_teams(connection, competition_name, season_name, season_id)
        print("No hay jornadas disponibles.")
    season_submenu_options = int(input("1. Actualizar información\n2. Regresar al menu principal. \nSelecciona una opción: "))
    if season_submenu_options == 1:
        extractor_data_match(competition_name, season_name, folder_path, extractor_data_match_checker(folder_path_checker))
        try:
            update_season(connection, competition_name, season_name, season_id, matchday)
        except:
            print("Error al actualizar la información.")
            selected_season_menu(selected_season, selected_teams, competition_name)
        finally:
            print("Información actualizada.")
            selected_season_menu(selected_season, selected_teams, competition_name)
    else:
        main_menu()


main_menu()