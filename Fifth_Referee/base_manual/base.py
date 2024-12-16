from classes import Competition, FootballTeam, Match, Player  # Importa las clases del archivo `classes.py`
import os

# Menú Principal
def main_menu():
    '''
    Main menu is made up of 3 options: Load a Competition, Create a Competition, and Exit. To load a Competition you must have it created in the Competitions folder. To create a Competition, you will be prompted to enter the name, season, and number of weeks (jornadas). You will then be prompted to add teams to the competition. Once a competition is loaded or created, you will be taken to the Competition Menu where you can view general team stats, view top player rankings, select a team, select an opponent, manage matches, save and return to the main menu, exit to the main menu without saving, or exit the program.
    parameter: int x ; 0 < x < 4
    return: None.
    '''
    while True:
        main_menu_choice = input("\n--- Main Menu ---\n1. Load a Competition.\n2. Create a Competition.\n3. Exit.\nChoose an option:")

        if main_menu_choice == "1":
            load_competition_menu()
        elif main_menu_choice == "2":
            create_competition()
        elif main_menu_choice == "3":
            print("Exiting program...")
            break
        else:
            print("Invalid option. Please choose again.")

# Submenú para cargar una competencia existente
def load_competition_menu():
    competitions_dir = "Competitions"
    if not os.path.exists(competitions_dir):
        print("No competitions found.")
        return

    # Seleccionar la competición
    print("\n--- Select Competition ---")
    competitions = [d for d in os.listdir(competitions_dir) if os.path.isdir(os.path.join(competitions_dir, d))]
    if not competitions:
        print("No competitions available.")
        return

    for i, comp in enumerate(competitions):
        print(f"{i + 1}. {comp}")
    comp_index = int(input("Enter the number of the competition: ")) - 1
    selected_competition = competitions[comp_index]

    # Seleccionar la temporada
    comp_dir = os.path.join(competitions_dir, selected_competition)
    seasons = [d for d in os.listdir(comp_dir) if os.path.isdir(os.path.join(comp_dir, d))]
    if not seasons:
        print("No seasons available for this competition.")
        return

    print("\n--- Select Season ---")
    for i, season in enumerate(seasons):
        print(f"{i + 1}. {season}")
    season_index = int(input("Enter the number of the season: ")) - 1
    selected_season = seasons[season_index]

    # Cargar los datos de la temporada seleccionada
    season_dir = os.path.join(comp_dir, selected_season)
    comp = Competition(name=selected_competition, season=selected_season, num_jornadas=0)
    comp.load_competition(season_dir)

    # Ahora mostrar el menú para gestionar la competición cargada
    while True:
        print("\n--- Competition Menu ---")
        print("1. View General Team Stats")
        print("2. View Top Player Rankings")
        print("3. Select a Team")
        print("4. Select an Opponent")
        print("5. Match Management")
        print("6. Save and Return to Main Menu")
        print("7. Exit to Main Menu")
        print("8. Exit Program")
        choice = input("Choose an option: ")

        if choice == "1":
            view_team_stats(comp)
        elif choice == "2":
            view_top_player_rankings(comp)
        elif choice == "3":
            select_team(comp)
        elif choice == "4":
            select_opponent(comp)
        elif choice == "5":
            match_management(comp)
        elif choice == "6":
            save_and_exit(comp, season_dir)
            return  # Volver al menú principal
        elif choice == "7":
            return  # Volver al menú principal sin guardar
        elif choice == "8":
            print("Exiting program...")
            exit()
        else:
            print("Invalid option. Please choose again.")


def ensure_directory_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

