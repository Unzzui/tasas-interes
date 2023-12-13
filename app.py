import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
import re  # Para procesar el formato monetario
from datetime import datetime as dt
from flask import Flask, send_file
import io
from dash.exceptions import PreventUpdate

# Cargar los datos desde el archivo Excel

df = pd.read_excel("data/tasas_interes.xlsx", sheet_name="bd_2023_prueba")

# Obtener una lista de colores únicos para cada banco
colores_banco = px.colors.qualitative.Set1[:len(df['Nombre entidad acreedora'].unique())]

# Inicializar la aplicación Dash sin tema de Bootstrap
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])  # Usando Bootstrap para mejorar el diseño

# Obtener la lista de nombres de empresas, sectores y bancos únicos
empresa_options = [{'label': empresa, 'value': empresa} for empresa in df['Empresa'].unique()]
sector_options = [{'label': sector, 'value': sector} for sector in df['Sector'].unique()]
# Filtrar el DataFrame para incluir solo bancos chilenos
df_bancos_chilenos = df[df['Pais Empresa Acreedora'] == 'Chile']

# Obtener la lista de nombres de bancos chilenos únicos
banco_options = [{'label': banco, 'value': banco} for banco in df_bancos_chilenos['Nombre entidad acreedora'].unique()]

# Introducción explicativa
external_stylesheets = ['styles.css']

clasification_text = """
### Clasificación

Estas categorías se utilizan para evaluar la solidez financiera de diferentes instrumentos financieros, como bonos o préstamos. Aquí está una explicación más simple:

- **Categoría AAA:** La mejor categoría, significa que es muy probable que el emisor pague el dinero prestado en los términos acordados sin importar los cambios económicos.
- **Categoría AA:** Muy buena, también es probable que el emisor pague como se acordó, pero puede ser un poco menos resistente a cambios económicos.
- **Categoría A:** Buena, probablemente se pagará según lo acordado, pero puede ser más vulnerable a cambios económicos.
- **Categoría BBB:** Suficiente, es probable que se pague, pero existe un riesgo mayor de que se vea afectado por cambios económicos.
- **Categoría BB:** Aceptable, es posible que se pague, pero la capacidad de pago es variable y puede verse afectada por cambios económicos, incluso con retrasos en los pagos.
- **Categoría B:** Mínima, hay capacidad limitada para pagar y es muy variable, con riesgo de pérdida de dinero.
- **Categoría C:** Alto riesgo, la capacidad de pago es insuficiente, lo que aumenta el riesgo de pérdida de dinero.
- **Categoría D:** Riesgo extremo, el emisor no puede pagar como se acordó, hay incumplimientos en los pagos o una posible quiebra en curso.
- **Categoría E:** Sin información suficiente, no hay datos adecuados para evaluar la solidez financiera.

*Nota adicional: Puede haber símbolos "+" o "-" en las categorías AA a B para indicar fortalezas o debilidades dentro de esas categorías.*
"""



navbar = dbc.Navbar(
    children=[
        html.Script(src="https://code.jquery.com/jquery-3.5.1.min.js"),
        html.Script(src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"),
        dbc.NavbarToggler(id="navbar-toggler"),
        dbc.Collapse(
            dbc.Nav(
                [
                    dbc.NavItem(dbc.NavLink(html.A("Inicio", href="/#", className="nav-link-custom"))),
                    dbc.NavItem(dbc.NavLink(html.A("Gráficos", href="/#bar-chart", className="nav-link-custom"))),
                    dbc.NavItem(dbc.NavLink(html.A("Descargar Datos", href="/#descargar-seccion", className="nav-link-custom"))),
                    dbc.NavItem(dbc.NavLink(html.A("DUOC", href="https://www.duoc.cl/", target="_blank", className="nav-link-custom"))),
                    dbc.NavItem(dbc.NavLink(html.A("Contacto", href="mailto:diegobravobe@gmail.com?subject=Consulta%20Web%20Tasas%20de%20Interés", className="nav-link-custom"))),

                ],
                navbar=True,
                className="ml-auto mx-auto",
            ),
            id="navbar-collapse",
            navbar=True,
        ),
    ],
    color="dark",
    sticky="top",
    className="w-100 h-1"
    
)

# Footer con tu información de contacto
footer = dbc.Row(
    dbc.Col(
        html.Div(
            [
                html.P("© 2023 Diego Bravo - Todos los derechos reservados"),
                  html.P(
            [
                "Información de contacto: ",
                html.A("diegobravobe@gmail.com", href="mailto:diegobravobe@gmail.com?subject=Consulta%20Web%20Tasas%20de%20Interés",
                       style={'color': 'inherit', 'text-decoration': 'none'}),
                " | Teléfono: +56930532461"
            ]
        ),
                # Puedes incluir más información de contacto aquí
            ],
            className="py-3 bg-dark text-white text-center"
        ),
        width=12
    )
)


colores_graficos = px.colors.qualitative.Vivid  # Cambia esto por una paleta que prefieras

# Personaliza los estilos de los gráficos
def customizar_grafico(fig):
    fig.update_layout(
        font=dict(family="Helvetica", size=12, color="#7f7f7f"),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False)
    )
    return fig



