import os
import psycopg2
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, html, dcc

# подключение к БД
DB_HOST     = os.getenv("DB_HOST")
DB_PORT     = os.getenv("DB_PORT")
DB_NAME     = os.getenv("DB_NAME")
DB_USER     = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

try:
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cursor = conn.cursor()
except psycopg2.Error as e:
    print(f"Ошибка при подключении к базе данных: {e}")
    exit(1)

# получаем данные из представления daily_flights
cursor.execute("SELECT model_name, airline_name, flight_count FROM daily_flights")
rows = cursor.fetchall()
df = pd.DataFrame(rows, columns=["Model", "Airline", "Flight Count"])

# получаем данные о рейсах для карты
cursor.execute("""
    SELECT 
      f.icao_code,
      f.departure_airport,
      f.arrival_airport,
      f.dep_iata,
      f.arr_iata,
      dep.latitude   AS dep_lat,
      dep.longitude  AS dep_lon,
      arr.latitude   AS arr_lat,
      arr.longitude  AS arr_lon
    FROM flights f
    JOIN airports dep ON f.dep_iata = dep.iata_code
    JOIN airports arr ON f.arr_iata = arr.iata_code
    WHERE f.timestamp >= CURRENT_DATE
      AND f.timestamp <  CURRENT_DATE + INTERVAL '1 day'
""")

flight_routes = cursor.fetchall()
routes_df = pd.DataFrame(flight_routes, columns=["icao_code", "departure", "arrival", "dep_iata", "arr_iata", "dep_lat", "dep_lon", "arr_lat", "arr_lon"])

cursor.close()
conn.close()

# создаём таблицу для отображения
fig_table = go.Figure(data=[go.Table(
    header=dict(values=["Model", "Airline", "Flight Count"],
                fill_color="paleturquoise",
                align="left"),
    cells=dict(values=[df["Model"], df["Airline"], df["Flight Count"]],
               fill_color="lavender",
               align="left"))
])

# создаём карту с маршрутами
fig_map = go.Figure()

# добавляем маршруты как линии
for _, route in routes_df.iterrows():
    fig_map.add_trace(go.Scattermapbox(
        lat=[route["dep_lat"], route["arr_lat"]],
        lon=[route["dep_lon"], route["arr_lon"]],
        mode="lines+markers+text",
        line=dict(width=2, color="blue"),
        marker=dict(size=10),
        text=[route["dep_iata"], route["arr_iata"]],
        textposition="top center",
        name=route["icao_code"],
        hoverinfo="text",
        hovertext=f"{route['icao_code']}: {route['departure']} → {route['arrival']}"
    ))

# настраиваем стиль карты
fig_map.update_layout(
    mapbox=dict(
        style="open-street-map",
        center=dict(lat=43, lon=34),  # центр Чёрного моря
        zoom=5
    ),
    showlegend=True,
    height=600
)

# создаём приложение Dash
app = Dash(__name__)

app.layout = html.Div([
    html.H1("Flight Dashboard"),
    html.H2("Daily Flight Statistics"),
    dcc.Graph(figure=fig_table),
    html.H2("Flight Routes"),
    dcc.Graph(figure=fig_map)
])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050)