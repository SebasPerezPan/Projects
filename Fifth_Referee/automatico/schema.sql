/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19-11.6.2-MariaDB, for Linux (x86_64)
--
-- Host: localhost    Database: football_project
-- ------------------------------------------------------
-- Server version	11.6.2-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*M!100616 SET @OLD_NOTE_VERBOSITY=@@NOTE_VERBOSITY, NOTE_VERBOSITY=0 */;

--
-- Table structure for table `competition`
--

DROP TABLE IF EXISTS `competition`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `competition` (
  `competition_id` int(11) NOT NULL AUTO_INCREMENT,
  `competition_name` varchar(20) NOT NULL,
  PRIMARY KEY (`competition_id`),
  UNIQUE KEY `competition_name` (`competition_name`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `football_game`
--

DROP TABLE IF EXISTS `football_game`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `football_game` (
  `match_id` int(11) NOT NULL,
  `matchday_id` int(11) DEFAULT NULL,
  `home_team_id` int(11) DEFAULT NULL,
  `away_team_id` int(11) DEFAULT NULL,
  `season_id` int(11) DEFAULT NULL,
  `home_score` int(11) DEFAULT NULL,
  `away_score` int(11) DEFAULT NULL,
  `duration` int(11) DEFAULT NULL,
  `insert_date` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`match_id`),
  KEY `home_team_id` (`home_team_id`,`season_id`),
  KEY `away_team_id` (`away_team_id`,`season_id`),
  KEY `matchday_id` (`matchday_id`),
  CONSTRAINT `football_game_ibfk_1` FOREIGN KEY (`home_team_id`, `season_id`) REFERENCES `team` (`team_id`, `season_id`),
  CONSTRAINT `football_game_ibfk_2` FOREIGN KEY (`away_team_id`, `season_id`) REFERENCES `team` (`team_id`, `season_id`),
  CONSTRAINT `football_game_ibfk_3` FOREIGN KEY (`matchday_id`) REFERENCES `matchday` (`matchday_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `matchday`
--

DROP TABLE IF EXISTS `matchday`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `matchday` (
  `matchday_id` int(11) NOT NULL,
  `season_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`matchday_id`),
  KEY `season_id` (`season_id`),
  CONSTRAINT `matchday_ibfk_1` FOREIGN KEY (`season_id`) REFERENCES `season` (`season_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `player`
--

DROP TABLE IF EXISTS `player`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `player` (
  `player_id` int(11) NOT NULL,
  `team_id` int(11) NOT NULL,
  `player_name` varchar(50) DEFAULT NULL,
  `jersey_number` int(11) DEFAULT NULL,
  `season_id` int(11) DEFAULT NULL,
  `position` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`player_id`,`team_id`),
  KEY `team_id` (`team_id`,`season_id`),
  CONSTRAINT `player_ibfk_1` FOREIGN KEY (`team_id`, `season_id`) REFERENCES `team` (`team_id`, `season_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `player_stats`
--

DROP TABLE IF EXISTS `player_stats`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `player_stats` (
  `player_id` int(11) NOT NULL,
  `team_id` int(11) NOT NULL,
  `season_id` int(11) NOT NULL,
  `match_id` int(11) NOT NULL,
  `asistencias` int(11) DEFAULT NULL,
  `asistencias_esperadas` double DEFAULT NULL,
  `barridas_ganadas` int(11) DEFAULT NULL,
  `barridas_totales` int(11) DEFAULT NULL,
  `big_chances_scored` int(11) DEFAULT NULL,
  `centros` int(11) DEFAULT NULL,
  `centros_totales` int(11) DEFAULT NULL,
  `chances_perdidas` int(11) DEFAULT NULL,
  `despeje_con_los_punos` int(11) DEFAULT NULL,
  `despejes` int(11) DEFAULT NULL,
  `despejes_por_alto` int(11) DEFAULT NULL,
  `duelos_aereos_ganados` int(11) DEFAULT NULL,
  `duelos_aereos_totales` int(11) DEFAULT NULL,
  `duelos_en_el_suelo_ganados` int(11) DEFAULT NULL,
  `duelos_en_el_suelo_totales` int(11) DEFAULT NULL,
  `error_que_llevo_al_gol` int(11) DEFAULT NULL,
  `errores_que_terminan_el_disparo` int(11) DEFAULT NULL,
  `faltas_cometidas` int(11) DEFAULT NULL,
  `faltas_recibidas` int(11) DEFAULT NULL,
  `fueras_de_juego` int(11) DEFAULT NULL,
  `goles` int(11) DEFAULT NULL,
  `goles_esperados` float DEFAULT NULL,
  `goles_esperados_al_arco_concedidos` float DEFAULT NULL,
  `goles_esperados_de_remates_al_arco` float DEFAULT NULL,
  `goles_esperados_evitados` float DEFAULT NULL,
  `goles_recibidos` int(11) DEFAULT NULL,
  `grandes_chances` int(11) DEFAULT NULL,
  `intercepciones` int(11) DEFAULT NULL,
  `jugo_como_libero` int(11) DEFAULT NULL,
  `minutes` int(11) DEFAULT NULL,
  `pases_claves` int(11) DEFAULT NULL,
  `pases_completados` int(11) DEFAULT NULL,
  `pases_en_el_ultimo_tercio` int(11) DEFAULT NULL,
  `pases_hacia_atras` int(11) DEFAULT NULL,
  `pases_largos_completados` int(11) DEFAULT NULL,
  `pases_largos_totales` int(11) DEFAULT NULL,
  `pases_totales` int(11) DEFAULT NULL,
  `pelotas_al_poste` int(11) DEFAULT NULL,
  `penal_fallado` int(11) DEFAULT NULL,
  `penales_atajados` int(11) DEFAULT NULL,
  `penales_cometidos` int(11) DEFAULT NULL,
  `penales_ganados` int(11) DEFAULT NULL,
  `penales_totales` int(11) DEFAULT NULL,
  `posesiones_ganadas_en_el_ultimo_tercio` int(11) DEFAULT NULL,
  `posesiones_perdidas` int(11) DEFAULT NULL,
  `recuperacion_de_la_posesion` int(11) DEFAULT NULL,
  `regateado` int(11) DEFAULT NULL,
  `regates` int(11) DEFAULT NULL,
  `regates_totales` int(11) DEFAULT NULL,
  `remates_a_puerta` int(11) DEFAULT NULL,
  `remates_bloqueados` int(11) DEFAULT NULL,
  `remates_fuera` int(11) DEFAULT NULL,
  `salvadas_de_portero` int(11) DEFAULT NULL,
  `salvadas_en_el_area` int(11) DEFAULT NULL,
  `toques` int(11) DEFAULT NULL,
  `total_remates` int(11) DEFAULT NULL,
  PRIMARY KEY (`player_id`,`team_id`,`season_id`,`match_id`),
  KEY `team_id` (`team_id`,`season_id`),
  KEY `match_id` (`match_id`),
  CONSTRAINT `player_stats_ibfk_1` FOREIGN KEY (`player_id`, `team_id`) REFERENCES `player` (`player_id`, `team_id`) ON DELETE CASCADE,
  CONSTRAINT `player_stats_ibfk_2` FOREIGN KEY (`team_id`, `season_id`) REFERENCES `team` (`team_id`, `season_id`) ON DELETE CASCADE,
  CONSTRAINT `player_stats_ibfk_3` FOREIGN KEY (`match_id`) REFERENCES `football_game` (`match_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `season`
--

DROP TABLE IF EXISTS `season`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `season` (
  `season_id` int(11) NOT NULL AUTO_INCREMENT,
  `competition_id` int(11) DEFAULT NULL,
  `season_name` varchar(20) NOT NULL,
  PRIMARY KEY (`season_id`),
  KEY `competition_id` (`competition_id`),
  CONSTRAINT `season_ibfk_1` FOREIGN KEY (`competition_id`) REFERENCES `competition` (`competition_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `team`
--

DROP TABLE IF EXISTS `team`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `team` (
  `team_id` int(11) NOT NULL,
  `season_id` int(11) NOT NULL,
  `team_name` varchar(25) NOT NULL,
  PRIMARY KEY (`team_id`,`season_id`),
  KEY `season_id` (`season_id`),
  CONSTRAINT `team_ibfk_1` FOREIGN KEY (`season_id`) REFERENCES `season` (`season_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*M!100616 SET NOTE_VERBOSITY=@OLD_NOTE_VERBOSITY */;

-- Dump completed on 2024-12-16  1:13:43
