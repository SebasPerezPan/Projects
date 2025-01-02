import json
import pandas as pd
import pymysql as sql
from typing import Tuple
from datetime import datetime

class DatabaseManager:
    def __init__(self, config_path: str):
        with open(config_path) as f:
            self.config = json.load(f)
        self.connection = None
        
    def connect(self):
        self.connection = sql.connect(
            user=self.config['DB_USER'],
            password=self.config['DB_PASSWORD'],
            host=self.config['DB_HOST'],
            database=self.config['DB_NAME']
        )
        return self.connection

    def close(self):
        if self.connection:
            self.connection.close()

    def insertar_proveedor(self, data: Tuple[str, str, str, str, str]) -> None:
        query = """
            INSERT INTO proveedores (proveedor, nit, telefono, direccion, correo_electronico) 
            VALUES (%s, %s, %s, %s, %s)
        """
        with self.connection.cursor() as cursor:
            try:
                cursor.execute(query, data)
                self.connection.commit()
            except sql.Error as e:
                self.connection.rollback()
                raise Exception(f"Error insertando proveedor: {e}")

    def insertar_cliente(self, data: Tuple[str, str, str, str, str, str]) -> None:
        query = """
            INSERT INTO clientes (cliente, telefono, correo_electronico, identificacion, 
                              direccion, notas)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        with self.connection.cursor() as cursor:
            try:
                cursor.execute(query, data)
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
                        row['producto'], row['categoria'], row.get('cantidad', 0),
                        row['proveedor'], row['precio'], row['precio_unidad'],
                        row['precio_venta'], row['precio_compra'],
                        datetime.now()
                    )
                    cursor.execute(query, valores)
                self.connection.commit()
            except sql.Error as e:
                self.connection.rollback()
                raise Exception(f"Error insertando inventario: {e}")

    def insertar_venta(self, df_venta: pd.DataFrame, cliente:str) -> None:
        valor_factura = df_venta['valor'].sum()
        id_factura = self.insertar_factura(valor_factura, cliente)

        query_venta = """
            INSERT INTO ventas (producto, cantidad, valor, id_factura, fecha_venta)
            VALUES (%s, %s, %s, %s, %s)
        """
        with self.connection.cursor() as cursor:
            try:
                for _, row in df_venta.iterrows():
                    cursor.execute(query_venta, (
                        row['producto'], row['cantidad'], row['valor'],
                        id_factura, datetime.now()
                    ))
                self.connection.commit()
            except sql.Error as e:
                self.connection.rollback()
                raise Exception(f"Error procesando venta: {e}")

    def insertar_factura(self, valor: float, cliente: str) -> int:
        query = """
            INSERT INTO factura (valor, cliente)
            VALUES (%s, %s)
        """
        with self.connection.cursor() as cursor:
            try:
                cursor.execute(query, (valor, cliente))
                self.connection.commit()
                return cursor.lastrowid
            except sql.Error as e:
                self.connection.rollback()
                raise Exception(f"Error creando factura: {e}")