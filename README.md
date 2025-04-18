# AviationStack Tracking Project

Project for receiving and displaying information about flights over the Black Sea using API [AviationStack](https://aviationstack.com/).

## Stack

- Python
- PostgreSQL
- Docker
- Pandas
- Dash + Plotly 

## How to run a project

### 1. Clone this repository

```
git clone https://github.com/ShadowLancel/task-greenatom.git
cd aviationstack-task
```
### 2. Set up the .env file
Change the API key in `.env` file to your key obtained from https://aviationstack.com/
Example .env file is available in this repository

### 3. Launching containers
```
docker-compose up --build -d
```
The app service will collect and load data from the API into the DB once. The dashboard service will launch the Dash web interface on port 8050

### 4. Open the dashboard
Go to the address `http://localhost:8050` or `http://127.0.0.1:8050/` in your browser and make sure that the table with the number of flights and the map with routes are displayed.

### 4. Stop containers
```
docker-compose down
```

## Run locally (without Docker)

1. Install Python 3.13 and PostgreSQL.
2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate   # Linux/Mac
   Set-ExecutionPolicy        # If you use Windows PowerShell
   venv\Scripts\activate      # Windows
   ```
3. Install requirements:
   ```
   pip install -r requirements.txt
   ```
4. Config .env (see above step 2 in the guide to starting a project with docker).

5. Initialize the DB schema:
   ```
   psql -h <DB_HOST> -U <DB_USER> -d <DB_NAME> -f schema.sql
   ```
6. Run the data import once:
   ```
   python fetch_data.py
   ```
7. Launch Dashboard and open the Dashboard:
   ```
   python dashboard.py
   ```
   Go to the address `http://localhost:8050` or `http://127.0.0.1:8050/` in your browser.
