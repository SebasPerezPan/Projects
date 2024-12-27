from math import pi
import pandas as pd
from IPython.display import display, HTML
from bokeh.io import output_notebook, show
from bokeh.layouts import column, gridplot, row
from bokeh.models import (
    Button,
    ColumnDataSource,
    CustomJS,
    DataTable,
    Div,
    HoverTool,
    Select,
    TableColumn,
)
from bokeh.palettes import Category20, Category20c
from bokeh.plotting import figure
from bokeh.transform import cumsum


class Season:
    def __init__(self, season_id, season_name, competition_id, competition_name):
        self.season_id = season_id
        self.season_name = season_name
        self.competition_id = competition_id
        self.competition_name = competition_name
        self.teams = []

    def load_teams_and_players(self, connection):
        """
        Carga los equipos y jugadores de la temporada, incluyendo estadísticas básicas de los jugadores.
        """
        cursor = connection.cursor()

        query_teams = """
        SELECT team_id, team_name, stadium, city
        FROM team
        WHERE season_id = %s
        """
        cursor.execute(query_teams, (self.season_id,))
        teams_data = cursor.fetchall()

        # Crear diccionario para mapear team_id a información extendida
        
        teams_dict = {team_id: (team_name, stadium, city) for team_id, team_name, stadium, city in teams_data}            # Obtener jugadores y estadísticas básicas (actualizado)
        
        query_players = """
        SELECT p.player_id, p.team_id, p.player_name, p.jersey_number, p.season_id, p.position,
            SUM(ps.goles) as goles, SUM(ps.asistencias) as asistencias,
            SUM(ps.pases_claves) as pases_claves, SUM(ps.goles_recibidos) as goles_recibidos,
            SUM(ps.faltas_cometidas) as faltas_cometidas, SUM(ps.big_chances_scored) as big_chances_scored,
            SUM(ps.chances_perdidas) as chances_perdidas
        FROM player p
        LEFT JOIN player_stats ps ON p.player_id = ps.player_id AND p.team_id = ps.team_id
        WHERE p.season_id = %s
        GROUP BY p.player_id
        """
        cursor.execute(query_players, (self.season_id,))
        players_data = cursor.fetchall()

        # Crear un diccionario de jugadores por equipo
        players_by_team = {}
        for player in players_data:
            (player_id, team_id, player_name, jersey_number, season_id, position,
            goles, asistencias, pases_claves, goles_recibidos,
            faltas_cometidas, big_chances_scored, chances_perdidas) = player

            # Convertir valores a tipos numéricos nativos
            stats = {
                'goles': int(goles or 0),
                'asistencias': int(asistencias or 0),
                'pases_claves': int(pases_claves or 0),
                'goles_recibidos': int(goles_recibidos or 0),
                'faltas_cometidas': int(faltas_cometidas or 0),
                'big_chances_scored': int(big_chances_scored or 0),
                'chances_perdidas': int(chances_perdidas or 0)
            }
            player_obj = Player(
                player_id=player_id,
                team_id=team_id,
                player_name=player_name,
                jersey_number=jersey_number,
                season_id=season_id,
                position=position,
                stats=stats
            )

            # Añadir jugador al equipo correspondiente
            if team_id not in players_by_team:
                players_by_team[team_id] = []
            players_by_team[team_id].append(player_obj)

        # Construir los equipos con los jugadores
        for team_id, (team_name, stadium, city) in teams_dict.items():
            team_players = players_by_team.get(team_id, [])
            team_obj = Team(
                team_id=team_id,
                team_name=team_name,
                stadium=stadium,
                city=city,
                season_id=self.season_id,
                players=team_players,
                season=self  # Referencia a la temporada actual
            )
            self.teams.append(team_obj)

        cursor.close()

    def load_matches_and_assign_to_teams(self, connection):
        """
        Carga los partidos de la temporada y los asigna a los equipos correspondientes.
        """
        cursor = connection.cursor()

        # Obtener los partidos de la temporada
        query_matches = """
        SELECT match_id, matchday_id, home_team_id, away_team_id, home_score, away_score, duration
        FROM football_game
        WHERE season_id = %s
        """
        cursor.execute(query_matches, (self.season_id,))
        matches_data = cursor.fetchall()

        # Crear un diccionario para mapear team_id a objetos Team
        teams_by_id = {team.team_id: team for team in self.teams}

        for match in matches_data:
            (match_id, matchday_id, home_team_id, away_team_id,
             home_score, away_score, duration) = match

            # Crear objeto Match (asegurando que la clase Match está definida)
            match_obj = Match(
                match_id=match_id,
                matchday_id=matchday_id,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                home_score=home_score,
                away_score=away_score,
                duration=duration
            )

            # Asignar el partido al equipo local
            if home_team_id in teams_by_id:
                teams_by_id[home_team_id].matches.append(match_obj)

            # Asignar el partido al equipo visitante
            if away_team_id in teams_by_id:
                teams_by_id[away_team_id].matches.append(match_obj)

        cursor.close()