def generate_kpis(selected_empresas, selected_sectores, selected_bancos):
    # Cálculos de las tasas promedio máximas y mínimas
   
    filtered_df = df.copy()

    # Filtrar el DataFrame según las selecciones de empresas y sectores
    if selected_empresas:
        filtered_df = filtered_df[filtered_df['Empresa'].isin(selected_empresas)]
    if selected_sectores:
        filtered_df = filtered_df[filtered_df['Sector'].isin(selected_sectores)]

    # Filtrar el DataFrame para incluir solo bancos chilenos
    filtered_df = filtered_df[filtered_df['Pais Empresa Acreedora'] == 'Chile']

    # Si se han seleccionado bancos específicos, aplicar ese filtro
    if selected_bancos:
        filtered_df = filtered_df[filtered_df['Nombre entidad acreedora'].isin(selected_bancos)]
        
    # Verificar si solo se ha seleccionado un banco (si selected_bancos es una lista)
    if selected_bancos is not None and len(selected_bancos) == 1:
        # Calcular la tasa de interés promedio del banco seleccionado
        single_bank_average_interest_rate = filtered_df['Tasa nominal'].mean() * 100
        # Mostrar un KPI especial para un solo banco
        single_bank_kpi = dbc.Row(
            dbc.Col(
                dbc.Card([
                    html.H3(f"{single_bank_average_interest_rate:.2f}%", className="card-title text-muted"),
                    html.P(f"Tasa de Interés Promedio del {selected_bancos[0]}", className="card-title"),
                ], body=True, color="light", inverse=False),
                width={"size": 4, "offset": 4},  # Ancho de 4 y centrado
            )
        )
        return single_bank_kpi
    
    max_average_interest_rate = filtered_df.groupby('Nombre entidad acreedora')['Tasa nominal'].mean().idxmax()
    max_average_interest_rate_value = filtered_df.groupby('Nombre entidad acreedora')['Tasa nominal'].mean().max() * 100
    
    min_average_interest_rate = filtered_df.groupby('Nombre entidad acreedora')['Tasa nominal'].mean().idxmin()
    min_average_interest_rate_value = filtered_df.groupby('Nombre entidad acreedora')['Tasa nominal'].mean().min() * 100
    
    average_interest_rate = filtered_df['Tasa nominal'].mean() * 100
    
    # Crear las tarjetas para los KPIs
    kpi_cards = dbc.Row([
        dbc.Col(dbc.Card([
            html.H3(f"{max_average_interest_rate_value:.2f}%", className="card-title text-muted"),
            html.P(f"Tasa de Interés más Alta Promedio -  {max_average_interest_rate}",
                   className="card-text"),
        ], body=True, color="light", inverse=False)),
        dbc.Col(dbc.Card([
            html.H3(f"{min_average_interest_rate_value:.2f}%", className="card-title text-muted"),
            html.P(f"Tasa de Interés más Baja Promedio -  {min_average_interest_rate}",
                   className="card-text"),
        ], body=True, color="light", inverse=False)),
        dbc.Col(dbc.Card([
            html.H3(f"{average_interest_rate:.2f}%", className="card-title text-muted"),
            html.P("Promedio Tasa de Interés", className="card-text"),
        ], body=True, color="light", inverse=False)),
    ])
    
    # Crear la nota explicativa del promedio de todas las monedas
    note_average_currency = dbc.Row([
        dbc.Col(html.P("Nota: El promedio de tasa de interés incluye todas las monedas ofrecidas por el banco.",
                       className="card-text text-muted"))
    ])
    
    # Combinar las tarjetas de KPIs y la nota en un solo contenedor
    kpis_and_note = dbc.Container([kpi_cards, note_average_currency])
    
    return kpis_and_note




