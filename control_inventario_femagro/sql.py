import json

import pandas as pd
import pymysql as sql

with open('/home/sp3767/Documents/files/ferreteria.json') as f:
    config = json.load(f)

connection = sql.connect(
    user=config['DB_USER'],
    password=config['DB_PASSWORD'],
    host=config['DB_HOST'],
    database=config['DB_NAME']
    )

# Metodos de insersion:

def insertar_proveedor(connection, informacion_proveedor):
    
    # Paso 2: Crear el cursor y la consulta SQL
    cursor = connection.cursor()
    insert_query = "INSERT INTO proveedores (proveedor, nit, telefono, direccion, correo_electronico) VALUES (%s, %s, %s, %s, %s)"
    
    try:
        # Paso 3: Ejecutar la consulta con el nombre formateado
        cursor.execute(insert_query, (formatted_league,))
        connection.commit()
        print(f"La liga '{formatted_league.replace('_', ' ').title()}' ha sido insertada correctamente.")
        
    except Exception as e:
        print(f"Error al insertar la liga: {e}")
    
    finally:
        cursor.close()