## Metodos.

    def calculate_standings(self):
        # Constantes para índices en las sublistas de equipos
        TEAM_ID = 0
        STANDING = 1
        WINS = 2
        LOSSES = 3
        DRAWS = 4
        GOALS = 5
        GOALS_CONCEDED = 6

        # Inicializar estructura temporal para las estadísticas de los equipos
        team_stats = [
            [team.team_id, 0, [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]]  # [team_id, standing, wins, losses, draws, goals, goals_conceded]
            for team in self.teams
        ]

        # Crear un diccionario para optimizar la búsqueda de estadísticas
        team_stats_dict = {team.team_id: stats for team, stats in zip(self.teams, team_stats)}

        # Recorrer todos los partidos asociados a los equipos de la temporada
        for team in self.teams:
            for match in team.matches:
                # Identificar si el equipo es local o visitante
                if match.home_team_id == team.team_id:
                    home_team_stats = team_stats_dict[match.home_team_id]
                    home_team_stats[GOALS][0] += match.home_score  # Goles de local
                    home_team_stats[GOALS_CONCEDED][0] += match.away_score  # Goles concedidos de local
                    if match.home_score > match.away_score:
                        home_team_stats[WINS][0] += 1  # Victoria de local
                    elif match.home_score < match.away_score:
                        home_team_stats[LOSSES][0] += 1  # Derrota de local
                    else:
                        home_team_stats[DRAWS][0] += 1  # Empate de local

                if match.away_team_id == team.team_id:
                    away_team_stats = team_stats_dict[match.away_team_id]
                    away_team_stats[GOALS][1] += match.away_score  # Goles de visitante
                    away_team_stats[GOALS_CONCEDED][1] += match.home_score  # Goles concedidos de visitante
                    if match.away_score > match.home_score:
                        away_team_stats[WINS][1] += 1  # Victoria de visitante
                    elif match.away_score < match.home_score:
                        away_team_stats[LOSSES][1] += 1  # Derrota de visitante
                    else:
                        away_team_stats[DRAWS][1] += 1  # Empate de visitante

        # Actualizar los atributos de cada equipo con los datos calculados
        for team, stats in zip(self.teams, team_stats):
            team.standing = stats[STANDING]  # La posición se mantendrá en el atributo de la clase
            team.wins = sum(stats[WINS])  # Sumar victorias de local y visitante
            team.losses = sum(stats[LOSSES])  # Sumar derrotas de local y visitante
            team.draws = sum(stats[DRAWS])  # Sumar empates de local y visitante
            team.goals = [sum(stats[GOALS][0:1]), sum(stats[GOALS][1:2])]  # Goles de local y visitante
            team.goals_conceded = [sum(stats[GOALS_CONCEDED][0:1]), sum(stats[GOALS_CONCEDED][1:2])]  # Goles concedidos de local y visitante

        # Ahora ordenamos los equipos por puntos, diferencia de goles, y goles a favor
        self.teams.sort(key=lambda team: (
            team.wins * 3 + team.draws,  # Puntos
            (sum(team.goals) - sum(team.goals_conceded)),  # Diferencia de goles
            sum(team.goals)  # Goles a favor
        ), reverse=True)

        # Actualizamos la posición de cada equipo después de ordenar
        for position, team in enumerate(self.teams, start=1):
            team.standing = position  # Actualizar la posición en el standing

        # Limpiar las variables temporales de la memoria
        del team_stats
        del team_stats_dict

    def display_top_players(self, top_n=10):
        """
        Muestra un gráfico interactivo de los mejores jugadores en diferentes categorías utilizando Bokeh.
        Los jugadores están coloreados según su equipo.
        """
        # Crear un mapeo de team_id a team_name
        team_id_to_name = {team.team_id: team.team_name for team in self.teams}
        
        # Lista para almacenar todos los jugadores
        all_players = []
        for team in self.teams:
            all_players.extend(team.players)
        
        # Crear DataFrame con las estadísticas relevantes
        data = {
            'Player': [player.player_name for player in all_players],
            'Team': [team_id_to_name.get(player.team_id, 'Unknown') for player in all_players],
            'Goals': [int(player.stats.get('goles', 0)) for player in all_players],
            'Assists': [int(player.stats.get('asistencias', 0)) for player in all_players],
            'Key_Passes': [int(player.stats.get('pases_claves', 0)) for player in all_players],
            'Goals_Conceded': [int(player.stats.get('goles_recibidos', 0)) for player in all_players],
            'Fouls_Committed': [int(player.stats.get('faltas_cometidas', 0)) for player in all_players],
            'Big_Chances_Scored': [int(player.stats.get('big_chances_scored', 0)) for player in all_players],
            'Missed_Chances': [int(player.stats.get('chances_perdidas', 0)) for player in all_players]
        }
        
        df = pd.DataFrame(data)
        
        # Definir las categorías disponibles y sus títulos
        categories = {
            'Goals': 'Máximos Goleadores',
            'Assists': 'Máximos Asistidores',
            'Key_Passes': 'Jugadores con Más Pases Clave',
            'Goals_Conceded': 'Jugadores con Más Goles Recibidos',
            'Fouls_Committed': 'Jugadores con Más Faltas Cometidas',
            'Big_Chances_Scored': 'Jugadores con Más Grandes Ocasiones Anotadas',
            'Missed_Chances': 'Jugadores con Más Ocasiones Perdidas'
        }
        
        # Categoría inicial
        initial_category = 'Goals'
        
        # Asignar colores a cada equipo
        teams = df['Team'].unique()
        palette = Category20c[20] if len(teams) > 20 else Category20[len(teams)]
        color_map = {team: color for team, color in zip(teams, palette)}
        df['Color'] = df['Team'].map(color_map)
        
        # Ordenar y seleccionar los mejores jugadores para la categoría inicial
        top_players = df.sort_values(by=initial_category, ascending=False).head(top_n)
        
        # Crear ColumnDataSource con todos los datos necesarios
        source = ColumnDataSource(data=dict(
            player=top_players['Player'].tolist(),
            team=top_players['Team'].tolist(),
            value=top_players[initial_category].tolist(),
            color=top_players['Color'].tolist(),
            Goals=top_players['Goals'].tolist(),
            Assists=top_players['Assists'].tolist(),
            Key_Passes=top_players['Key_Passes'].tolist(),
            Goals_Conceded=top_players['Goals_Conceded'].tolist(),
            Fouls_Committed=top_players['Fouls_Committed'].tolist(),
            Big_Chances_Scored=top_players['Big_Chances_Scored'].tolist(),
            Missed_Chances=top_players['Missed_Chances'].tolist()
        ))
        
        # Crear figura de Bokeh
        p = figure(x_range=top_players['Player'].tolist(), height=600, title=categories[initial_category],
                toolbar_location=None, tools="")
        
        # Añadir gráfico de barras
        p.vbar(x='player', top='value', width=0.9, source=source, line_color='white', fill_color='color')
        
        # Personalizar gráfico
        p.xgrid.grid_line_color = None
        p.y_range.start = 0
        p.xaxis.major_label_orientation = 1.2  # Rotar etiquetas del eje x
        
        # Mapear nombres de categorías para JavaScript
        category_columns = {
            'Goals': 'Goals',
            'Assists': 'Assists',
            'Key_Passes': 'Key_Passes',
            'Goals_Conceded': 'Goals_Conceded',
            'Fouls_Committed': 'Fouls_Committed',
            'Big_Chances_Scored': 'Big_Chances_Scored',
            'Missed_Chances': 'Missed_Chances'
        }
        
        # Crear menú desplegable
        select = Select(title="Categoría:", value=initial_category, options=list(categories.keys()))
        
        # Crear callback JavaScript
        callback = CustomJS(args=dict(source=source, p=p, df=df.to_dict('list'), categories=categories, category_columns=category_columns, top_n=top_n), code="""
            var data = source.data;
            var category = cb_obj.value;
            var column_name = category_columns[category];
            
            // Obtener todos los datos
            var all_data = df;
            
            // Combinar datos en un solo arreglo
            var data_list = [];
            for (var i = 0; i < all_data['Player'].length; i++) {
                data_list.push({
                    'player': all_data['Player'][i],
                    'team': all_data['Team'][i],
                    'value': all_data[column_name][i],
                    'color': all_data['Color'][i],
                    'Goals': all_data['Goals'][i],
                    'Assists': all_data['Assists'][i],
                    'Key_Passes': all_data['Key_Passes'][i],
                    'Goals_Conceded': all_data['Goals_Conceded'][i],
                    'Fouls_Committed': all_data['Fouls_Committed'][i],
                    'Big_Chances_Scored': all_data['Big_Chances_Scored'][i],
                    'Missed_Chances': all_data['Missed_Chances'][i]
                });
            }
        
            // Ordenar y obtener los top_n
            data_list.sort(function(a, b) { return b['value'] - a['value']; });
            data_list = data_list.slice(0, top_n);
        
            // Actualizar datos en source
            data['player'] = data_list.map(function(item) { return item['player']; });
            data['team'] = data_list.map(function(item) { return item['team']; });
            data['value'] = data_list.map(function(item) { return item['value']; });
            data['color'] = data_list.map(function(item) { return item['color']; });
        
            // Actualizar todas las categorías
            for (var key in category_columns) {
                var col = category_columns[key];
                data[col] = data_list.map(function(item) { return item[col]; });
            }
        
            // Actualizar rango del eje x y título
            p.x_range.factors = data['player'];
            p.title.text = categories[category];
        
            source.change.emit();
        """)
        
        select.js_on_change('value', callback)
        
        # Mostrar todo en un layout
        layout = column(select, p)
        show(layout)

    def display_standings(self):
        """
        Muestra una tabla interactiva de clasificación, permitiendo seleccionar la jornada.
        """

        # Obtener todas las jornadas disponibles
        matchdays = sorted(set(match.matchday_id for team in self.teams for match in team.matches))

        if not matchdays:
            print("No hay jornadas disponibles para esta temporada.")
            return

        visible_matchdays = [md - (self.season_id * 50) for md in matchdays]
        matchday_mapping = {str(visible_md): real_md for visible_md, real_md in zip(visible_matchdays, matchdays)}

        initial_visible_matchday = max(visible_matchdays)
        initial_real_matchday = matchday_mapping[str(initial_visible_matchday)]

        standings_df = self.calculate_standings(matchday=initial_real_matchday)

        # Convertir datos a tipos serializables
        standings_df = standings_df.astype(str)  # Convertir todos los datos a cadenas para evitar problemas de serialización
        source = ColumnDataSource(standings_df)

        columns = [
            TableColumn(field="Posicion", title="Position"),
            TableColumn(field="Equipo", title="Team"),
            TableColumn(field="PJ", title="Matches"),
            TableColumn(field="PG", title="Wins"),
            TableColumn(field="PE", title="Draws"),
            TableColumn(field="PP", title="Losses"),
            TableColumn(field="GF", title="Goals"),
            TableColumn(field="GC", title="G. Conceded"),
            TableColumn(field="DG", title="G. Balance"),
        ]

        data_table = DataTable(source=source, columns=columns, width=800, height=400)

        select = Select(
            title="Jornada:",
            value=str(initial_visible_matchday),
            options=[str(md) for md in visible_matchdays]
        )

        callback = CustomJS(args=dict(source=source, matchday_mapping=matchday_mapping), code="""
            const visible_matchday = cb_obj.value;
            const real_matchday = matchday_mapping[visible_matchday];

            // Simulación: Obtén datos desde el servidor o recalcula datos
            console.log(`Cambiando a jornada ${visible_matchday} (matchday real: ${real_matchday})`);
            // Aquí deberías reemplazar con una lógica real para actualizar los datos
        """)
        select.js_on_change('value', callback)

        layout = column(select, data_table)
        show(layout)

