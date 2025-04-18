-- удаляем старые объекты
DROP VIEW IF EXISTS daily_flights;
DROP TABLE IF EXISTS flights CASCADE;
DROP TABLE IF EXISTS aircraft_models CASCADE;
DROP TABLE IF EXISTS airlines CASCADE;
DROP TABLE IF EXISTS airports CASCADE;

-- справочник аэропортов (Black Sea)
CREATE TABLE airports (
  iata_code      VARCHAR(3) PRIMARY KEY,
  name           TEXT         NOT NULL,
  latitude       FLOAT        NOT NULL,
  longitude      FLOAT        NOT NULL
);

-- вставляем основные аэропорты Черного моря
INSERT INTO airports (iata_code, name, latitude, longitude) VALUES
  ('IST','Istanbul Airport',           41.2753, 28.7519),
  ('SAW','Sabiha Gokcen International',40.8986, 29.3092),
  ('AER','Sochi International Airport',43.4499, 39.9566),
  ('TBS','Tbilisi International Airport',41.6692, 44.9545)
ON CONFLICT (iata_code) DO NOTHING;

-- справочники для авиакомпаний и моделей
CREATE TABLE airlines (
  id   SERIAL      PRIMARY KEY,
  name VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE aircraft_models (
  id         SERIAL      PRIMARY KEY,
  model_name VARCHAR(255) UNIQUE NOT NULL
);

-- таблица рейсов
CREATE TABLE flights (
  id                  SERIAL      PRIMARY KEY,
  callsign            VARCHAR(10),
  icao_code           VARCHAR(10),
  aircraft_model_id   INT         REFERENCES aircraft_models(id),
  airline_id          INT         REFERENCES airlines(id),
  departure_airport   VARCHAR(255),
  arrival_airport     VARCHAR(255),
  timestamp           TIMESTAMP WITH TIME ZONE,
  dep_iata            VARCHAR(3)  REFERENCES airports(iata_code),
  arr_iata            VARCHAR(3)  REFERENCES airports(iata_code),
  current_latitude    FLOAT,
  current_longitude   FLOAT,
  altitude            FLOAT,
  speed_horizontal    FLOAT,
  direction           FLOAT
);
-- витрина данных
CREATE OR REPLACE VIEW daily_flights AS
SELECT
  am.model_name,
  al.name        AS airline_name,
  COUNT(f.id)    AS flight_count
FROM flights f
JOIN aircraft_models am ON f.aircraft_model_id = am.id
JOIN airlines al        ON f.airline_id          = al.id
WHERE f.timestamp >= NOW() - INTERVAL '1 day'
GROUP BY am.model_name, al.name;