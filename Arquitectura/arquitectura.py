from bokeh.plotting import figure, show
from bokeh.io import output_notebook
from bokeh.models import ColumnDataSource, DataTable, TableColumn, HTMLTemplateFormatter
from bokeh.palettes import Spectral10
from bokeh.transform import cumsum
from bokeh.layouts import column, row
from math import pi

output_notebook()  # Habilitar Bokeh en el notebook

# Datos de componentes
componentes = ['ESP 32 WIFI BLUETOOTH', 'DAC', 'JACK OUTPUT', "LECTOR SD", "PROTOBOARD", "CABLEADO"]
unidades = [1, 1, 1, 1, 1, 25]
valores = [28489, 37009, 5000, 7000, 10000, 200]

# Calcular el costo total por componente
costos_totales = [u * v for u, v in zip(unidades, valores)]
total_proyecto = sum(costos_totales)

# Agregar fila de total a los datos
componentes.append("TOTAL")
unidades.append("")
valores.append("")
costos_totales.append(total_proyecto)


def costos_componentes_unidad():
    """Función que genera una tabla interactiva con los costos de los componentes."""
    # Configurar fuente de datos para Bokeh
    source = ColumnDataSource(data=dict(
        componentes=componentes,
        unidades=unidades,
        valores=valores,
        costos_totales=costos_totales
    ))

    # Crear un formatter para cambiar el color del texto
    template_formatter = HTMLTemplateFormatter(template="""
        <span style="color: black;"> <%= value %> </span>
    """)

    # Configurar columnas para la tabla con formato
    columns = [
        TableColumn(field="componentes", title="Componente", formatter=template_formatter),
        TableColumn(field="unidades", title="Unidades", formatter=template_formatter),
        TableColumn(field="valores", title="Valor Unitario", formatter=template_formatter),
        TableColumn(field="costos_totales", title="Costo Total", formatter=template_formatter)
    ]

    # Crear tabla de datos
    data_table = DataTable(source=source, columns=columns, width=600, height=300)  # Ajustar ancho

    return data_table


def porcentaje_componentes_unidad():

    """Función que genera un gráfico de dona para representar los costos como porcentajes."""
    # Calcular porcentajes
    porcentajes = [round((costo / total_proyecto) * 100, 2) if total_proyecto > 0 else 0 for costo in costos_totales[:-1]]

    # Preparar datos para gráfico de dona
    data = {'componentes': componentes[:-1], 
            'costos_totales': costos_totales[:-1],
            'porcentajes': porcentajes,
            'angle': [p * 2 * pi / 100 for p in porcentajes],
            'color': Spectral10[:len(componentes)-1]}

    source = ColumnDataSource(data)

    # Crear gráfico de dona
    p = figure(
        height=205, width=450,  # Dimensiones ajustadas
        title="Distribución de Costos del Proyecto", 
        toolbar_location=None, tools="hover", 
        tooltips="""
            <div>
                <span style="font-size: 14px; font-weight: bold;">@componentes</span><br>
                <span style="font-size: 12px;">Costo Total: $@costos_totales</span><br>
                <span style="font-size: 12px;">Porcentaje: @porcentajes%</span>
            </div>
        """,
        x_range=(-2, 2)  # Aumentar rango para evitar solapamientos
    )
    p.wedge(
        x=-1, y=2, radius=0.75, 
        start_angle=cumsum('angle', include_zero=True), 
        end_angle=cumsum('angle'), 
        line_color="white", 
        fill_color='color', 
        legend_field='componentes', 
        source=source
    )

    # Ajustes de visualización
    p.axis.visible = False
    p.grid.visible = False

    # Personalización de la leyenda
    p.legend.label_text_font_size = '10px'
    p.legend.label_text_font_style = 'bold'
    p.legend.location = "top_right"  # Mover la leyenda al lado superior derecho
    p.legend.orientation = "vertical"  # Mantener orientación vertical
    p.legend.glyph_width = 15  # Aumentar tamaño del icono de color
    p.legend.spacing = 5  # Espaciado entre elementos de la leyenda

    # Ajuste del título
    p.title.text_font_size = '14px'
    p.title.align = "center"  # Centrar el título

    return p


