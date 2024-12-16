from connector import *
from classes import *

def select_and_display_season():
    """
    Función para seleccionar una competición, una temporada y mostrar los jugadores destacados.
    """
    # Selección de competición
    competition_list = sorted(get_competitions(connection))
    print("\nCompeticiones disponibles:\n")
    for competition in competition_list:
        print(f"{competition[0]}. {competition[1].replace('_', ' ').title()}",end="    ")
    competition_id = int(input("\nSelecciona una competición: \n\n"))
    competition_name = competition_list[competition_id-1][1]
    print(f"\nHas seleccionado {competition_name.replace('_', ' ').title()}\n")

    # Selección de temporada
    season_list = list(get_seasons(connection, competition_id))
    print("Temporadas disponibles:\n")
    for idx, season in enumerate(season_list, start=1):
        print(f"{idx}. {season[2].replace('_','/')}\n")
    
    if len(season_list) > 1:
        season_option = int(input("Selecciona una temporada: \n"))
    else:
        season_option = 1

    season_id = season_list[season_option - 1][0]
    season_name = season_list[season_option-1][2]
    print(f"Has seleccionado {season_name.replace('_', '/').title()}\n")

    # Crear instancia de Season y cargar datos
    selected_season = Season(season_id, season_name, competition_id, competition_name)
    selected_season.load_teams_and_players(connection)
    selected_season.load_matches_and_assign_to_teams(connection)
#    selected_season.display_top_players()
    selected_season.display_standings()
    return selected_season

def select_teams(selected_season):
    """
    Permite al usuario seleccionar un equipo principal y uno secundario de una temporada específica.

    Parámetros:
    - selected_season: Objeto Season que contiene los equipos disponibles.

    Retorna:
    - selected_main_team: Objeto del equipo principal seleccionado.
    - selected_secondary_team: Objeto del equipo secundario seleccionado.
    """
    print("\nEquipos disponibles en la temporada:")
    for idx, team in enumerate(selected_season.teams):
        print(f"{idx + 1}. {team.team_name}")

    try:
        selected_main_team_idx = int(input("Selecciona el equipo local: ")) - 1
        selected_secondary_team_idx = int(input("Selecciona el equipo visitante: ")) - 1

        selected_main_team = selected_season.teams[selected_main_team_idx]
        selected_secondary_team = selected_season.teams[selected_secondary_team_idx]

        print(f"\nEquipo local seleccionado: {selected_main_team.team_name}")
        print(f"Equipo visitante seleccionado: {selected_secondary_team.team_name}")

        return selected_main_team, selected_secondary_team

    except IndexError:
        print("Seleccionaste un número fuera del rango. Por favor, inténtalo de nuevo.")
        return None, None
    except ValueError:
        print("Entrada inválida. Por favor, ingresa un número.")
        return None, None
