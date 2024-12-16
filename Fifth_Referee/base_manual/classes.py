import os
import csv

def ensure_directory_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)
# Clase Competition
class Competition:
    def __init__(self, name, season, num_jornadas):
        self.name = name  # Nombre de la competencia
        self.season = season  # Temporada de la competencia
        self.num_jornadas = num_jornadas  # Número de jornadas
        self.teams = []  # Lista de equipos participantes
        self.matches = []  # Lista de partidos
        self.clasificacion = {}  # Diccionario para la clasificación (puntos por equipo)
    
    def add_team(self, team):
        """Añade un equipo a la competencia."""
        self.teams.append(team)
        self.clasificacion[team.name] = {"points": 0, "wins": 0, "draws": 0, "losses": 0}  # Inicializa su posición en la clasificación
    
    def add_match(self, match):
        """Añade un partido y actualiza las estadísticas."""
        self.matches.append(match)
        self.update_clasificacion(match)
    
    def update_clasificacion(self, match):
        """Actualiza la clasificación según el resultado del partido."""
        winner, loser = match.determine_winner()
        if winner and loser:
            self.clasificacion[winner.name]["wins"] += 1
            self.clasificacion[winner.name]["points"] += 3
            self.clasificacion[loser.name]["losses"] += 1
        else:
            self.clasificacion[match.team1.name]["draws"] += 1
            self.clasificacion[match.team1.name]["points"] += 1
            self.clasificacion[match.team2.name]["draws"] += 1
            self.clasificacion[match.team2.name]["points"] += 1

    def save_to_file(self, dir_name):
        """Guarda la competencia (equipos, partidos) en un archivo."""
        # Crear el directorio de la competencia si no existe
        ensure_directory_exists(dir_name)
        
        # Guardar los equipos
        equipos_dir = os.path.join(dir_name, 'Equipos')
        ensure_directory_exists(equipos_dir)
        
        for team in self.teams:
            team.save_to_file(equipos_dir)

        # Guardar los partidos (por jornadas)
        jornadas_dir = os.path.join(dir_name, 'Jornadas')
        ensure_directory_exists(jornadas_dir)
        
        jornada_file = os.path.join(jornadas_dir, f'{self.season}.csv')
        with open(jornada_file, 'w', newline='') as file:
            writer = csv.writer(file)
            for match in self.matches:
                writer.writerow([match.team1.name, match.team2.name, match.date])

    def load_competition(self, dir_name):
        """Carga la competencia (equipos, partidos) desde un archivo."""
        equipos_dir = os.path.join(dir_name, 'Equipos')
        jornadas_dir = os.path.join(dir_name, 'Jornadas')
        
        # Cargar equipos
        for file_name in os.listdir(equipos_dir):
            file_path = os.path.join(equipos_dir, file_name)
            team = FootballTeam.load_from_file(file_path)
            self.add_team(team)

        # Cargar partidos
        jornada_file = os.path.join(jornadas_dir, f'{self.season}.csv')
        with open(jornada_file, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                team1_name, team2_name, date = row
                team1 = next((t for t in self.teams if t.name == team1_name), None)
                team2 = next((t for t in self.teams if t.name == team2_name), None)
                if team1 and team2:
                    match = Match(team1, team2, date)
                    self.add_match(match)


# Clase FootballTeam
class FootballTeam:
    def __init__(self, name, country, technical_director=None):
        self.name = name  # Nombre del equipo
        self.players = []  # Lista de jugadores
        self.country = country  # País del equipo
        self.technical_director = technical_director  # Director técnico (opcional)
    
    def add_player(self, player):
        """Añade un jugador al equipo."""
        self.players.append(player)

    def add_technical_director(self, name):
        """Añade un director técnico al equipo."""
        self.technical_director = name
    
    def save_to_file(self, dir_name):
        """Guarda el equipo y las estadísticas generales en un archivo."""
        file_path = os.path.join(dir_name, f'{self.name}.csv')
        with open(file_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([self.name, self.country, self.technical_director])
            writer.writerow(["Player", "Position", "Goals", "Shots on Target", "Shots", "Passes", "Key Passes", "Pass Accuracy", "Offside", "Red Cards", "Yellow Cards"])
            for player in self.players:
                writer.writerow([player.name, player.position, player.goals, player.shots_on_target, player.shots, player.passes, player.key_passes, player.pass_accuracy, player.offside, player.red_cards, player.yellow_cards])

    @classmethod
    def load_from_file(cls, file_path):
        """Carga un equipo desde un archivo."""
        with open(file_path, 'r') as file:
            reader = csv.reader(file)
            rows = list(reader)
            name, country, technical_director = rows[0]
            team = cls(name, country, technical_director)
            for row in rows[2:]:
                player = Player(row[0], row[1])
                player.goals = int(row[2])
                player.shots_on_target = int(row[3])
                player.shots = int(row[4])
                player.passes = int(row[5])
                player.key_passes = int(row[6])
                player.pass_accuracy = float(row[7])
                player.offside = int(row[8])
                player.red_cards = int(row[9])
                player.yellow_cards = int(row[10])
                team.add_player(player)
            return team


# Clase Player
class Player:
    def __init__(self, name, position):
        self.name = name  # Nombre del jugador
        self.position = position  # Posición del jugador
        self.match_stats = []  # Lista de estadísticas por partido
        
        # Inicializamos las estadísticas acumuladas en 0
        self.goals = 0
        self.shots_on_target = 0
        self.shots = 0
        self.passes = 0
        self.key_passes = 0
        self.pass_accuracy = 0
        self.offside = 0
        self.red_cards = 0
        self.yellow_cards = 0

    def add_match_stats(self, goals, shots_on_target, shots, passes, key_passes, pass_accuracy, offside, red_cards, yellow_cards):
        """Añade estadísticas de un partido y actualiza las estadísticas acumuladas."""
        self.match_stats.append({
            "goals": goals,
            "shots_on_target": shots_on_target,
            "shots": shots,
            "passes": passes,
            "key_passes": key_passes,
            "pass_accuracy": pass_accuracy,
            "offside": offside,
            "red_cards": red_cards,
            "yellow_cards": yellow_cards
        })
        self.update_general_stats()

    def update_general_stats(self):
        """Actualiza las estadísticas generales del jugador."""
        # Inicializamos todas las estadísticas acumuladas en 0
        self.goals = 0
        self.shots_on_target = 0
        self.shots = 0
        self.passes = 0
        self.key_passes = 0
        self.pass_accuracy = 0
        self.offside = 0
        self.red_cards = 0
        self.yellow_cards = 0

        # Acumulamos las estadísticas desde match_stats
        for match in self.match_stats:
            self.goals += match["goals"]
            self.shots_on_target += match["shots_on_target"]
            self.shots += match["shots"]
            self.passes += match["passes"]
            self.key_passes += match["key_passes"]
            self.pass_accuracy += match["pass_accuracy"]
            self.offside += match["offside"]
            self.red_cards += match["red_cards"]
            self.yellow_cards += match["yellow_cards"]

        # Promediamos la precisión de los pases (pass_accuracy)
        if self.match_stats:
            self.pass_accuracy /= len(self.match_stats)

    def get_general_stats(self):
        """Devuelve un resumen de las estadísticas acumuladas del jugador."""
        return {
            "goals": self.goals,
            "shots_on_target": self.shots_on_target,
            "shots": self.shots,
            "passes": self.passes,
            "key_passes": self.key_passes,
            "pass_accuracy": self.pass_accuracy,
            "offside": self.offside,
            "red_cards": self.red_cards,
            "yellow_cards": self.yellow_cards
        } 
    
class Match:
    def __init__(self, team1, team2, week):
        self.team1 = team1  # Primer equipo
        self.team2 = team2  # Segundo equipo
        self.week = week  # Fecha del partido
        self.player_stats = []  # Estadísticas de los jugadores en el partido

    def add_player_stats(self, team, player_name, goals=0, shots_on_target=0, shots=0, passes=0, key_passes=0, pass_accuracy=0, offside=0, red_cards=0, yellow_cards=0):
        """Actualiza las estadísticas de un jugador en el partido."""
        # Encuentra al jugador en el equipo
        player = next((p for p in team.players if p.name == player_name), None)
        if player:
            # Añade las estadísticas del jugador al partido
            self.player_stats.append({
                "player": player_name,
                "goals": goals,
                "shots_on_target": shots_on_target,
                "shots": shots,
                "passes": passes,
                "key_passes": key_passes,
                "pass_accuracy": pass_accuracy,
                "offside": offside,
                "red_cards": red_cards,
                "yellow_cards": yellow_cards
            })
    def determine_winner(self):
        """Determina el resultado del partido basado en las estadísticas de los jugadores."""
        goals_team1 = sum(stat["goals"] for stat in self.player_stats if stat["player"] in self.team1.players)
        goals_team2 = sum(stat["goals"] for stat in self.player_stats if stat["player"] in self.team2.players)

        if goals_team1 > goals_team2:
            return self.team1, self.team2  # equipo1 gana
        elif goals_team2 > goals_team1:
            return self.team2, self.team1  # equipo2 gana
        else:
            return None, None  # empate
        
    def __repr__(self):
        return f"Match: {self.team1.name} vs {self.team2.name} on {self.week}"