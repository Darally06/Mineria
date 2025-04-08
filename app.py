import dash
from dash import dcc, html, dash_table
import plotly.express as px
import plotly.graph_objects as go

import pandas as pd
import geopandas as gpd
import folium

# 1️⃣ CARGA DE DATOS
# Base de datos y Mapa de Colombia por municipios
df = pd.read_csv(r"Productores_Productores_de_B100_y_Etanol_-_Alcohol_Carburante__AUTOMATIZADO__20250314.csv")
gdf_m = gpd.read_file("mi_dash\Municipios_Interes.geojson")

# 2️⃣ DESPACHOS
# Tabla del total de despachos
t_desp = pd.DataFrame({
    "Producto": df["PRODUCTO"].value_counts().index,
    "Cantidad": df["PRODUCTO"].value_counts().values,
})
t_desp

# Despachos por producto
b100 = df[df["PRODUCTO"] == "B 100"]
etanol = df[df["PRODUCTO"] == "ETANOL - ALCOHOL CARBURANTE"]

year = df.groupby("ANIO_DESPACHO").size().reset_index(name="Total Despachos")
b100_d = b100.groupby("ANIO_DESPACHO").size().reset_index(name="Despachos B100")
etanol_d = etanol.groupby("ANIO_DESPACHO").size().reset_index(name="Despachos Etanol")

table_desp = year.merge(b100_d, on="ANIO_DESPACHO", how="left").merge(etanol_d, on="ANIO_DESPACHO", how="left")
table_desp = table_desp.rename(columns={"ANIO_DESPACHO": "Año"})


# Gráfico despachos por año y mes de cada producto
def despachos(data, producto, color = "#A0C878"):
    """
    Generar un gráfico de linea sobre la evolución mensual de despachos
    """
    nombre_columna = f"Despachos {producto}"
    data_m = data.groupby(["ANIO_DESPACHO", "MES_DESPACHO"]).size().reset_index(name= nombre_columna)
    fig = px.line(
        data_m,
        x="MES_DESPACHO", 
        y=nombre_columna,
        color="ANIO_DESPACHO",
        title=f"Evolución Mensual de Despachos de {producto} por Año",
        labels={"MES_DESPACHO": "Mes", nombre_columna: "Despachos"},
        markers=True,
        hover_data={"MES_DESPACHO": False, "ANIO_DESPACHO": False, nombre_columna: True}
    )   
    fig.update_layout(
        title_font=dict(size=16, color=color),
        xaxis=dict(tickmode="linear", dtick=1),
        legend_title="Año",
        hovermode="x unified"
    )

    return fig

fig_b100 = despachos(b100, "B100")
fig_etanol = despachos(etanol, "Etanol")



# VOLUMEN|
df.loc[df["VOLUMEN_DESPACHADO"] > 3.1e6, "VOLUMEN_DESPACHADO"] = pd.NA
vol_e = df[df["PRODUCTO"] == "ETANOL - ALCOHOL CARBURANTE"]["VOLUMEN_DESPACHADO"]
vol_b = df[df["PRODUCTO"] == "B 100"]["VOLUMEN_DESPACHADO"]

def volumen(data, producto, color):
    """
    Generar un boxplot para la distribución del volumen
    """
    fig = go.Figure()
    fig.add_trace(go.Box(
        x = data,
        name = producto,
        marker_color = color,
        boxmean = "sd",
    ))
    fig.update_layout(
        title = f"Distribución de los volúmenes de {producto} despachados",
        title_font=dict(size=18, color="#A0C878"),  
        xaxis_title = producto,
        yaxis_title ="Volumen despachado",
        yaxis=dict(gridcolor="lightgray") 
    )
    return fig
fig_e_v = volumen(vol_b, "B100", "#57B4BA")
fig_b100_v = volumen(vol_e, "Etanol", "#FE4F2D")