@app.callback(
    Output('kpi-cards-container', 'children'),
    [Input('empresa-dropdown', 'value'),
     Input('sector-dropdown', 'value'),
     Input('banco-dropdown', 'value')]
)
def update_kpi_cards(selected_empresas, selected_sectores, selected_bancos):
    # Actualizar los KPIs en función de las selecciones de los dropdowns
    kpi_cards = generate_kpis(selected_empresas, selected_sectores, selected_bancos)
    return kpi_cards


display_bar_logo = {
    'displayModeBar':True,
    'displaylogo':False,
}

@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open



navbar_wrapper = html.Div(
    children=[
        navbar
    ],
    className="navbar-wrapper mx-auto text-center",

)
# Diseño de la aplicación
app.layout = dbc.Container([
    navbar_wrapper,
       dbc.Row(
            dbc.Col(html.H1("Análisis Tasas de Interés Bancos Chilenos", className="text-center"), width="auto"),
            justify="center",
            style={"margin-top": "4rem", "margin-bottom":"2rem"}
        ),    
    # Incluir KPIs con un estilo mejorado
    html.Div(id='kpi-cards-container'),
    # Mejor diseño para los Dropdowns
    dbc.Container(
    dbc.Row([
        dbc.Col(dcc.Dropdown(id='empresa-dropdown', options=empresa_options, multi=True, placeholder="Seleccionar Empresa(s)", className="mt-4 mb-2"), width=4),
        dbc.Col(dcc.Dropdown(id='sector-dropdown', options=sector_options, multi=True, placeholder="Seleccionar Sector(es)", className="mt-4 mb-2"), width=4),
        dbc.Col(dcc.Dropdown(id='banco-dropdown', options=banco_options, multi=True, placeholder="Seleccionar Banco(s) (Solo Chilenos)", className="mt-4 mb-2"), width=4),
    ], justify="around"),
),
    dbc.Row(dbc.Col(dcc.Graph(id='bar-chart',config=display_bar_logo), width=12)),

    # Gráficos con mejor diseño
    dbc.Row([
        dbc.Col(dcc.Graph(id='scatter-plot',config=display_bar_logo), width=6),
        dbc.Col(dcc.Graph(id='boxplot',config=display_bar_logo), width=6),
    ], justify="around"),


    dbc.Row(
        dbc.Col(dcc.Markdown(clasification_text, className="p-4"), className="mt-4 bg-light border"),
        justify="center"
    ),
         dbc.Row(
            dbc.Col(
                html.H3(children="Descargar Datos", id="descargar-seccion"),
                width="auto"
            ),
            justify="center",
            style={"margin-top": "4rem", "margin-bottom": "0.5rem"}
        ),
        dbc.Row(
            dbc.Col(
                html.P(
                    "Descarga la base de datos completa en CSV para acceder a todos los datos disponibles. Además, tienes la opción de descargar los datos en formato Excel, en el caso de que no se tenga disponible la forma de abrir el archivo en formato CSV."
                ),
                width="auto"
            ),
            justify="center",
            style={"margin-bottom": "0.2rem"}
        ),
        dbc.Row(
            dbc.Col(
                html.Div(
                    className="text-center my-4",
                    children=[
                        html.A(
                            html.Button("Descargar CSV", className="btn btn-info", style={"margin-right": "10px"}),
                            href="/download_csv"
                        ),
                        html.A(
                            html.Button("Descargar Excel", className="btn btn-info ml-10 mt-10"),
                            href="/download_excel"
                        ),
                    ]
                ),
            ),
            justify="center"
        ),
    footer,
], fluid=True, className="py-3")

base_graph_style = {
    'font_family': 'Open Sans, sans-serif',
    'title_font_family': 'Open Sans, sans-serif',
    'legend_title_font_family': 'Open Sans, sans-serif',
    'font_size': 14,
    'title_font_size': 18,
    'legend_title_font_size': 16,
    'colorway': ['#003f5c', '#58508d', '#bc5090', '#ff6361', '#ffa600'],  # Ejemplo de una paleta de colores
}



