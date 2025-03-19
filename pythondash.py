import dash
from dash import dcc, html, dash_table
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from flask import Flask

# 🔹 Crear el servidor Flask
server = Flask(__name__)  

# 🔹 Conectar Dash con Flask
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.LUX])

# 🔹 Cargar el dataset
url = "https://raw.githubusercontent.com/EdwinAAH/Inteligencia-de-negocios/refs/heads/main/netflix_titles.csv"
df = pd.read_csv(url)

# 🔹 Limpiar datos eliminando valores nulos
df.dropna(subset=['type', 'release_year', 'country', 'listed_in', 'title'], inplace=True)

# 🔹 Extraer los géneros únicos para el dropdown
generos = df['listed_in'].str.split(', ').explode().unique()

# 🔹 Lista de años únicos para el slider
min_year = df["release_year"].min()
max_year = df["release_year"].max()

# 🔹 **Definir el Layout (Evita el Error `NoLayoutException`)**
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Dashboard de Netflix", className="text-center text-primary mb-4"), width=12)
    ]),

    dbc.Row([
        dbc.Col(html.P("Explora el catálogo de Netflix con visualizaciones interactivas.", 
                       className="text-center text-secondary"), width=12)
    ]),

    dbc.Row([
        dbc.Col([
            html.Label("Selecciona un género:", className="fw-bold"),
            dcc.Dropdown(
                id="dropdown_genero",
                options=[{'label': g, 'value': g} for g in generos],
                value="Drama",
                clearable=False
            )
        ], width=6),

        dbc.Col([
            html.Label("Selecciona el rango de años:", className="fw-bold"),
            dcc.RangeSlider(
                id="slider_anio",
                min=min_year,
                max=max_year,
                value=[min_year, max_year],
                marks={i: str(i) for i in range(min_year, max_year+1, 5)},
                step=1
            )
        ], width=6),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(dcc.Graph(id="grafico_bar"), width=6),
        dbc.Col(dcc.Graph(id="grafico_line"), width=6)
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(dcc.Graph(id="grafico_pastel"), width=6),
        dbc.Col(dcc.Graph(id="grafico_mapa"), width=6)
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(html.H5("Lista de títulos filtrados:", className="text-center text-primary mt-4"), width=12),
        dbc.Col(dash_table.DataTable(
            id="tabla_titulos",
            columns=[{"name": col, "id": col} for col in ["title", "type", "release_year", "country"]],
            page_size=20,
            style_table={'overflowX': 'auto', 'height': '400px', 'margin-bottom': '20px'},  
            style_header={'backgroundColor': 'lightblue', 'fontWeight': 'bold'},
            style_cell={'textAlign': 'center'}
        ), width=12)
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id="grafico_dispersion"), width=12)
    ], className="mb-4"),

], fluid=True, className="p-4 bg-light")

# 🔹 **Definir Callbacks**
@app.callback(
    [Output("grafico_bar", "figure"),
     Output("grafico_line", "figure"),
     Output("grafico_pastel", "figure"),
     Output("grafico_mapa", "figure"),
     Output("grafico_dispersion", "figure"),
     Output("tabla_titulos", "data")],  
    [Input("dropdown_genero", "value"),
     Input("slider_anio", "value")]
)
def actualizar_graficos(genero_seleccionado, anios):
    df_filtrado = df[df["listed_in"].str.contains(fr"\b{genero_seleccionado}\b", case=False, na=False, regex=True)]
    df_filtrado = df_filtrado[(df_filtrado["release_year"] >= anios[0]) & (df_filtrado["release_year"] <= anios[1])]

    fig_bar = px.bar(df_filtrado.groupby("release_year").size().reset_index(name="Cantidad"),
                     x='release_year', y='Cantidad', 
                     title=f"Títulos de {genero_seleccionado} en Netflix por Año")

    fig_line = px.line(df_filtrado.groupby("release_year").count().reset_index(),
                       x="release_year", y="show_id",
                       title=f"Evolución del catálogo de Netflix ({anios[0]} - {anios[1]})")

    tipo_contenido = df_filtrado["type"].value_counts().reset_index()
    tipo_contenido.columns = ["Tipo de Contenido", "Cantidad"]
    fig_pastel = px.pie(tipo_contenido, names="Tipo de Contenido", values="Cantidad",
                         title="Proporción de Películas y Series")

    paises = df_filtrado["country"].value_counts().reset_index()
    paises.columns = ["País", "Cantidad"]
    fig_mapa = px.choropleth(paises, locations="País", locationmode="country names",
                             color="Cantidad", title="Cantidad de Títulos por País",
                             color_continuous_scale="reds")

    fig_dispersion = px.strip(df_filtrado, x="release_year", y="type",
                              title="Relación entre Año de Lanzamiento y Tipo de Contenido",
                              labels={'release_year': 'Año de Lanzamiento', 'type': 'Tipo de Contenido'},
                              color="type",
                              stripmode="group")

    return fig_bar, fig_line, fig_pastel, fig_mapa, fig_dispersion, df_filtrado[["title", "type", "release_year", "country"]].to_dict('records')

# 🔹 **Ejecutar el Servidor en Render**
if __name__ == "__main__":
    server.run(host="0.0.0.0", port=10000)