# Volumen por año
tabla_volumen = df.groupby(["ANIO_DESPACHO", "PRODUCTO"])["VOLUMEN_DESPACHADO"].sum().unstack()
tabla_volumen = tabla_volumen.apply(pd.to_numeric)
tabla_volumen_reset = tabla_volumen.reset_index()
fig_vol_year = px.bar(
    tabla_volumen_reset, 
    x="ANIO_DESPACHO", 
    y=tabla_volumen.columns,  
    barmode="group",
    title="Volúmen de productos despachados por año",
    labels={"value": "Volúmen despachado", "variable": "Producto"},
    hover_data={"ANIO_DESPACHO": False}, 
    color_discrete_map={ "B 100": '#57B4BA',  "ETANOL": "#FE4F2D"}
)
fig_vol_year.update_layout(
    title = dict(
        text = "Volúmen de producto despachado por año", font = dict(size = 20, color = "#A0C878"),
        x = 0.5),
    xaxis_title="Año de despacho",
    yaxis_title="Volúmen despachado",
    legend_title="Producto",
    bargap=0.2,  
    hovermode="x"
)



# TIPO DE COMPRADOR
t_comp = pd.DataFrame({
    "Producto": df["TIPO_COMPRADOR"].value_counts().index,
    "Cantidad": df["TIPO_COMPRADOR"].value_counts().values,
    "Porcentaje": (df["TIPO_COMPRADOR"].value_counts().values / df["TIPO_COMPRADOR"].count()) * 100
})
t_comp["Porcentaje"] = t_comp["Porcentaje"].map(lambda x: f"{x:.2f}%")



# LUGAR DE DESPACHO
# Proveedores
tabla_proveedores = df.groupby(["DEPARTAMENTO_PROVEEDOR", "MUNICIPIO_PROVEEDOR"]).agg(
    Cantidad_Despachos=("VOLUMEN_DESPACHADO", "count"),
    Volumen_Etanol=("VOLUMEN_DESPACHADO", lambda x: x[df["PRODUCTO"] == "ETANOL - ALCOHOL CARBURANTE"].sum()),
    Volumen_B100=("VOLUMEN_DESPACHADO", lambda x: x[df["PRODUCTO"] == "B 100"].sum())
).reset_index()
tabla_proveedores.rename(columns={
    "DEPARTAMENTO_PROVEEDOR": "Departamento",
    "MUNICIPIO_PROVEEDOR": "Municipio",
    "Cantidad_Despachos": "Cantidad de Despachos",
    "Volumen_Etanol": "Volumen de Etanol",
    "Volumen_B100": "Volumen de B100"
}, inplace=True)
tabla_proveedores["Volumen de B100"] = tabla_proveedores["Volumen de B100"].apply(lambda x: f"{x:,.2f}")
tabla_proveedores["Volumen de Etanol"] = tabla_proveedores["Volumen de Etanol"].apply(lambda x: f"{x:,.2f}")

# Destino
tabla_destino = df.groupby(["DEPARTAMENTO", "MUNICIPIO"]).agg(
    Cantidad_Despachos=("VOLUMEN_DESPACHADO", "count"),
    Volumen_Etanol=("VOLUMEN_DESPACHADO", lambda x: x[df["PRODUCTO"] == "ETANOL - ALCOHOL CARBURANTE"].sum()),
    Volumen_B100=("VOLUMEN_DESPACHADO", lambda x: x[df["PRODUCTO"] == "B 100"].sum())
).reset_index()
tabla_destino.rename(columns={
    "DEPARTAMENTO": "Departamento",
    "MUNICIPIO": "Municipio",
    "Cantidad_Despachos": "Cantidad de Despachos",
    "Volumen_Etanol": "Volumen de Etanol",
    "Volumen_B100": "Volumen de B100"
}, inplace=True)
tabla_destino["Volumen de B100"] = tabla_destino["Volumen de B100"].apply(lambda x: f"{x:,.2f}")
tabla_destino["Volumen de Etanol"] = tabla_destino["Volumen de Etanol"].apply(lambda x: f"{x:,.2f}")

# Asegurar strings de 5 dígitos para los códigos de municipios
df["CODIGO_MUNICIPIO_DANE_PROVEEDOR"] = df["CODIGO_MUNICIPIO_DANE_PROVEEDOR"].astype(str).str.zfill(5)
df["CODIGO_MUNICIPIO_DANE_DESTINO"] = df["CODIGO_MUNICIPIO_DANE_DESTINO"].astype(str).str.zfill(5)

