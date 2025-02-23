import streamlit as st
import pandas as pd
import plotly.express as px
import json
from io import BytesIO
from fpdf import FPDF

# Título en la sección principal
st.title("📊 Calculadora de Presupuestos Personal 🏠")

# Menú lateral para configuraciones
with st.sidebar:
    st.header("Configuraciones")

    # Lista de unidades de medida
    unit_types = ["Metros (m)", "Cantidad (Und.)", "Pieza (Pz)", "Peso (Kg)"]
    iva_percentage = st.slider("IVA (%)", 0, 21, 21)

    # Mostrar el slider de IVA en el menú lateral
    st.markdown("### Opciones de IVA")
    st.write(f"IVA seleccionado: {iva_percentage}%")

    # Cargar presupuesto desde archivo JSON en el menú lateral
    st.subheader("📂 Cargar presupuesto guardado")
    uploaded_file = st.file_uploader("Sube un archivo JSON", type=["json"])
    
    if uploaded_file:
        load_budget(uploaded_file)

# Inicializar session_state si no existe
if "data" not in st.session_state:
    st.session_state.data = []
if "history" not in st.session_state:
    st.session_state.history = []

# Función para agregar datos
def add_entry(room, category, subcategory, product, unit_type, units, unit_price):
    total_cost = unit_price * units  # Cálculo automático del costo total

    if not subcategory:  # Validación de subcategoría vacía
        if not st.session_state.get("allow_empty_subcategory", False):
            confirm = st.checkbox("¿Desea continuar sin subcategoría?", key="allow_empty_subcategory")
            if not confirm:
                return
    
    new_entry = {
        "Estancia": room,
        "Categoría": category,
        "Subcategoría": subcategory if subcategory else "Sin subcategoría",
        "Producto": product,
        "Tipo de Unidad": unit_type,
        "Unidades": units,
        "Precio Unitario (€)": unit_price,
        "Costo Total (€)": total_cost
    }
    
    st.session_state.data.append(new_entry)
    st.session_state.history.append(st.session_state.data.copy())  # Guardar historial de cambios

# Función para cargar presupuesto desde archivo JSON
def load_budget(file):
    content = json.load(file)
    st.session_state.data = content
    # Asegurarnos de que todas las entradas tengan la columna 'Costo Total (€)'
    for entry in st.session_state.data:
        if "Costo Total (€)" not in entry:
            entry["Costo Total (€)"] = entry["Precio Unitario (€)"] * entry["Unidades"]
    st.success("📂 Presupuesto cargado correctamente")

# Guardar presupuesto en JSON
def save_budget():
    return json.dumps(st.session_state.data, indent=4)

# Exportar a Excel
def export_to_excel():
    df = pd.DataFrame(st.session_state.data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Presupuesto")
    return output.getvalue()

# Crear PDF con fuente TrueType
def generate_pdf():
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Usar una fuente TrueType (DejaVuSans) que soporta caracteres Unicode como el euro
    pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)  # Añadimos la fuente TrueType
    pdf.set_font('DejaVu', '', 12)

    pdf.cell(200, 10, "Presupuesto de Reforma", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("DejaVu", "", 12)
    df = pd.DataFrame(st.session_state.data)

    for _, row in df.iterrows():
        pdf.cell(200, 10, f"{row['Estancia']} - {row['Categoría']} - {row['Subcategoría']}", ln=True)
        pdf.cell(200, 10, f"Producto: {row['Producto']} - {row['Unidades']} {row['Tipo de Unidad']}", ln=True)
        pdf.cell(200, 10, f"Precio Unitario: {row['Precio Unitario (€)']} € - Total: {row['Costo Total (€)']} €", ln=True)
        pdf.ln(5)

    # Guardamos el PDF en un buffer de memoria
    output = BytesIO()
    pdf_output = pdf.output(dest='S').encode('latin1')  # Generamos el PDF como bytes
    output.write(pdf_output)  # Escribimos en el buffer
    output.seek(0)  # Nos aseguramos de que el buffer esté listo para leer

    return output  # Retornamos el buffer con el archivo PDF

# Formulario de entrada en el contenido principal
with st.form("budget_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        room = st.text_input("Estancia", placeholder="Ej: Cocina")
        category = st.text_input("Categoría", placeholder="Ej: Suelos")
    with col2:
        subcategory = st.text_input("Subcategoría (Opcional)", placeholder="Ej: Parquet")
        product = st.text_input("Producto", placeholder="Ej: Baldosas")
        unit_type = st.selectbox("Tipo de Unidad", unit_types)
    with col3:
        units = st.number_input("Unidades", min_value=1, step=1, value=1)
        unit_price = st.number_input("Precio Unitario (€)", min_value=0.0, step=10.0)

    submitted = st.form_submit_button("Añadir")
    if submitted and room and category and product and unit_price:
        add_entry(room, category, subcategory, product, unit_type, units, unit_price)
        st.success("Añadido correctamente")

# Mostrar tabla y gráficos en el contenido principal
df = pd.DataFrame(st.session_state.data)
if not df.empty:
    st.subheader("📊 Presupuesto detallado")
    st.dataframe(df)

    # Calcular IVA
    st.subheader("💰 Resumen del presupuesto")
    total_cost = df["Costo Total (€)"].sum()
    iva_amount = total_cost * (iva_percentage / 100)
    final_cost = total_cost + iva_amount

    st.write(f"Subtotal: **{total_cost:.2f} €**")
    st.write(f"IVA ({iva_percentage}%): **{iva_amount:.2f} €**")
    st.write(f"Total con IVA: **{final_cost:.2f} €**")

    # Gráficos de distribución
    st.subheader("📊 Distribución del presupuesto")
    
    # Gráfico por Categorías
    fig1 = px.pie(df, names="Categoría", values="Costo Total (€)", title="Gasto por Categoría")
    st.plotly_chart(fig1)
    
    # Gráfico por Subcategorías
    if "Subcategoría" in df.columns:
        fig2 = px.pie(df, names="Subcategoría", values="Costo Total (€)", title="Gasto por Subcategoría")
        st.plotly_chart(fig2)

    # Botón para descargar Excel
    st.download_button(
        label="📥 Descargar Excel",
        data=export_to_excel(),
        file_name="presupuesto_reforma.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Botón para guardar el presupuesto en JSON
    st.download_button(
        label="💾 Guardar Presupuesto",
        data=save_budget(),
        file_name="presupuesto.json",
        mime="application/json"
    )

    # Botón para descargar informe en PDF
    st.download_button(
        label="📄 Generar Informe PDF",
        data=generate_pdf(),
        file_name="presupuesto_reforma.pdf",
        mime="application/pdf"
    )

    # Botón para borrar datos
    if st.button("🗑️ Borrar todo el presupuesto"):
        st.session_state.data = []
        st.rerun()