# Datos de componentes
componentes_total = ['ESP 32 WIFI BLUETOOTH', 'DAC ADAFR-935', 'JACK OUTPUT SJ1-3515-SMT', "LECTOR SD SIG0104", "MINIPROTO", "CABLES", "MANO DE OBRA"]
unidades_total = [50, 50, 10*5, 50, 1*50, 25*2, 2]
valores_total = [25490, 31458, 2826, 3540, 9996, 200*2,120000]

# Calcular el costo total por componente correctamente
costos_total = [u * v for u, v in zip(unidades_total, valores_total)]
total_proyecto_total = sum(costos_total)

# Agregar fila de total a los datos
componentes_total.append("TOTAL")
unidades_total.append("")
valores_total.append("")
costos_total.append(total_proyecto_total)

def costos_componentes_total():
    """Función que genera una tabla interactiva con los costos de los componentes."""
    # Configurar fuente de datos para Bokeh
    source = ColumnDataSource(data=dict(
        componentes=componentes_total,
        unidades=unidades_total,
        valores=valores_total,
        costos_totales=costos_total
    ))

    # Crear un formatter para cambiar el color del texto
    template_formatter = HTMLTemplateFormatter(template="""
        <span style="color: black;"> <%= value %> </span>
    """)

    # Configurar columnas para la tabla con formato
    columns = [
        TableColumn(field="componentes", title="Componente", formatter=template_formatter),
        TableColumn(field="unidades", title="Unidades", formatter=template_formatter),
        TableColumn(field="valores", title="Valor Unitario", formatter=template_formatter),
        TableColumn(field="costos_totales", title="Costo Total", formatter=template_formatter)
    ]

    # Crear tabla de datos
    data_table = DataTable(source=source, columns=columns, width=600, height=300)  # Ajustar ancho

    return data_table


def porcentaje_componentes_total():
    """Función que genera un gráfico de dona para representar los costos como porcentajes."""
    # Calcular porcentajes
    porcentajes = [round((costo / total_proyecto_total) * 100, 2) if total_proyecto_total > 0 else 0 for costo in costos_total[:-1]]

    # Preparar datos para gráfico de dona
    data = {'componentes': componentes_total[:-1], 
            'costos_totales': costos_total[:-1],
            'porcentajes': porcentajes,
            'angle': [p * 2 * pi / 100 for p in porcentajes],
            'color': Spectral10[:len(componentes_total)-1]}

    source = ColumnDataSource(data)

    # Crear gráfico de dona
    p = figure(
        height=205, width=450,  # Dimensiones ajustadas
        title="Distribución de Costos del Proyecto Total", 
        toolbar_location=None, tools="hover", 
        tooltips="""
            <div>
                <span style="font-size: 14px; font-weight: bold;">@componentes</span><br>
                <span style="font-size: 12px;">Costo Total: $@costos_totales</span><br>
                <span style="font-size: 12px;">Porcentaje: @porcentajes%</span>
            </div>
        """,
        x_range=(-2, 2)  # Aumentar rango para evitar solapamientos
    )
    p.wedge(
        x=-1, y=2, radius=0.75, 
        start_angle=cumsum('angle', include_zero=True), 
        end_angle=cumsum('angle'), 
        line_color="white", 
        fill_color='color', 
        legend_field='componentes', 
        source=source
    )

    # Ajustes de visualización
    p.axis.visible = False
    p.grid.visible = False

    # Personalización de la leyenda
    p.legend.label_text_font_size = '10px'
    p.legend.label_text_font_style = 'bold'
    p.legend.location = "top_right"  # Mover la leyenda al lado superior derecho
    p.legend.orientation = "vertical"  # Mantener orientación vertical
    p.legend.glyph_width = 15  # Aumentar tamaño del icono de color
    p.legend.spacing = 5  # Espaciado entre elementos de la leyenda

    # Ajuste del título
    p.title.text_font_size = '14px'
    p.title.align = "center"  # Centrar el título

    return p