# CREACIÓN DE CÓDIGOS DE MUNICIPIOS EN gdf_m
gdf_m["CODIGO_MUNICIPIO_DANE"] = gdf_m["dpto_ccdgo"].astype(str).str.zfill(2) + gdf_m["mpio_ccdgo"].astype(str).str.zfill(3)
geo_dict = dict(zip(gdf_m["CODIGO_MUNICIPIO_DANE"], gdf_m["geometry"]))
df["geometry_proveedor"] = df["CODIGO_MUNICIPIO_DANE_PROVEEDOR"].map(geo_dict)
df["geometry_destino"] = df["CODIGO_MUNICIPIO_DANE_DESTINO"].map(geo_dict)

gdf_proveedores = gpd.GeoDataFrame(df, geometry="geometry_proveedor").drop_duplicates(subset=["CODIGO_MUNICIPIO_DANE_PROVEEDOR"])
gdf_destinos = gpd.GeoDataFrame(df, geometry="geometry_destino").drop_duplicates(subset=["CODIGO_MUNICIPIO_DANE_DESTINO"])



# Mapa municipios y proveedores
m = folium.Map(location=[4.5709, -74.2973], zoom_start=6)
for _, row in gdf_proveedores.iterrows():
    if row["geometry_proveedor"]:
        nombre = row.get("MUNICIPIO_PROVEEDOR")  
        folium.GeoJson(
            row["geometry_proveedor"],
            style_function=lambda x: {"color": "#57B4BA", "fillColor": "#57B4BA", "fillOpacity": 0.5},
            tooltip=f"Proveedor: {nombre}"
        ).add_to(m)
for _, row in gdf_destinos.iterrows():
    if row["geometry_destino"]:
        nombre = row.get("MUNICIPIO")  
        folium.GeoJson(
            row["geometry_destino"],
            style_function=lambda x: {"color": "#FE4F2D", "fillColor": "#FE4F2D", "fillOpacity": 0.5},
            tooltip=f"Destino: {nombre}"
        ).add_to(m)