def update_scatter_plot(selected_empresas, selected_sectores, selected_bancos):
    # Crear una copia del DataFrame original
    filtered_df = df.copy()

    # Filtrar el DataFrame según las selecciones de empresas y sectores
    if selected_empresas:
        filtered_df = filtered_df[filtered_df['Empresa'].isin(selected_empresas)]
    if selected_sectores:
        filtered_df = filtered_df[filtered_df['Sector'].isin(selected_sectores)]

    # Filtrar el DataFrame para incluir solo bancos chilenos
    filtered_df = filtered_df[filtered_df['Pais Empresa Acreedora'] == 'Chile']

    # Si se han seleccionado bancos específicos, aplicar ese filtro
    if selected_bancos:
        filtered_df = filtered_df[filtered_df['Nombre entidad acreedora'].isin(selected_bancos)]

    # Procesar la columna "Total" para obtener el monto del crédito como un valor numérico
    filtered_df['Monto del Crédito'] = filtered_df['Total']
    # Crear un gráfico de dispersión
    scatter_fig = px.scatter(
        filtered_df,
        x='Monto del Crédito',  # Monto en el eje x
        y='Tasa nominal',  # Tasa de interés en el eje y
        color='Nombre entidad acreedora',
        hover_data=['Empresa'],  # Aquí se especifica qué datos adicionales mostrar en el hover
        labels={'Monto del Crédito': 'Monto del Crédito', 'Tasa nominal': 'Tasa de Interés (%)', 'Empresa':'Empresa'},
        color_discrete_sequence=colores_banco,
    )

    # Personalizar el gráfico de dispersión
    scatter_fig.update_layout(
        title='Relación entre Monto del Crédito y Tasa de Interés',
        xaxis_title='Monto del Crédito',
        yaxis_title='Tasa de Interés (%)',
        font=dict(family='Arial', size=12),
        legend_title_text='Banco',
        legend_title_font=dict(family='Arial', size=12),
        margin=dict(l=60, r=10, t=50, b=60),
        plot_bgcolor='#F7F7F7',
        paper_bgcolor='#FFFFFF',
    )

    scatter_fig.update_xaxes(title_text="Monto Total (M$)", showline=True, linecolor='black', tickfont=dict(family='Arial', size=12), tickformat="$,.0f")

    scatter_fig.update_yaxes(title_text="Tasa Nominal %", showline=True, linecolor='black', tickfont=dict(family='Arial', size=12), tickformat=",.2%",)



    return scatter_fig


# Función para actualizar el gráfico de caja
@app.callback(
    Output('boxplot', 'figure'),
    [Input('empresa-dropdown', 'value'),
     Input('sector-dropdown', 'value'),
     Input('banco-dropdown', 'value')]
)
def update_boxplot(selected_empresas, selected_sectores, selected_bancos):
    # Filtrar el DataFrame según las selecciones
    filtered_df = df.copy()
    filtered_df = filtered_df[filtered_df['Pais Empresa Acreedora'] == 'Chile']

    if selected_empresas:
        filtered_df = filtered_df[filtered_df['Empresa'].isin(selected_empresas)]
    if selected_sectores:
        filtered_df = filtered_df[filtered_df['Sector'].isin(selected_sectores)]
    if selected_bancos:
        filtered_df = filtered_df[filtered_df['Nombre entidad acreedora'].isin(selected_bancos)]
     # Verificar si el DataFrame filtrado está vacío
    if filtered_df.empty:
        return px.box()

    # Lista ordenada de ratings
    ordered_ratings = ['AA+', 'AA', 'AA-', 'A', 'A-', 'BBB+', 'BBB', 'BBB-', 'BB+', 'BB', 'BB-', 'B+', 'B', 'B-', 'C', 'D', 'E']

    # Ajustar las categorías de 'Rating' basadas en los valores presentes en el DataFrame filtrado
    existing_ratings = filtered_df['Rating'].dropna().unique()
    ordered_ratings = [rating for rating in ordered_ratings if rating in existing_ratings]

    # Si no hay ratings disponibles, devolver un gráfico vacío
    if not ordered_ratings:
        return px.box()

    # Aplicar las categorías ajustadas al DataFrame
    filtered_df['Rating'] = pd.Categorical(filtered_df['Rating'], categories=ordered_ratings, ordered=True)
    filtered_df = filtered_df.sort_values(by='Rating')

    # Crear el gráfico de caja
    boxplot_fig = px.box(
        filtered_df,
        x='Rating',
        y='Tasa nominal',
        color='Rating',
        labels={'Rating': 'Rating', 'Tasa nominal': 'Tasa de Interés (%)'}
    )

    # Personalizar el gráfico de caja
    boxplot_fig.update_layout(
        title='Distribución de Tasas de Interés por Rating',
        xaxis_title='Rating',
        yaxis_title='Tasa de Interés (%)',
        font=dict(family='Arial', size=12),
        margin=dict(l=60, r=10, t=50, b=60),
        plot_bgcolor='#F7F7F7',
        paper_bgcolor='#FFFFFF'
        
    )
    


    boxplot_fig.update_yaxes(title_text="Tasa Nominal %", showline=True, linecolor='black', tickfont=dict(family='Arial', size=12), tickformat=",.2%",)

    return boxplot_fig

