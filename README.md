# POSITREN
This project consists of a Python script to monitor and log delays on the FGC and Rodalies/Renfe train lines in Catalonia.

## Features

- Monitors FGC and Rodalies/Renfe train lines.
- Logs delays in a file (`renfepy.log`).
- Uses the `renfepy` library to obtain data for Rodalies/Renfe.
- Contains a list of Rodalies stations in `rodalies_stations.csv`.

## Requirements

The necessary libraries to run the script are listed in the `requirements.txt` file:

- `beautifulsoup4==4.12.3`
- `feedparser==6.0.11`
- `renfepy==0.2.1`
- `requests==2.31.0`

You can install them using pip:

```bash
pip install -r requirements.txt
```

## Usage

To run the script, simply execute the following command in your terminal:

```bash
python monitor_trenes.py
```

# Monitor de Retrasos de Trenes (FGC y Rodalies/Renfe)

Este proyecto consiste en un script de Python para monitorizar y registrar los retrasos en las líneas de tren de FGC y Rodalies/Renfe en Cataluña.

## Características

- Monitoriza las líneas de tren de FGC y Rodalies/Renfe.
- Registra los retrasos en un archivo (`renfepy.log`).
- Utiliza la librería `renfepy` para obtener los datos de Rodalies/Renfe.
- Contiene un listado de las estaciones de Rodalies en `rodalies_stations.csv`.

## Requisitos

Las librerías necesarias para ejecutar el script se encuentran en el archivo `requirements.txt`:

- `beautifulsoup4==4.12.3`
- `feedparser==6.0.11`
- `renfepy==0.2.1`
- `requests==2.31.0`

Puedes instalarlas usando pip:

```bash
pip install -r requirements.txt
```

## Uso

Para ejecutar el script, simplemente ejecuta el siguiente comando en tu terminal:

```bash
python monitor_trenes.py
```