legend_html = """
<div style="
    position: fixed; 
    bottom: 50px; left: 50px; width: 200px; height: 90px; 
    background-color: white; z-index:9999; 
    padding: 10px; font-size:14px; border-radius:5px;
    box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
">
    <b>Leyenda</b> <br>
    <i style="background:blue; width:10px; height:10px; display:inline-block;"></i> Municipios Proveedores<br>
    <i style="background:red; width:10px; height:10px; display:inline-block;"></i> Municipios Destino
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))
m.save("mapa_municipios.html")



# RELACIÓN PROVEEDOR-DESTINO
df_despachos = df.groupby(["MUNICIPIO_PROVEEDOR", "MUNICIPIO"]).size().reset_index(name="CANTIDAD_DESPACHOS")

# Proveedor
df_rel_p = df_despachos.groupby("MUNICIPIO_PROVEEDOR")["MUNICIPIO"].nunique().reset_index()
df_rel_p.columns = ["MUNICIPIO_PROVEEDOR", "CANTIDAD_RELACIONES"]

# Destinos
df_rel_d = df_despachos.groupby("MUNICIPIO")["MUNICIPIO_PROVEEDOR"].nunique().reset_index()
df_rel_d .columns = ["MUNICIPIO", "CANTIDAD_RELACIONES"]

fig_rel_p = px.bar(df_rel_p, 
    x="MUNICIPIO_PROVEEDOR", 
    y="CANTIDAD_RELACIONES", 
    title="Número de relaciones por Municipio Proveedor",
    labels={"MUNICIPIO_PROVEEDOR": "Municipio Proveedor", "CANTIDAD_RELACIONES": "Número de Destinos"},
    hover_data=["CANTIDAD_RELACIONES"]
)
fig_rel_p.update_layout(clickmode="event+select")
fig_rel_p.update_traces(marker_color="#57B4BA")

fig_rel_d = px.bar(df_rel_d , 
    x="MUNICIPIO", 
    y="CANTIDAD_RELACIONES", 
    title="Número de relaciones por Municipio Destino",
    labels={"MUNICIPIO": "Municipio Destino", "CANTIDAD_RELACIONES": "Número de Proveedores"},
    hover_data=["CANTIDAD_RELACIONES"])
fig_rel_d.update_layout(clickmode="event+select")
fig_rel_d.update_traces(marker_color="#57B4BA")


# MAPA RELACIONES
grafo = folium.Map(location=[4.5709, -74.2973], zoom_start=6)

gdf_proveedores["lat"] = gdf_proveedores.geometry.centroid.y
gdf_proveedores["lon"] = gdf_proveedores.geometry.centroid.x
gdf_destinos["lat"] = gdf_destinos.geometry.centroid.y
gdf_destinos["lon"] = gdf_destinos.geometry.centroid.x

coord_prov = gdf_proveedores.set_index("MUNICIPIO_PROVEEDOR")[["lat", "lon"]].to_dict("index")
coord_dest = gdf_destinos.set_index("MUNICIPIO")[["lat", "lon"]].to_dict("index")

for municipio, coord in coord_prov.items():
    folium.CircleMarker(
        location=[coord["lat"], coord["lon"]],
        radius=5,
        color="blue",
        fill=True,
        fill_color="blue",
        fill_opacity=0.6,
        tooltip=f"Proveedor: {municipio}"
    ).add_to(m)

for municipio, coord in coord_dest.items():
    folium.CircleMarker(
        location=[coord["lat"], coord["lon"]],
        radius=5,
        color="red",
        fill=True,
        fill_color="red",
        fill_opacity=0.6,
        tooltip=f"Destino: {municipio}"
    ).add_to(m)
    
rango_colores = {
    (0, 100): "blue",
    (100, 1000): "green",
    (1000, 10000): "orange",
    (10000, 30000): "red"
}

import math

for _, row in df_despachos.iterrows():
    origen = row["MUNICIPIO_PROVEEDOR"]
    destino = row["MUNICIPIO"]
    peso = row["CANTIDAD_DESPACHOS"]
    if origen in coord_prov and destino in coord_dest:
        lat_o = coord_prov[origen]["lat"]
        lon_o = coord_prov[origen]["lon"]
        lat_d = coord_dest[destino]["lat"]
        lon_d = coord_dest[destino]["lon"]

        # Chequeo de NaNs
        if any(math.isnan(x) for x in [lat_o, lon_o, lat_d, lon_d]):
            print(f"❌ Coordenadas faltantes para: {origen} → {destino}")
            continue  # Saltar esta fila

        loc_origen = [lat_o, lon_o]
        loc_destino = [lat_d, lon_d]
        color = "gray"  
        for (low, high), col in rango_colores.items():
            if low <= peso < high:
                color = col
                break       
        folium.PolyLine(
            [loc_origen, loc_destino],
            color=color,
            weight=3,
            opacity=0.6,
            tooltip=f"{origen} → {destino}: {peso} despachos"
        ).add_to(grafo)

legend_html = """
<div style="
    position: fixed;
    bottom: 50px;
    left: 50px;
    width: 220px;
    background-color: white;
    z-index:9999;
    padding: 10px;
    border-radius: 5px;
    font-size: 14px;
    opacity: 0.9;
">
    <b>Rango de Despachos</b><br>
    <i style="background:blue; width: 10px; height: 10px; display: inline-block;"></i> 0 - 100 <br>
    <i style="background:green; width: 10px; height: 10px; display: inline-block;"></i> 100 - 1,000 <br>
    <i style="background:orange; width: 10px; height: 10px; display: inline-block;"></i> 1,000 - 10,000 <br>
    <i style="background:red; width: 10px; height: 10px; display: inline-block;"></i> 10,000 - 30,000 <br>
