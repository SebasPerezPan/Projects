import json
import pandas as pd
import pymysql as sql
from typing import List, Tuple, Dict
from datetime import datetime

class DatabaseManager:
    def __init__(self, config_path: str):
        with open(config_path) as f:
            config = json.load(f)
        self.config = config
        self.connection = None
        
    def connect(self):
        try:
            self.connection = sql.connect(
                user=self.config['DB_USER'],
                password=self.config['DB_PASSWORD'],
                host=self.config['DB_HOST'],
                database=self.config['DB_NAME']
            )
            return self.connection
        except Exception as e:
            raise ConnectionError(f"Error conectando a la base de datos: {e}")

    def close(self):
        if self.connection:
            self.connection.close()

    def insertar_proveedor(self, informacion_proveedor: Tuple[str, str, str, str, str]) -> None:
        proveedor, nit, telefono, direccion, correo = informacion_proveedor
        
        query = """
            INSERT INTO proveedores (proveedor, nit, telefono, direccion, correo_electronico) 
            VALUES (%s, %s, %s, %s, %s)
        """
        
        with self.connection.cursor() as cursor:
            try:
                cursor.execute(query, (proveedor, nit, telefono, direccion, correo))
                self.connection.commit()
            except sql.Error as e:
                self.connection.rollback()
                raise Exception(f"Error insertando proveedor: {e}")

    def insertar_cliente(self, informacion_cliente: Tuple[str, str, str, str, str, str]) -> None:
        cliente, telefono, correo, identificacion, direccion, notas = informacion_cliente
        
        query = """
            INSERT INTO clientes (cliente, telefono, correo_electronico, identificacion, 
                              direccion, notas)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        with self.connection.cursor() as cursor:
            try:
                cursor.execute(query, (cliente, telefono, correo, identificacion, 
                                     direccion, notas))
                self.connection.commit()
            except sql.Error as e:
                self.connection.rollback()
                raise Exception(f"Error insertando cliente: {e}")

    def insertar_inventario(self, df_inventario: pd.DataFrame) -> None:
        query = """
            INSERT INTO inventario (producto, categoria, cantidad, proveedor, 
                                precio, precio_unidad, precio_venta, precio_compra,
                                fecha_ingreso)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        with self.connection.cursor() as cursor:
            try:
                for _, row in df_inventario.iterrows():
                    valores = (
                        row['producto'], row['categoria'], row['cantidad'],
                        row['proveedor'], row['precio'], row['precio_unidad'],
                        row['precio_venta'], row['precio_compra'],
                        datetime.now()
                    )
                    cursor.execute(query, valores)
                self.connection.commit()
            except sql.Error as e:
                self.connection.rollback()
                raise Exception(f"Error insertando inventario: {e}")

    def insertar_venta(self, df_venta: pd.DataFrame, id_factura: int) -> None:
        query_venta = """
            INSERT INTO ventas (producto, cantidad, valor, id_factura, fecha_egreso)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        query_inventario = """
            UPDATE inventario 
            SET cantidad = cantidad - %s 
            WHERE producto = %s
        """
        
        with self.connection.cursor() as cursor:
            try:
                for _, row in df_venta.iterrows():
                    # Verificar stock
                    cursor.execute(
                        "SELECT cantidad FROM inventario WHERE producto = %s",
                        (row['producto'],)
                    )
                    stock_actual = cursor.fetchone()[0]
                    
                    if stock_actual < row['cantidad']:
                        raise ValueError(
                            f"Stock insuficiente para {row['producto']}"
                        )
                
                    # Insertar venta
                    cursor.execute(query_venta, (
                        row['producto'], row['cantidad'], row['valor'],
                        id_factura, datetime.now()
                    ))
                    
                    # Actualizar inventario
                    cursor.execute(query_inventario, (
                        row['cantidad'], row['producto']
                    ))
                
                self.connection.commit()
            except Exception as e:
                self.connection.rollback()
                raise Exception(f"Error procesando venta: {e}")