class Team:
    
    def __init__(self, team_id, team_name, stadium, city, season_id, players=None, season=None):
        self.team_id = team_id
        self.team_name = team_name
        self.stadium = stadium
        self.city = city
        self.season_id = season_id
        self.players = players or []
        self.season = season
        self.matches = []
        self.standing = 0  # Posición en la tabla
        self.wins = [0, 0]  # [local_wins, away_wins]
        self.losses = [0, 0]  # [local_losses, away_losses]
        self.draws = [0, 0]  # [local_draws, away_draws]
        self.goals = [0, 0]  # [home_goals, away_goals]
        self.goals_conceded = [0, 0]  # [home_goals_conceded, away_goals_conceded]

    def __str__(self):
        return f"\n{self.team_name} ({self.city}) - Posición: {self.standing}, Goles: {sum(self.goals)}, Goles Concedidos: {sum(self.goals_conceded)}"

    def display_players(self):
        """
        Muestra la lista de jugadores del equipo y sus estadísticas básicas.
        """
        print(f"\nJugadores del equipo {self.team_name}:")
        for player in self.players:
            print(f"Jugador: {player.player_name} - Posición: {player.position}")
            print(f"Goles: {player.stats.get('goles', 0)}, Asistencias: {player.stats.get('asistencias', 0)}, "
                  f"Pases Claves: {player.stats.get('pases_claves', 0)}, Goles Recibidos: {player.stats.get('goles_recibidos', 0)}\n")

    def display_matches(self):
        """
        Muestra los partidos del equipo.
        """
        print(f"\nPartidos del equipo {self.team_name}:")
        for match in self.matches:
            if match.home_team_id == self.team_id:
                opponent = self.get_team_name(match.away_team_id)
                result = f"{self.team_name} {match.home_score} - {match.away_score} {opponent}"
            else:
                opponent = self.get_team_name(match.home_team_id)
                result = f"{opponent} {match.home_score} - {match.away_score} {self.team_name}"
            print(f"Jornada {match.matchday_id}: {result}")

    
    def display_team_summary(self):
        """
        Muestra un resumen completo del rendimiento del equipo combinando gráficos de dona para
        resultados y gráficos de tendencia para el rendimiento a lo largo del tiempo.
        """
        output_notebook()

        # Procesar datos para los gráficos de dona
        home_wins, home_draws, home_losses = 0, 0, 0
        away_wins, away_draws, away_losses = 0, 0, 0
        home_results = []
        away_results = []

        # Datos para gráficos de tendencia
        match_numbers = []
        total_performance = []
        home_performance = []
        away_performance = []
        tooltips_total = []
        tooltips_home = []
        tooltips_away = []

        total_score = 0
        home_score = 0
        away_score = 0
        
        # Ordenar los partidos por jornada
        sorted_matches = sorted(self.matches, key=lambda x: x.matchday_id)
        
        # Variables para llevar el conteo de partidos
        home_match_number = 0
        away_match_number = 0

        for idx, match in enumerate(sorted_matches):
            match_numbers.append(idx + 1)
            
            if match.home_team_id == self.team_id:
                home_match_number += 1
                opponent = self.get_team_name(match.away_team_id)
                result = f"{self.team_name} {match.home_score} - {match.away_score} {opponent}"
                home_results.append(result)
                
                # Procesar resultado para dona
                if match.home_score > match.away_score:
                    home_wins += 1
                    total_score += 1
                    home_score += 1
                elif match.home_score == match.away_score:
                    home_draws += 1
                else:
                    home_losses += 1
                    total_score -= 1
                    home_score -= 1
                    
                # Datos para gráfico de tendencia
                tooltips_total.append(f"Jornada {int(match.matchday_id) - (50*self.season_id)}: {result}")
                tooltips_home.append(f"Jornada {int(match.matchday_id) - (50*self.season_id)}: {result}")
                tooltips_away.append(None)
                total_performance.append(total_score)
                home_performance.append(home_score)
                
            elif match.away_team_id == self.team_id:
                away_match_number += 1
                opponent = self.get_team_name(match.home_team_id)
                result = f"{opponent} {match.home_score} - {match.away_score} {self.team_name}"
                away_results.append(result)
                
                # Procesar resultado para dona
                if match.away_score > match.home_score:
                    away_wins += 1
                    total_score += 1
                    away_score += 1
                elif match.away_score == match.home_score:
                    away_draws += 1
                else:
                    away_losses += 1
                    total_score -= 1
                    away_score -= 1
                    
                # Datos para gráfico de tendencia
                tooltips_total.append(f"Jornada {int(match.matchday_id) - (50*self.season_id)}: {result}")
                tooltips_home.append(None)
                tooltips_away.append(f"Jornada {int(match.matchday_id) - (50*self.season_id)}: {result}")
                total_performance.append(total_score)
                away_performance.append(away_score)

        # Crear fuentes de datos para las donas
        home_total = home_wins + home_draws + home_losses
        away_total = away_wins + away_draws + away_losses
        
        home_source = ColumnDataSource({
            'angle': [2*pi*v/home_total for v in [home_wins, home_draws, home_losses]],
            'color': ['#337357', '#FFD23F', '#EE4266'],
            'category': ['Victorias', 'Empates', 'Derrotas'],
            'value': [home_wins, home_draws, home_losses],
            'percentage': [v/home_total*100 for v in [home_wins, home_draws, home_losses]]
        })

        away_source = ColumnDataSource({
            'angle': [2*pi*v/away_total for v in [away_wins, away_draws, away_losses]],
            'color': ['#337357', '#FFD23F', '#EE4266'],
            'category': ['Victorias', 'Empates', 'Derrotas'],
            'value': [away_wins, away_draws, away_losses],
            'percentage': [v/away_total*100 for v in [away_wins, away_draws, away_losses]]
        })

        # Crear fuentes de datos para los gráficos de tendencia
        source_total = ColumnDataSource(data=dict(
            x=match_numbers,
            y=total_performance,
            desc=tooltips_total
        ))

        source_home = ColumnDataSource(data=dict(
            x=list(range(1, home_match_number + 1)),
            y=home_performance,
            desc=[d for d in tooltips_home if d is not None]
        ))

        source_away = ColumnDataSource(data=dict(
            x=list(range(1, away_match_number + 1)),
            y=away_performance,
            desc=[d for d in tooltips_away if d is not None]
        ))

        # Crear gráficos de dona
        tooltips_dona = [
            ('Categoría', '@category'),
            ('Cantidad', '@value'),
            ('Porcentaje', '@percentage{0.1}%')
        ]

        p_home_dona = figure(height=300, width=300, title=f"Rendimiento Local - {self.team_name}",
                            toolbar_location=None, tools="hover", tooltips=tooltips_dona)
        
        p_home_dona.annular_wedge(x=0, y=0, inner_radius=0.2, outer_radius=0.4,
                                start_angle=cumsum('angle', include_zero=True),
                                end_angle=cumsum('angle'),
                                line_color="white", fill_color='color', source=home_source)

        p_away_dona = figure(height=300, width=300, title=f"Rendimiento Visitante - {self.team_name}",
                            toolbar_location=None, tools="hover", tooltips=tooltips_dona)
        
        p_away_dona.annular_wedge(x=0, y=0, inner_radius=0.2, outer_radius=0.4,
                                start_angle=cumsum('angle', include_zero=True),
                                end_angle=cumsum('angle'),
                                line_color="white", fill_color='color', source=away_source)

        for p in [p_home_dona, p_away_dona]:
            p.axis.axis_label = None
            p.axis.visible = False
            p.grid.grid_line_color = None

        # Crear gráficos de tendencia
        hover_trend = HoverTool(tooltips=[("Info", "@desc")])

        p_total = figure(title=f"Rendimiento Total de {self.team_name}", 
                        x_axis_label='Partidos', y_axis_label='Rendimiento',
                        width=900, height=250)
        p_total.line('x', 'y', source=source_total, line_width=2, color='blue')
        p_total.scatter('x', 'y', source=source_total, size=8, color='blue')
        p_total.add_tools(hover_trend)

        p_home = figure(title=f"Rendimiento en Casa de {self.team_name}", 
                    x_axis_label='Partidos en Casa', y_axis_label='Rendimiento',
                    width=900, height=250)
        p_home.line('x', 'y', source=source_home, line_width=2, color='green')
        p_home.scatter('x', 'y', source=source_home, size=8, color='green')
        p_home.add_tools(hover_trend)

        p_away = figure(title=f"Rendimiento como Visitante de {self.team_name}", 
                    x_axis_label='Partidos como Visitante', y_axis_label='Rendimiento',
                    width=900, height=250)
        p_away.line('x', 'y', source=source_away, line_width=2, color='red')
        p_away.scatter('x', 'y', source=source_away, size=8, color='red')
        p_away.add_tools(hover_trend)

        # Crear tabla de resultados
        results_html = f"""
        <div style="padding: 20px; background-color: #f5f5f5; border-radius: 5px;">
            <h3 style="color: #333;">Últimos Resultados</h3>
            <div style="display: flex; justify-content: space-between;">
                <div style="width: 45%;">
                    <h4 style="color: #337357;">Local</h4>
                    <ul style="list-style-type: none; padding: 0;">
                        {"".join(f"<li style='margin: 5px 0;'>{result}</li>" for result in home_results[-5:])}
                    </ul>
                </div>
                <div style="width: 45%;">
                    <h4 style="color: #EE4266;">Visitante</h4>
                    <ul style="list-style-type: none; padding: 0;">
                        {"".join(f"<li style='margin: 5px 0;'>{result}</li>" for result in away_results[-5:])}
                    </ul>
                </div>
            </div>
        </div>
        """
        
        results_table = Div(text=results_html)

        # Organizar el layout
        donas = row(p_home_dona, p_away_dona)
        trends = column(p_total, p_home, p_away)
        
        layout = column(
            Div(text=f"<h2 style='text-align: center;'>{self.team_name} - Análisis de Rendimiento</h2>"),
            donas,
            results_table,
            trends
        )

        show(layout)



    def plot_performance_trends(self):
        """
        Genera gráficos de línea interactivos para el rendimiento total, de local y de visitante.
        Muestra información de cada partido al pasar el mouse sobre los puntos.
        """

        output_notebook()

        # Inicializar listas para almacenar datos
        match_numbers = []
        total_performance = []
        home_performance = []
        away_performance = []
        tooltips_total = []
        tooltips_home = []
        tooltips_away = []

        total_score = 0
        home_score = 0
        away_score = 0

        # Ordenar los partidos por jornada
        sorted_matches = sorted(self.matches, key=lambda x: x.matchday_id)

        # Variables para llevar el conteo de partidos en casa y fuera
        home_match_number = 0
        away_match_number = 0

        for idx, match in enumerate(sorted_matches):
            match_numbers.append(idx + 1)

            if match.home_team_id == self.team_id:
                home_match_number += 1
                if match.home_score > match.away_score:
                    total_score += 1
                    home_score += 1
                elif match.home_score == match.away_score:
                    pass  # Empate, no cambia el puntaje
                else:
                    total_score -= 1
                    home_score -= 1
                # Información del partido
                opponent = self.get_team_name(match.away_team_id)
                result = f"{self.team_name} {match.home_score} - {match.away_score} {opponent}"
                tooltips_total.append(f"Jornada {int(match.matchday_id) - (50*self.season_id)}: {result}")
                tooltips_home.append(f"Jornada {int(match.matchday_id) - (50*self.season_id)}: {result}")
                tooltips_away.append(None)  # No hay datos para partidos fuera
                total_performance.append(total_score)
                home_performance.append(home_score)
            else:
                away_match_number += 1
                if match.away_score > match.home_score:
                    total_score += 1
                    away_score += 1
                elif match.away_score == match.home_score:
                    pass  # Empate, no cambia el puntaje
                else:
                    total_score -= 1
                    away_score -= 1
                # Información del partido
                opponent = self.get_team_name(match.home_team_id)
                result = f"{opponent} {match.home_score} - {match.away_score} {self.team_name}"
                tooltips_total.append(f"Jornada {int(match.matchday_id) - (50*self.season_id)}: {result}")
                tooltips_home.append(None)  # No hay datos para partidos en casa
                tooltips_away.append(f"Jornada {int(match.matchday_id) - (50*self.season_id)}: {result}")
                total_performance.append(total_score)
                away_performance.append(away_score)

        # Crear ColumnDataSource para cada gráfico
        source_total = ColumnDataSource(data=dict(
            x=match_numbers,
            y=total_performance,
            desc=tooltips_total
        ))

        source_home = ColumnDataSource(data=dict(
            x=list(range(1, home_match_number + 1)),
            y=home_performance,
            desc=[d for d in tooltips_home if d is not None]
        ))

        source_away = ColumnDataSource(data=dict(
            x=list(range(1, away_match_number + 1)),
            y=away_performance,
            desc=[d for d in tooltips_away if d is not None]
        ))

        # Crear herramientas de hover
        hover_total = HoverTool(tooltips=[("Info", "@desc")])
        hover_home = HoverTool(tooltips=[("Info", "@desc")])
        hover_away = HoverTool(tooltips=[("Info", "@desc")])

        # Gráfico de rendimiento total
        p_total = figure(title=f"Rendimiento Total de {self.team_name}", x_axis_label='Partidos', y_axis_label='Rendimiento',
                        width=700, height=300)
        p_total.line('x', 'y', source=source_total, line_width=2, color='blue')
        p_total.scatter('x', 'y', source=source_total, size=8, color='blue', marker='circle')
        p_total.add_tools(hover_total)

        # Gráfico de rendimiento en casa
        p_home = figure(title=f"Rendimiento en Casa de {self.team_name}", x_axis_label='Partidos en Casa', y_axis_label='Rendimiento',
                        width=700, height=300)
        p_home.line('x', 'y', source=source_home, line_width=2, color='green')
        p_home.scatter('x', 'y', source=source_home, size=8, color='green', marker='circle')
        p_home.add_tools(hover_home)

        # Gráfico de rendimiento como visitante
        p_away = figure(title=f"Rendimiento como Visitante de {self.team_name}", x_axis_label='Partidos como Visitante', y_axis_label='Rendimiento',
                        width=700, height=300)
        p_away.line('x', 'y', source=source_away, line_width=2, color='red')
        p_away.scatter('x', 'y', source=source_away, size=8, color='red', marker='circle')
        p_away.add_tools(hover_away)

        # Organizar los gráficos en una cuadrícula
        grid = gridplot([[p_total], [p_home], [p_away]])

        show(grid)


    def get_team_name(self, team_id):
        """
        Obtiene el nombre de un equipo dado su ID dentro de la temporada.
        """
        for team in self.season.teams:
            if team.team_id == team_id:
                return team.team_name
        return "Desconocido"
        
    def display_top_players(self, top_n=10):
        """
        Muestra un gráfico interactivo de los mejores jugadores del equipo en diferentes categorías utilizando Bokeh.
        """
        
        # Crear DataFrame con las estadísticas relevantes para los jugadores del equipo
        data = {
            'Player': [player.player_name for player in self.players],
            'Position': [player.position for player in self.players],
            'Goals': [int(player.stats.get('goles', 0)) for player in self.players],
            'Assists': [int(player.stats.get('asistencias', 0)) for player in self.players],
            'Key_Passes': [int(player.stats.get('pases_claves', 0)) for player in self.players],
            'Goals_Conceded': [int(player.stats.get('goles_recibidos', 0)) for player in self.players],
            'Fouls_Committed': [int(player.stats.get('faltas_cometidas', 0)) for player in self.players],
            'Big_Chances_Scored': [int(player.stats.get('big_chances_scored', 0)) for player in self.players],
            'Missed_Chances': [int(player.stats.get('chances_perdidas', 0)) for player in self.players]
        }
        
        df = pd.DataFrame(data)
        
        # Definir las categorías disponibles y sus títulos
        categories = {
            'Goals': 'Máximos Goleadores',
            'Assists': 'Máximos Asistidores',
            'Key_Passes': 'Jugadores con Más Pases Clave',
            'Goals_Conceded': 'Jugadores con Más Goles Recibidos',
            'Fouls_Committed': 'Jugadores con Más Faltas Cometidas',
            'Big_Chances_Scored': 'Jugadores con Más Grandes Ocasiones Anotadas',
            'Missed_Chances': 'Jugadores con Más Ocasiones Perdidas'
        }
        
        # Categoría inicial
        initial_category = 'Goals'
        
        # Asignar colores a las posiciones (opcional)
        positions = df['Position'].unique()
        palette = Category20c[20] if len(positions) > 20 else Category20[len(positions)]
        color_map = {position: color for position, color in zip(positions, palette)}
        df['Color'] = df['Position'].map(color_map)
        
        # Ordenar y seleccionar los mejores jugadores para la categoría inicial
        top_players = df.sort_values(by=initial_category, ascending=False).head(top_n)
        
        # Crear ColumnDataSource con todos los datos necesarios
        source = ColumnDataSource(data=dict(
            player=top_players['Player'].tolist(),
            position=top_players['Position'].tolist(),
            value=top_players[initial_category].tolist(),
            color=top_players['Color'].tolist(),
            Goals=top_players['Goals'].tolist(),
            Assists=top_players['Assists'].tolist(),
            Key_Passes=top_players['Key_Passes'].tolist(),
            Goals_Conceded=top_players['Goals_Conceded'].tolist(),
            Fouls_Committed=top_players['Fouls_Committed'].tolist(),
            Big_Chances_Scored=top_players['Big_Chances_Scored'].tolist(),
            Missed_Chances=top_players['Missed_Chances'].tolist()
        ))
        
        # Crear figura de Bokeh
        p = figure(x_range=top_players['Player'].tolist(), height=600, title=categories[initial_category],
                   toolbar_location=None, tools="")
        
        # Añadir gráfico de barras
        p.vbar(x='player', top='value', width=0.9, source=source, line_color='white', fill_color='color')
        
        # Personalizar gráfico
        p.xgrid.grid_line_color = None
        p.y_range.start = 0
        p.xaxis.major_label_orientation = 1.2  # Rotar etiquetas del eje x
        
        # Mapear nombres de categorías para JavaScript
        category_columns = {
            'Goals': 'Goals',
            'Assists': 'Assists',
            'Key_Passes': 'Key_Passes',
            'Goals_Conceded': 'Goals_Conceded',
            'Fouls_Committed': 'Fouls_Committed',
            'Big_Chances_Scored': 'Big_Chances_Scored',
            'Missed_Chances': 'Missed_Chances'
        }
        
        # Crear menú desplegable
        select = Select(title="Categoría:", value=initial_category, options=list(categories.keys()))
        
        # Crear callback JavaScript
        callback = CustomJS(args=dict(source=source, p=p, df=df.to_dict('list'), categories=categories, category_columns=category_columns, top_n=top_n), code="""
            var data = source.data;
            var category = cb_obj.value;
            var column_name = category_columns[category];
            
            // Obtener todos los datos
            var all_data = df;
            
            // Combinar datos en un solo arreglo
            var data_list = [];
            for (var i = 0; i < all_data['Player'].length; i++) {
                data_list.push({
                    'player': all_data['Player'][i],
                    'position': all_data['Position'][i],
                    'value': all_data[column_name][i],
                    'color': all_data['Color'][i],
                    'Goals': all_data['Goals'][i],
                    'Assists': all_data['Assists'][i],
                    'Key_Passes': all_data['Key_Passes'][i],
                    'Goals_Conceded': all_data['Goals_Conceded'][i],
                    'Fouls_Committed': all_data['Fouls_Committed'][i],
                    'Big_Chances_Scored': all_data['Big_Chances_Scored'][i],
                    'Missed_Chances': all_data['Missed_Chances'][i]
                });
            }
        
            // Ordenar y obtener los top_n
            data_list.sort(function(a, b) { return b['value'] - a['value']; });
            data_list = data_list.slice(0, top_n);
        
            // Actualizar datos en source
            data['player'] = data_list.map(function(item) { return item['player']; });
            data['position'] = data_list.map(function(item) { return item['position']; });
            data['value'] = data_list.map(function(item) { return item['value']; });
            data['color'] = data_list.map(function(item) { return item['color']; });
        
            // Actualizar todas las categorías
            for (var key in category_columns) {
                var col = category_columns[key];
                data[col] = data_list.map(function(item) { return item[col]; });
            }
        
            // Actualizar rango del eje x y título
            p.x_range.factors = data['player'];
            p.title.text = categories[category];
        
            source.change.emit();
        """)
        
        select.js_on_change('value', callback)
        
        # Mostrar todo en un layout
        layout = column(select, p)
        show(layout)