</div>
"""

grafo.get_root().html.add_child(folium.Element(legend_html))
grafo.save("despachos_mapa.html")


#______________
app = dash.Dash(__name__)
server = app.server


titulo_estilo = {
    'color': '#57B4BA',
    'textAlign': 'center',  
    'fontSize': '30px', 
    'fontWeight': 'bold',
}
subtitulo_estilo = {
    'color': '#A0C878',
    'textAlign': 'center', 
    'fontSize': '24px' 
}

app.layout = html.Div([
    html.H1("PRODUCTORES DE ETANOL Y B100 EN COLOMBIA", style=titulo_estilo),
    html.P("El biodiesel puro (B100) y el Bioetanol (Etanol) "
        "son productos derivados de la transformación de productos vegetales."), 
    html.P("Los datos son extraidos de SICOM, sobre los productores de B100 y Etanol en Colombia."
            "Se tiene el registro de 106.624 despachos realizados desde 01/01/2021 hasta 13/03/2025."
            "No se encuetran valores nulos o perdidos en los registros."
            "Cada despacho es referenciado por la fecha, el tipo de comprador"
            "departamento y municipio del proveedor y de despacho, el tipo de producto y el volumen despachado."),

    # DESPACHOS
    html.H2("Despachos por producto", style=subtitulo_estilo),
    html.H3("Tabla: Total de Despachos por producto"),
    dash_table.DataTable(
        id = 'tabla_despachos',
        columns=[
            {'name': 'Producto', 'id': 'Producto'},
            {'name': 'Cantidad', 'id': 'Cantidad'}
        ],
        data = t_desp.to_dict('records'), 
        style_table={'height': '100px', 'overflowY': 'auto'},  
        style_cell={'textAlign': 'center'},  
        style_header={"backgroundColor": "#A0C878", "color": "white", "fontWeight": "bold"},
        style_data={"textAlign": "center"},
    ),
    html.H3("Tabla: Total de Despachos por año"),
    dash_table.DataTable(
        id='tabla_despachos_total',
        columns=[ 
            {'name': 'Año', 'id': 'Año'},
            {'name': 'Total Despachos', 'id': 'Total Despachos'},
            {'name': 'Despachos B100', 'id': 'Despachos B100'},
            {'name': 'Despachos Etanol', 'id': 'Despachos Etanol'}
        ],
        data = table_desp.to_dict('records'),  
        style_table={'height': '200px', 'overflowY': 'auto'},  
        style_cell={'textAlign': 'center'}, 
        style_header={"backgroundColor": "#A0C878", "color": "white", "fontWeight": "bold"}, 
        style_data={"textAlign": "center"},
    ),
    html.P("Exceptuando el 2025, todos en todos los años tienen más de 20.000 despachos, "
    "siendo 2023 el que menos registros tiene (23.730) y 2024 el de mayor registro (25.940). "
    "En Colombia se produce en mayor cantidad Biodiesel puro B100 con 69.517 despachos. "
    "El Etanol tiene casi la mitad de esos despachos 37.107."),

    html.H3("Gráfico: Evolución mensual de despachos por año"),
    dcc.Graph(
        id = "grafico_etanol",
        figure = fig_etanol,
    ),
    dcc.Graph(
        id = "grafico_b100",
        figure = fig_b100,
    ),
    html.P("Para el Etanol, se observa una fluctuación significativa en la cantidad de despachos"
    "mes a mes, lo que sugiere que la demanda no es constante a lo largo del año. "
    "Algunos meses presentan caídas abruptas en ciertos años, como en abril de 2021 y mayo de 2025."
    "Para el B100, la variabilidad en los despachos es menor en comparación al etanol, "
    "lo que sugiere que su demanda o producción está mejor regulada."),


    # Volumen despachado
    html.H2("Volúmenes de Producto despachados", style=subtitulo_estilo),
    html.H3("Gráfico: Distribución de volúmenes"),
    dcc.Graph(
        id = "fig_e_v",
        figure = fig_e_v,
    ),
    dcc.Graph(
        id = "fig_b100_v",
        figure = fig_b100_v,
    ),
    html.P("La distribución del volúmen en galones vendidos es muy amplia en ambos casos."
           "La producción de Etanol, tiene asimetría negativa, con una producción desde 3.72 hasta más de 12 mil galones. "
           "Se encuentran observaciones registradas a lo largo de toda la amplitud."
           "Para el caso del B100, se tienen datos desde 10.4 galones hasta 3.01 millones de galones, "
           "con una alta asimetría positiva. Dentro de la dispersión, podemos ver dos grandes cúmulos de datos entre 0 a 500 mil galones, "
           "y el otro de datos dispersos entre los 2 a 2.7 millones de galones. Existen zonas sin presencia de datos, "
           "lo que podría indicar diferencia entre capacidades de producción."
           ),

    dcc.Graph(
        id = "fig_vol_year",
        figure = fig_vol_year,
    ),
    html.P("A lo largo de los años, la producción de B100 es mucho mayor que la de Etanol"
            "El año 2024, es el año de mayor volumen de ambos protuctos."),


    # Tipo de comprador
    html.H2("Tipo de comprador", style=subtitulo_estilo),
    dash_table.DataTable(
        columns=[
            {"name": "Tipo de Comprador", "id": "Producto"},
            {"name": "Cantidad", "id": "Cantidad"},
            {"name": "Porcentaje", "id": "Porcentaje"}
        ],
        data=t_comp.to_dict("records"),
        style_header={"backgroundColor": "#A0C878", "color": "white", "fontWeight": "bold"},
        style_cell={"textAlign": "center", "padding": "10px"},
        style_table={'height': '200px', 'overflowY': 'auto'},  
        style_data={"textAlign": "center"},
    ),


    # Georeferenciación
    html.H2("Ubicación del Despacho", style = subtitulo_estilo),
    html.H3("Tabla: Municipios proveedores"),
    dash_table.DataTable(
        columns=[
            {"name": "Departamento", "id": "Departamento"},
            {"name": "Municipio", "id": "Municipio"},
            {"name": "Cantidad de Despachos", "id": "Cantidad de Despachos"},
            {"name": "Volumen de Etanol", "id": "Volumen de Etanol"},
            {"name": "Volumen de B100", "id": "Volumen de B100"}
        ],
        data=tabla_proveedores.to_dict("records"),
        style_header={"backgroundColor": "#A0C878", "color": "white", "fontWeight": "bold"},
        style_cell={"textAlign": "center", "padding": "8px"},
        style_table={'height': '300px', 'overflowY': 'auto'},  # Definir el tamaño de la tabla
        style_data={"textAlign": "center"},
    ),
    html.P("Se identifican 15 municipios proveedores distribuidos en 8 departamentos."
        "Facatativá (Cundinamarca), es el mayor proveedor con 23,598 despachos, mientras que Barranquilla reporta solo 5 despachos."
        "Ningún municipio exporta ambos productos. 8 municipios exportan únicamente B100, mientras que 7 exportan solo Etanol."
        "Meta es el departamento con mayor cantidad de despachos registrados, siendo el único que exporta ambos productos."),
    html.H3("Tabla: Municipios de Destino"),
    dash_table.DataTable(
        columns=[
            {"name": "Departamento", "id": "Departamento"},
            {"name": "Municipio", "id": "Municipio"},
            {"name": "Cantidad de Despachos", "id": "Cantidad de Despachos"},
            {"name": "Volumen de Etanol", "id": "Volumen de Etanol"},
            {"name": "Volumen de B100", "id": "Volumen de B100"}
        ],
        data=tabla_destino.to_dict("records"),
        style_header={"backgroundColor": "#A0C878", "color": "white", "fontWeight": "bold"},
        style_cell={"textAlign": "center", "padding": "8px"},
        style_table={'height': '300px', 'overflowY': 'auto'},  # Definir el tamaño de la tabla
        style_data={"textAlign": "center"},
    ), 
    html.P("Bogotá, D.C. es el destino con mayor recepción de ambos productos, acumulando más de 93,000 despachos. "
        "Mientras que Nariño es el departamento con menor cantidad de despachos recibidos, con 130 despachos."
        "Uribia (La Guajira) recibe solo B100 y no tiene consumo reportado de Etanol."
        "Bogotá lidera la recepción de ambos productos."
        "Medellín (Antioquia), es el municipio con menor cantidad de despachos recibidos, solo 67."),

    html.H3("Mapa: Ubicación de los municipios Proveedores y Destino"),
    html.Iframe(
        srcDoc=open("mapa_municipios.html", "r", encoding="utf-8").read(),
        width="100%",
        height="600px"
    ),

    # Relaciones proveedor-destino
    html.H2("Relaciones Proveedor y destino", style = subtitulo_estilo),
    dcc.Graph(
        id = "fig_rel_p",
        figure = fig_rel_p,
    ),
    html.P("Los municipios de El cerrito(Valle del Cauca), Miranda(Cauca) y Santa Marta (Magdalena), "
    "son los municipios que más relaciones de envio tienen, cada uno envia a 6 municipios. "),
    dcc.Graph(
        id = "fig_rel_d",
        figure = fig_rel_d,
    ),
    html.P("Los municipios que más envio de producto reciben son Bogotá D.C. y Cartagena de Indias, "
    "que reciben de 13 y 12 municipios respectivamente."),
    html.H3("Mapa: Despachos entre Municipios"),
    html.Iframe(
        srcDoc=open("despachos_mapa.html", "r", encoding="utf-8").read(),
        width="100%",
        height="600px"
    ),

])

if __name__ == "__main__":
    app.run(debug=True)

