import streamlit as st
import mercadopago
import qrcode
import pandas as pd
from io import BytesIO
from datetime import datetime
from gspread_streamlit import gspread_streamlit

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Sistema Hipergas", page_icon="🔥")

# 2. CONEXIÓN A GOOGLE SHEETS
# Esta función busca la "llave" en tus Secrets y abre el Excel
def conectar_google():
    try:
        conn = gspread_streamlit.authorize(st.secrets["gcp_service_account"])
        # IMPORTANTE: El nombre debe ser EXACTO al de tu archivo en Google Drive
        sh = conn.open("Rendicion_Hipergas")
        return sh.sheet1
    except Exception as e:
        st.error(f"Error de conexión con Google: {e}")
        return None

sheet = conectar_google()

# 3. BASE DE USUARIOS
usuarios = {"admin": "hiper2024", "juan": "1234", "pedro": "5678"}

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

# --- LÓGICA DE ACCESO ---
if not st.session_state["autenticado"]:
    st.title("🔐 Acceso Hipergas")
    user = st.text_input("Usuario").lower()
    password = st.text_input("Contraseña", type="password")
    
    if st.button("Entrar"):
        if user in usuarios and usuarios[user] == password:
            st.session_state["autenticado"] = True
            st.session_state["usuario"] = user
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

# --- APP PARA USUARIOS LOGUEADOS ---
else:
    st.sidebar.title(f"Chofer: {st.session_state['usuario'].capitalize()}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state["autenticado"] = False
        st.rerun()

    # VISTA ADMINISTRADOR
    if st.session_state["usuario"] == "admin":
        st.title("📊 Resumen de Ventas (Google Sheets)")
        
        if sheet:
            if st.button("🔄 Actualizar Tabla"):
                st.rerun()
            
            # Lee los datos del Excel y los muestra en una tabla
            datos = pd.DataFrame(sheet.get_all_records())
            if not datos.empty:
                st.dataframe(datos, use_container_width=True)
            else:
                st.info("Todavía no hay ventas anotadas en el Excel.")
        else:
            st.warning("No se pudo conectar con la planilla. Revisá los Secrets y el nombre del archivo.")

    # VISTA CHOFERES
    else:
        st.title("🚚 Registro de Venta")
        
        # Mercado Pago
        token = st.secrets.get("MP_ACCESS_TOKEN")
        sdk = mercadopago.SDK(token)

        productos = {
            "Garrafa 10kg": 15000,
            "Garrafa 15kg": 22000,
            "Cilindro 45kg": 45000
        }
        
        prod = st.selectbox("Producto vendido:", list(productos.keys()))
        monto = productos[prod]

        if st.button(f"Generar QR y Guardar ${monto}"):
            with st.spinner("Procesando..."):
                # A. ANOTAR EN EXCEL
                fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                if sheet:
                    try:
                        sheet.append_row([fecha, st.session_state["usuario"], prod, monto])
                        st.success("✅ Venta anotada en el Excel")
                    except Exception as e:
                        st.error(f"Error al anotar: {e}")

                # B. GENERAR QR
                preference_data = {"items": [{"title": prod, "quantity": 1, "unit_price": monto}]}
                res = sdk.preference().create(preference_data)
                link = res["response"]["init_point"]

                qr = qrcode.make(link)
                buf = BytesIO()
                qr.save(buf, format="PNG")
                st.image(buf, caption=f"QR de pago para {prod}")