class Player:
    def __init__(self, player_id, team_id, player_name, jersey_number, season_id, position, stats=None):
        self.player_id = player_id
        self.team_id = team_id
        self.player_name = player_name
        self.jersey_number = jersey_number
        self.season_id = season_id
        self.position = position
        self.stats = stats or {}  # Diccionario para estadísticas básicas
    
    def display_player_info(self):
        """
        Muestra la información básica del jugador y sus estadísticas.
        """
        print(f"Jugador: {self.player_name} - Posición: {self.position} - Número: {self.jersey_number}")
        print(f"Goles: {self.stats.get('goles', 0)}, Asistencias: {self.stats.get('asistencias', 0)}, "
              f"Pases Claves: {self.stats.get('pases_claves', 0)}, Goles Recibidos: {self.stats.get('goles_recibidos', 0)}\n")
    
    def display_detailed_stats(self, connection):
        """
        Muestra las estadísticas detalladas del jugador, cargando los datos desde MySQL.
        """
        cursor = connection.cursor()
        
        # Obtener todas las columnas de estadísticas disponibles en player_stats
        cursor.execute("SHOW COLUMNS FROM player_stats")
        columns_info = cursor.fetchall()
        stat_columns = [col[0] for col in columns_info if col[0] not in ['player_id', 'team_id', 'match_id']]
        
        # Construir la consulta SQL para obtener las estadísticas del jugador
        query = f"""
        SELECT {', '.join(stat_columns)}
        FROM player_stats
        WHERE player_id = %s AND team_id = %s
        """
        cursor.execute(query, (self.player_id, self.team_id))
        stats_data = cursor.fetchall()
        
        # Verificar si hay datos disponibles
        if not stats_data:
            print(f"No hay estadísticas detalladas disponibles para {self.player_name}.")
            cursor.close()
            return
        
        # Calcular las estadísticas totales
        total_stats = {col: 0 for col in stat_columns}
        for row in stats_data:
            for idx, value in enumerate(row):
                total_stats[stat_columns[idx]] += int(value or 0)
        
        cursor.close()
        
        # Crear un DataFrame para mostrar las estadísticas
        df_stats = pd.DataFrame(list(total_stats.items()), columns=['Estadística', 'Valor'])
        
        # Mostrar las estadísticas en una tabla
        display(HTML(f"<h3>Estadísticas detalladas de {self.player_name}</h3>"))
        display(df_stats)