# Añadir el gráfico de caja al layout de la aplicación
# Definir una función para actualizar el gráfico y los mensajes informativos
@app.callback(
    [Output('bar-chart', 'figure'),
     Output('scatter-plot', 'figure')],
    [Input('empresa-dropdown', 'value'),
     Input('sector-dropdown', 'value'),
     Input('banco-dropdown', 'value')]
)
def update_bar_and_scatter(selected_empresas, selected_sectores, selected_bancos):
    # Crear una copia del DataFrame original
    filtered_df = df.copy()

    # Filtrar el DataFrame según las selecciones de empresas y sectores
    if selected_empresas:
        filtered_df = filtered_df[filtered_df['Empresa'].isin(selected_empresas)]
    if selected_sectores:
        filtered_df = filtered_df[filtered_df['Sector'].isin(selected_sectores)]

    # Filtrar el DataFrame para incluir solo bancos chilenos
    filtered_df = filtered_df[filtered_df['Pais Empresa Acreedora'] == 'Chile']

    # Si se han seleccionado bancos específicos, aplicar ese filtro
    if selected_bancos:
        filtered_df = filtered_df[filtered_df['Nombre entidad acreedora'].isin(selected_bancos)]

    
    # Agrupar por moneda y calcular la tasa de interés promedio
    grouped_df = filtered_df.groupby(['Tipo Moneda', 'Nombre entidad acreedora'])['Tasa nominal'].mean().reset_index()
    grouped_df = grouped_df.sort_values(by=['Tipo Moneda', 'Tasa nominal'], ascending=[True, True])
    scatter_fig = update_scatter_plot(selected_empresas, selected_sectores, selected_bancos)

    
    # Crear un gráfico de barras grupales con colores por banco
    fig = px.bar(
        grouped_df,
        x='Tipo Moneda',
        y='Tasa nominal',
        color='Nombre entidad acreedora',
        barmode='group',
        labels={'Tipo Moneda': 'Moneda', 'Tasa nominal': 'Tasa de Interés (%)'},
        color_discrete_sequence=colores_banco,
    )

    fig.update_yaxes(categoryorder='total ascending')

    # Personalizar el gráfico para hacerlo más profesional y atractivo
    fig.update_xaxes(title_text="Moneda", showline=True, linecolor='black', tickfont=dict(family='Arial', size=12))
    fig.update_yaxes(title_text="Tasa de Interés (%)", showline=True, linecolor='black', tickfont=dict(family='Arial', size=12), tickformat=",.2%",)
    fig.update_layout(
        title='Distribución de Tasas de Interés Promedio por Banco',
        xaxis_tickangle=-45,
        legend_title_text='Banco',
        legend_title_font=dict(family="Arial", size=12),
        font=dict(family="Arial", size=12),
        margin=dict(l=60, r=10, t=50, b=60),
        plot_bgcolor='#F7F7F7',  # Fondo del gráfico
        paper_bgcolor='#FFFFFF',  # Fondo del papel
        legend=dict(title=dict(font=dict(family="Arial", size=12))),
        legend_traceorder='normal',
    )


    return fig, scatter_fig



@app.server.route("/download_csv")
def download_csv():
    # Guardar el DataFrame en un archivo CSV en memoria
    csv_data = df_bancos_chilenos.to_csv(index=False)

    # Crear un objeto de archivo en memoria utilizando io.BytesIO
    mem_file = io.BytesIO()
    mem_file.write(csv_data.encode())
    mem_file.seek(0)
    now = dt.now().strftime("%d-%m-%y")



    # Devolver el archivo CSV generado como respuesta
    return send_file(mem_file, mimetype="text/csv", as_attachment=True,download_name=f"data_{now}.csv")


@app.server.route("/download_excel")
def download_excel():
    excel_path = "../Idea/tasas_interes.xlsx"  # Reemplaza con la ruta real de tu archivo CSV
    return send_file(excel_path, as_attachment=True)
# Ejecutar la aplicación Dash
if __name__ == '__main__':
    app.run_server(debug=True)
