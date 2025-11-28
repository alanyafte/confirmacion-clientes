import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import traceback

# Configuración de página PRIMERO
st.set_page_config(
    page_title="Confirmación de Pedido",
    page_icon="✅", 
    layout="centered"
)

try:
    st.title("✅ Confirmación de Pedido")
    st.info("Por favor revise los detalles de su pedido")
    
    # Debug: Verificar que funciona
    st.success("🔍 App cargada - Verificando conexión...")
    
    # Configuración para Google Sheets (SOLO LECTURA)
    SCOPE = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

    def conectar_google_sheets_solo_lectura():
        """Conectar con Google Sheets en modo solo lectura"""
        try:
            # Verificar secrets
            if "gservice_account" not in st.secrets:
                st.error("❌ No se configuraron los secrets")
                return None
                
            creds_dict = {
                "type": st.secrets["gservice_account"]["type"],
                "project_id": st.secrets["gservice_account"]["project_id"],
                "private_key_id": st.secrets["gservice_account"]["private_key_id"],
                "private_key": st.secrets["gservice_account"]["private_key"].replace('\\n', '\n'),
                "client_email": st.secrets["gservice_account"]["client_email"],
                "client_id": st.secrets["gservice_account"]["client_id"],
                "auth_uri": st.secrets["gservice_account"]["auth_uri"],
                "token_uri": st.secrets["gservice_account"]["token_uri"]
            }
            
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
            client = gspread.authorize(creds)
            
            sheet_id = st.secrets["gsheets"]["ordenes_bordado_sheet_id"]
            spreadsheet = client.open_by_key(sheet_id)
            sheet = spreadsheet.worksheet("OrdenesBordado")
            
            st.success("✅ Conexión a Google Sheets exitosa")
            return sheet
            
        except Exception as e:
            st.error(f"❌ Error en conexión: {e}")
            return None

    def obtener_orden_por_id(pedido_id):
        """Obtener una orden específica"""
        sheet = conectar_google_sheets_solo_lectura()
        if sheet:
            try:
                data = sheet.get_all_records()
                df = pd.DataFrame(data)
                
                # Debug: mostrar columnas
                st.write(f"🔍 Columnas encontradas: {list(df.columns)}")
                st.write(f"🔍 Buscando pedido: {pedido_id}")
                
                orden = df[df['Número Orden'] == pedido_id]
                if not orden.empty:
                    st.success(f"✅ Pedido {pedido_id} encontrado")
                    return orden.iloc[0]
                else:
                    st.error(f"❌ Pedido {pedido_id} no encontrado")
                    return None
                    
            except Exception as e:
                st.error(f"❌ Error buscando orden: {e}")
                return None
        return None

    # Obtener parámetros de la URL
    query_params = st.query_params
    pedido_id = query_params.get("pedido", [None])[0] if "pedido" in query_params else None
    
    st.write(f"🔍 Parámetro pedido: {pedido_id}")
    
    if not pedido_id:
        st.warning("📝 Ingrese un número de pedido en la URL")
        st.info("💡 Ejemplo: ?pedido=BORD-001")
        
        # Mostrar interfaz de prueba
        pedido_ejemplo = st.text_input("O pruebe con un pedido:")
        if pedido_ejemplo:
            pedido_id = pedido_ejemplo
        else:
            st.stop()

    # Obtener datos del pedido
    with st.spinner("Buscando información del pedido..."):
        orden = obtener_orden_por_id(pedido_id)
    
    if orden is None:
        st.error("No se pudo cargar la información del pedido")
        st.stop()
    
    # MOSTRAR INFORMACIÓN DEL PEDIDO
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Información del Pedido")
        st.write(f"**Número:** {orden.get('Número Orden', 'N/A')}")
        st.write(f"**Cliente:** {orden.get('Cliente', 'N/A')}")
        st.write(f"**Vendedor:** {orden.get('Vendedor', 'N/A')}")
        st.write(f"**Entrega:** {orden.get('Fecha Entrega', 'N/A')}")
    
    with col2:
        st.subheader("🎨 Especificaciones")
        st.write(f"**Diseño:** {orden.get('Nombre Diseño', 'N/A')}")
        st.write(f"**Colores Hilos:** {orden.get('Colores de Hilos', 'N/A')}")
        st.write(f"**Medidas:** {orden.get('Medidas Bordado', 'N/A')}")
        st.write(f"**Posición:** {orden.get('Posición Bordado', 'N/A')}")

    # Mostrar imágenes si existen
    st.subheader("🖼️ Diseños")
    col_disenos = st.columns(5)
    for i in range(1, 6):
        diseno_col = f'Diseño {i}'
        if orden.get(diseno_col) and str(orden[diseno_col]) not in ['', 'nan', 'None']:
            with col_disenos[i-1]:
                try:
                    st.image(orden[diseno_col], caption=f"Diseño {i}", use_column_width=True)
                except:
                    st.markdown(f"[📎 Ver Diseño {i}]({orden[diseno_col]})")

    # SECCIÓN DE CONFIRMACIÓN
    st.markdown("---")
    st.subheader("🔏 Confirmación del Pedido")
    
    opcion = st.radio(
        "¿La información es correcta?",
        ["✅ Sí, confirmar pedido", "❌ No, necesito cambios"]
    )
    
    if opcion == "✅ Sí, confirmar pedido":
        nombre = st.text_input("✍️ Nombre completo:")
        email = st.text_input("📧 Email:")
        
        if st.button("🎯 Confirmar Pedido"):
            if nombre and email:
                st.balloons()
                st.success("🎉 ¡Confirmación exitosa!")
                st.info("📧 Nos contactaremos para proceder con producción")
            else:
                st.error("Complete todos los campos")
    
    else:
        cambios = st.text_area("📝 Cambios necesarios:")
        contacto = st.text_input("📞 Contacto:")
        
        if st.button("📤 Enviar Cambios"):
            if cambios and contacto:
                st.success("✅ Cambios enviados")
                st.info("🛠️ Ajustaremos según sus indicaciones")

except Exception as e:
    st.error("❌ ERROR CRÍTICO")
    st.code(traceback.format_exc())
                