def create_competition():
    name = input("Enter competition name: ").lower().replace(" ", "_")
    season = input("Enter competition season (e.g., 2023_2024): ")
    num_jornadas = int(input("Enter the number of weeks (jornadas): "))

    # Preguntar si la competición es nacional o internacional
    competition_type = input("Is this a national or international competition? (n/i): ").lower()
    if competition_type == 'n':
        country = input("Enter the country for this national league: ")
    else:
        country = None  # Para competiciones internacionales, pediremos el país por equipo

    comp = Competition(name, season, num_jornadas)

    while True:
        print("\n--- Add Teams ---")
        team_name = input("Enter team name (or type 'done' to finish): ").lower().replace(" ", "_")
        if team_name.lower() == 'done':
            break
        
        # Si la competición es nacional, el país es el mismo para todos los equipos
        if competition_type == 'n':
            team = FootballTeam(name=team_name, country=country)
        else:
            # Para competiciones internacionales, se pide el país de cada equipo
            country = input(f"Enter the country for {team_name}: ").lower().replace(" ", "_")
            team = FootballTeam(name=team_name, country=country)

        comp.add_team(team)

    # Definir la ruta para guardar la competición
    comp_dir = os.path.join("Competitions", name, season)

    # Asegurar que las carpetas existan
    ensure_directory_exists(comp_dir)
    ensure_directory_exists(os.path.join(comp_dir, 'Equipos'))
    ensure_directory_exists(os.path.join(comp_dir, 'Jornadas'))

    # Guardar la competición en los directorios creados
    comp.save_to_file(comp_dir)
    print(f"Competition {name} for season {season} created and saved.")
    main_menu()  # Regresar al menú principal


# Ver estadísticas generales del equipo
def view_team_stats(comp):
    print("\n--- General Team Stats ---")
    for team in comp.teams:
        print(f"\nTeam: {team.name}")
        for player in team.players:
            stats = player.get_general_stats()
            print(f"Player: {player.name} - {stats}")

# Ver clasificación de los mejores jugadores
def view_top_player_rankings(comp):
    print("\n--- Top Player Rankings ---")
    top_scorers = []
    for team in comp.teams:
        for player in team.players:
            top_scorers.append((player.name, player.goals))
    top_scorers = sorted(top_scorers, key=lambda x: x[1], reverse=True)[:5]
    print("\nTop 5 Scorers:")
    for i, (player_name, goals) in enumerate(top_scorers):
        print(f"{i + 1}. {player_name} - Goals: {goals}")

# Seleccionar equipo para ver sus estadísticas
def select_team(comp):
    print("\n--- Select Team ---")
    for i, team in enumerate(comp.teams):
        print(f"{i + 1}. {team.name}")
    team_index = int(input("Enter the number of the team to select: ")) - 1
    selected_team = comp.teams[team_index]
    print(f"\nSelected Team: {selected_team.name}")

    for player in selected_team.players:
        stats = player.get_general_stats()
        print(f"Player: {player.name} - {stats}")

# Seleccionar un equipo rival
def select_opponent(comp):
    print("\n--- Select Opponent ---")
    for i, team in enumerate(comp.teams):
        print(f"{i + 1}. {team.name}")
    opponent_index = int(input("Enter the number of the opponent team: ")) - 1
    opponent_team = comp.teams[opponent_index]
    print(f"\nSelected Opponent: {opponent_team.name}")

# Gestión de partidos
def match_management(comp):
    print("\n--- Match Management ---")
    print("1. View Match Stats")
    print("2. Create a Match")
    choice = input("Choose an option: ")

    if choice == "1":
        view_match_stats(comp)
    elif choice == "2":
        create_match(comp)

# Ver estadísticas de un partido
def view_match_stats(comp):
    print("\n--- Select a Match to View ---")
    for i, match in enumerate(comp.matches):
        print(f"{i + 1}. {match.team1.name} vs {match.team2.name} (Week: {match.date})")
    match_index = int(input("Enter the number of the match to view: ")) - 1
    selected_match = comp.matches[match_index]
    print(f"\nMatch: {selected_match.team1.name} vs {selected_match.team2.name} (Week: {selected_match.date})")
    for stat in selected_match.player_stats:
        print(f"Player: {stat['player']}, Goals: {stat['goals']}, Passes: {stat['passes']}")

# Crear un nuevo partido
def create_match(comp):
    print("\n--- Create a Match ---")
    print("Select Team 1:")
    select_team(comp)
    print("Select Team 2:")
    select_opponent(comp)
    week = input("Enter the week number: ")
    team1 = comp.teams[int(input("Enter the number of Team 1: ")) - 1]
    team2 = comp.teams[int(input("Enter the number of Team 2: ")) - 1]

    match = Match(team1, team2, week)
    comp.add_match(match)
    print(f"Match {team1.name} vs {team2.name} created for week {week}.")

# Guardar y salir
def save_and_exit(comp, comp_dir):
    comp.save_to_file(comp_dir)
    print(f"Competition saved to {comp_dir}.")

# Iniciar el programa
if __name__ == "__main__":
    main_menu()
