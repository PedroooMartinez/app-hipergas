import streamlit as st
import mercadopago
import qrcode
import pandas as pd
from io import BytesIO
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Sistema Hipergas", page_icon="🔥")

# 2. CONEXIÓN A GOOGLE SHEETS
def conectar_google():
    try:
        # Definimos los permisos que necesita la app
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        # Sacamos los datos de tus Secrets
        info_llave = st.secrets["gcp_service_account"]
        
        # Creamos las credenciales
        creds = Credentials.from_service_account_info(info_llave, scopes=scope)
        client = gspread.authorize(creds)
        
        # Abrimos la planilla
        sh = client.open("Rendicion_Hipergas")
        return sh.sheet1
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

sheet = conectar_google()

# 3. LOGIN Y USUARIOS
usuarios = {"admin": "hiper2024", "juan": "1234", "pedro": "5678"}

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

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
            st.error("Error de acceso")

else:
    # --- APP PARA USUARIOS LOGUEADOS ---
    st.sidebar.title(f"Hola {st.session_state['usuario'].capitalize()}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state["autenticado"] = False
        st.rerun()

    # VISTA ADMIN
    if st.session_state["usuario"] == "admin":
        st.title("📊 Resumen de Ventas")
        if sheet:
            if st.button("🔄 Actualizar"):
                st.rerun()
            datos = pd.DataFrame(sheet.get_all_records())
            st.dataframe(datos, use_container_width=True)
        else:
            st.error("No se pudo conectar con el Excel.")

    # VISTA CHOFERES
    else:
        st.title("🚚 Registro de Venta")
        token = st.secrets.get("MP_ACCESS_TOKEN")
        sdk = mercadopago.SDK(token)
        productos = {"Garrafa 10kg": 15000, "Garrafa 15kg": 22000, "Cilindro 45kg": 45000}
        prod = st.selectbox("Producto:", list(productos.keys()))
        monto = productos[prod]

        if st.button(f"Generar QR y Guardar"):
            # ANOTAR EN EXCEL
            if sheet:
                fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                sheet.append_row([fecha, st.session_state["usuario"], prod, monto])
                st.success("✅ Venta anotada")

            # GENERAR QR
            res = sdk.preference().create({"items": [{"title": prod, "quantity": 1, "unit_price": monto}]})
            qr = qrcode.make(res["response"]["init_point"])
            buf = BytesIO()
            qr.save(buf, format="PNG")
            st.image(buf, caption=f"QR de pago ${monto}")
