import streamlit as st
import pandas as pd
import plotly.express as px
import json
import io  # Asegurar que io está importado
from io import BytesIO
from fpdf import FPDF

st.title("📊 Calculadora de Presupuesto de Reforma 🏠")

# Lista de unidades de medida
unit_types = ["Metros (m)", "Cantidad (Und.)", "Pieza (Pz)", "Peso (Kg)"]

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

# Cargar presupuesto desde JSON
def load_budget(file):
    content = json.load(file)
    st.session_state.data = content
    # Asegurar que todas las entradas tengan la columna 'Costo Total (€)'
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

# Generar PDF
def generate_pdf():
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)  # Añadir fuente TrueType
    pdf.set_font('DejaVu', '', 12)

    pdf.cell(200, 10, "Presupuesto de Reforma", ln=True, align="C")
    pdf.ln(10)

    df = pd.DataFrame(st.session_state.data)

    for _, row in df.iterrows():
        pdf.cell(200, 10, f"{row['Estancia']} - {row['Categoría']} - {row['Subcategoría']}", ln=True)
        pdf.cell(200, 10, f"Producto: {row['Producto']} - {row['Unidades']} {row['Tipo de Unidad']}", ln=True)
        pdf.cell(200, 10, f"Precio Unitario: {row['Precio Unitario (€)']} € - Total: {row['Costo Total (€)']} €", ln=True)
        pdf.ln(5)

    output = BytesIO()
    pdf_output = pdf.output(dest='S').encode('latin1')
    output.write(pdf_output)
    output.seek(0)

    return output

# Formulario de entrada
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

# Mostrar presupuesto detallado si hay datos
if st.session_state.data:
    st.subheader("📊 Presupuesto detallado")
    
    df = pd.DataFrame(st.session_state.data)

    for index, row in df.iterrows():
        col1, col2 = st.columns([6, 1])
        col1.write(f"📌 {row['Producto']} ({row['Unidades']} {row['Tipo de Unidad']}) - {row['Costo Total (€)']} €")
        if col2.button("❌", key=f"delete_{index}"):
            st.session_state.data.pop(index)
            st.rerun()  # Recargar la interfaz

    # Mostrar tabla completa
    st.dataframe(df)

    # Resumen de costos
    st.subheader("💰 Resumen de Costos")
    total_cost = df["Costo Total (€)"].sum()
    iva_percentage = st.slider("IVA (%)", 0, 21, 21)
    iva_amount = total_cost * (iva_percentage / 100)
    final_cost = total_cost + iva_amount

    st.write(f"Subtotal: **{total_cost:.2f} €**")
    st.write(f"IVA ({iva_percentage}%): **{iva_amount:.2f} €**")
    st.write(f"Total con IVA: **{final_cost:.2f} €**")

    # Gráficos de distribución
    st.subheader("📊 Distribución del presupuesto")
    fig1 = px.pie(df, names="Categoría", values="Costo Total (€)", title="Gasto por Categoría")
    st.plotly_chart(fig1)

    if "Subcategoría" in df.columns:
        fig2 = px.pie(df, names="Subcategoría", values="Costo Total (€)", title="Gasto por Subcategoría")
        st.plotly_chart(fig2)

    # Descarga de archivos
    st.download_button("📥 Descargar Excel", data=export_to_excel(), file_name="presupuesto.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.download_button("💾 Guardar Presupuesto", data=save_budget(), file_name="presupuesto.json", mime="application/json")
    st.download_button("📄 Generar Informe PDF", data=generate_pdf(), file_name="presupuesto.pdf", mime="application/pdf")

    # Botón para borrar todo el presupuesto
    if st.button("🗑️ Borrar todo el presupuesto"):
        st.session_state.data = []
        st.rerun()

# Cargar presupuesto desde JSON
st.subheader("📂 Cargar presupuesto guardado")
uploaded_file = st.file_uploader("Sube un archivo JSON", type=["json"])
if uploaded_file:
    load_budget(uploaded_file)
