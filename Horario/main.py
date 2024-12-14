import pandas as pd
pd.set_option('display.max_rows', None)
# pd.set_option('display.max_columns', None)

# Leer el archivo Excel
archivo_excel = "Oferta pregrados EICT 2025-1 estudiantes.xlsx"  # Reemplaza con la ruta de tu archivo

df = pd.read_excel(archivo_excel)
df.drop(df.columns[[0,16,15,17,18]], axis=1, inplace=True)
df.drop(index=[165, 164,163,162,161], inplace=True)

df.rename(columns={"\nNOMBRE ASIGNATURA":"ASIGNATURA",'Unnamed: 6': 'LUNES_SALIDA','Unnamed: 8': 'MARTES_SALIDA','MIÉRCOLES': 'MIERCOLES','Unnamed: 10': 'MIERCOLES_SALIDA','Unnamed: 12': 'JUEVES_SALIDA','Unnamed: 14': 'VIERNES_SALIDA'}, inplace=True)

def obtener_primer_valor(valor):
    if pd.isna(valor):  # Si el valor es NaN
        return 0  # Retornar 0 si está vacío
    if valor == 'ELECTIVA':  # Si el valor es exactamente 'ELECTIVA'
        return 0
    if '-' in valor:  # Si es un rango, por ejemplo '5-7'
        inicio, _ = map(int, valor.split('-'))  # Tomar el inicio del rango
        return inicio
    if valor.isdigit():  # Si es un número en formato string, como '1'
        return int(valor)

df['SEMESTRE'] = df['SEMESTRE'].apply(obtener_primer_valor)

df_filtrado = df[df['SEMESTRE'] == 3]

print(df_filtrado.columns)

class semester:
    def __init__(self, MATERIAS, HORARIO,ASIGNATURAS_DISPONIBLES):
        self.materias = []
        self.horario = HORARIO
        self.asignaturas_disponibles = ASIGNATURAS_DISPONIBLES


class subject:
    def __init__(self, ASIGNATURA, SEMESTRE, GRUPO, HORARIO, CODIGO, DIAS):
        self.asignatura = ASIGNATURA
        self.codigo = CODIGO
        self.semestre = SEMESTRE
        self.grupo = GRUPO
        self.horario = HORARIO
        self.dias = DIAS
    
    def load_subjects(self):
        pass

def construir_horario(df):
    horarios_list = []
    dias = ['LUNES', 'MARTES', 'MIERCOLES', 'JUEVES', 'VIERNES']
    
    for index, row in df.iterrows():
        for dia in dias:
            if pd.notna(row[dia]) and pd.notna(row[f'{dia}_SALIDA']):
                horario = {
                    'DIA_A': dia,
                    'ENTRADA_A': row[dia],
                    'SALIDA_A': row[f'{dia}_SALIDA']
                }
                horarios_list.append(horario)
    
    return pd.DataFrame(horarios_list)

horario = construir_horario(df)

print(horario.columns)