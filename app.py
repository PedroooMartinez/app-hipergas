import streamlit as st
import mercadopago
import qrcode
import pandas as pd
from io import BytesIO
from datetime import datetime
from gspread_streamlit import gspread_streamlit

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Sistema Hipergas", page_icon="🔥")

# 2. CONEXIÓN A GOOGLE SHEETS (Segura)
def conectar_google():
    try:
        # Usa los Secrets que pegamos antes
        conn = gspread_streamlit.authorize(st.secrets["gcp_service_account"])
        # Abre la planilla por su nombre exacto
        sh = conn.open("Rendicion_Hipergas")
        return sh.sheet1
    except Exception as e:
        st.error(f"Error conectando a Google Sheets: {e}")
        return None

sheet = conectar_google()

# 3. BASE DE USUARIOS
usuarios = {"admin": "hiper2024", "juan": "1234", "pedro": "5678"}

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

# --- LÓGICA DE LOGIN ---
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

# --- APP UNA VEZ LOGUEADO ---
else:
    st.sidebar.title(f"Bienvenido {st.session_state['usuario'].capitalize()}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state["autenticado"] = False
        st.rerun()

    # --- VISTA ADMINISTRADOR ---
    if st.session_state["usuario"] == "admin":
        st.title("📊 Control de Ventas Real")
        st.write("Estos datos se cargan directamente desde Google Sheets.")

        if sheet:
            if st.button("🔄 Actualizar Datos"):
                st.rerun()
            
            # Traer datos de la planilla
            datos = pd.DataFrame(sheet.get_all_records())
            
            if not datos.empty:
                st.dataframe(datos, use_container_width=True)
            else:
                st.info("Aún no hay ventas registradas en el Excel.")
        else:
            st.error("No se pudo cargar la planilla. Revisá el nombre en Google Sheets.")

    # --- VISTA CHOFERES ---
    else:
        st.title("🚚 Registrar Nueva Venta")
        
        # Configuración de Mercado Pago
        token = st.secrets.get("MP_ACCESS_TOKEN")
        sdk = mercadopago.SDK(token)

        productos = {
            "Garrafa 10kg": 15000,
            "Garrafa 15kg": 22000,
            "Cilindro 45kg": 45000
        }
        
        prod = st.selectbox("Seleccione Producto:", list(productos.keys()))
        monto = productos[prod]

        if st.button(f"Generar QR y Guardar - ${monto}"):
            with st.spinner("Anotando en el Excel y generando QR..."):
                # A. Guardar en Google Sheets
                fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                if sheet:
                    try:
                        sheet.append_row([fecha, st.session_state["usuario"], prod, monto])
                        st.success("✅ Venta guardada en el Excel")
                    except:
                        st.error("No se pudo guardar en el Excel, pero generaremos el QR igual.")

                # B. Generar QR de Mercado Pago
                preference_data = {
                    "items": [{"title": prod, "quantity": 1, "unit_price": monto}]
                }
                preference_response = sdk.preference().create(preference_data)
                link_pago = preference_response["response"]["init_point"]

                # C. Crear imagen QR
                qr = qrcode.QRCode(box_size=10, border=4)
                qr.add_data(link_pago)
                qr.make(fit=True)
                img_qr = qr.make_image(fill_color="black", back_color="white")
                
                buf = BytesIO()
                img_qr.save(buf, format="PNG")
                
                st.image(buf, caption=f"QR de Pago - {prod}")
                st.warning("Pedile al cliente que escanee para pagar.")