class Match:
    def __init__(self, match_id, matchday_id, home_team_id, away_team_id, home_score, away_score, duration):
        self.match_id = match_id
        self.matchday_id = matchday_id
        self.home_team_id = home_team_id
        self.away_team_id = away_team_id
        self.home_score = home_score
        self.away_score = away_score
        self.duration = duration

class Versus:
    def __init__(self, home_team_id, away_team_id, standings):
        self.home_team_id = home_team_id
        self.away_team_id = away_team_id
        self.standings = standings
        
    def check_derby(self, teams_info):
        """
        Verifica si el enfrentamiento es un derbi (mismos equipos en la misma ciudad).

        Parámetros:
        - teams_info (pd.DataFrame): DataFrame con información de equipos (team_id, city).

        Retorna:
        - bool: True si es un derbi, False en caso contrario.
        """
        home_city = teams_info.loc[teams_info['team_id'] == self.home_team_id, 'city'].values[0]
        away_city = teams_info.loc[teams_info['team_id'] == self.away_team_id, 'city'].values[0]
        
        return home_city == away_city

    def analyze_match(self):
        """
        Analiza la diferencia de posiciones entre los equipos en las standings.

        Retorna:
        - str: Una categoría de dificultad del partido.
        """
        home_team_position = self.standings.loc[self.standings['Equipo'] == self.home_team_id, 'Posicion'].astype(int).values[0]
        away_team_position = self.standings.loc[self.standings['Equipo'] == self.away_team_id, 'Posicion'].astype(int).values[0]

        position_diff = abs(home_team_position - away_team_position)

        if position_diff > 15:
            return "Partido fácil"
        elif position_diff < 4:
            return "Partido difícil"
        elif home_team_position > 10 and away_team_position > 10:
            return "Accesible"
        elif home_team_position <= 4 and away_team_position <= 10:
            return "Manejable"
        else:
            return "Neutro"

    def display_analysis(self, teams_info):
        """
        Muestra el análisis del partido usando Matplotlib.

        Parámetros:
        - teams_info (pd.DataFrame): DataFrame con información de equipos (team_id, team_name, city).
        """
        import matplotlib.pyplot as plt

        home_team_name = teams_info.loc[teams_info['team_id'] == self.home_team_id, 'team_name'].values[0]
        away_team_name = teams_info.loc[teams_info['team_id'] == self.away_team_id, 'team_name'].values[0]

        derby = self.check_derby(teams_info)
        analysis = self.analyze_match()

        title = f"Análisis del partido: {home_team_name} vs {away_team_name}"
        subtitle = f"Categoría: {analysis} {'(Derbi)' if derby else ''}"

        # Crear el gráfico
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.6, title, ha='center', va='center', fontsize=14, fontweight='bold')
        ax.text(0.5, 0.4, subtitle, ha='center', va='center', fontsize=12)
        ax.axis('off')
        plt.show()
