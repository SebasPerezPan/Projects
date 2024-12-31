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
    proveedor, nit, telefono, direccion, correo_electronico = informacion_proveedor
    # Paso 2: Crear el cursor y la consulta SQL
    cursor = connection.cursor()
    insert_query = "INSERT INTO proveedores (proveedor, nit, telefono, direccion, correo_electronico) VALUES (%s, %s, %s, %s, %s)"
    
    try:
        # Paso 3: Ejecutar la consulta con el nombre formateado
        cursor.execute(insert_query, (proveedor, nit, telefono, direccion, correo_electronico))
        connection.commit()
        print(f"El proveedor '{proveedor.replace('_', ' ').title()}' ha sido insertado correctamente.\nNIT: {nit}, telefono: {telefono}, direccion: {direccion}, correo_electronico: {correo_electronico}.")
        
    except Exception as e:
        print(f"Error al insertar proveedor: {e}")
    
    finally:
        cursor.close()

def insertar_cliente(connection, informacion_cliente):
    cliente, telefono, correo_electronico, identificacion, direccion, notas = informacion_cliente
    # Paso 2: Crear el cursor y la consulta SQL
    cursor = connection.cursor()
    insert_query = "INSERT INTO proveedores (cliente, telefono, correo_electronico, identificacion, direccion, notas) VALUES (%s, %s, %s, %s, %s, %s)"
    
    try:
        # Paso 3: Ejecutar la consulta con el nombre formateado
        cursor.execute(insert_query, (cliente, telefono, correo_electronico, identificacion, direccion, notas))
        connection.commit()
        print(f"El cliente '{cliente.replace('_', ' ').capitalize}' ha sido insertado correctamente.\ntelefono: {telefono}, correo_electronico: {correo_electronico}, identificacion: {identificacion}, direccion: {direccion}, notas: {notas}")
        
    except Exception as e:
        print(f"Error al insertar proveedor: {e}")
    
    finally:
        cursor.close()

def insertar_inventario(connection, dataframe_inventario):
    cursor = connection.cursor()
    insert_query = "INSERT INTO inventario (producto, categoria, cantidad, proveedor, precio, precio_unidad, precio_venta, precio_compra) VALUES (%s, %s, %s, %s, %s, %s)"
    
    data_to_insert = list(dataframe_inventario[['producto', 'categoria', 'cantidad', "proveedor", "precio", "precio_unidad", "precio_venta", "precio_compra"]].itertuples(index=False, name=None))

    try:
        # Paso 3: Ejecutar la consulta con el nombre formateado
        cursor.execute(insert_query, data_to_insert)
        connection.commit()
        print(f"Insersión completada de los productos en el inventario.")
        
    except Exception as e:
        print(f"Error al insertar proveedor: {e}")
    
    finally:
        cursor.close()

def insertar_ventas(connection, dataframe_venta):

    cursor = connection.cursor()
    insert_query = "INSERT INTO ventas (producto, cantidad, valor, id_factura) VALUES (%s, %s, %s, %s, %s, %s)" 
    
    data_to_insert = list(dataframe_venta[['producto', 'cantidad', "valor", "id_factura"]].itertuples(index=False, name=None))

    try:
        # Paso 3: Ejecutar la consulta con el nombre formateado
        cursor.execute(insert_query, data_to_insert)
        connection.commit()
        print(f"Insersión completada de los productos en el inventario.")
        actualizar_inventario(connection, dataframe_venta)

    except Exception as e:
        print(f"Error al insertar proveedor: {e}")
    
    finally:
        cursor.close()

def actualizar_inventario(connection, dataframe_venta):

    cursor = connection.cursor()
    
    for _, venta in dataframe_venta.iterrows():
        query = """
            UPDATE inventario 
            SET cantidad = cantidad - %s 
            WHERE producto = %s
        """
        cursor.execute(query, (venta['cantidad'], venta['producto']))
    
    connection.commit()
    cursor.close()