import streamlit as st
import mercadopago
import qrcode
import pandas as pd
from io import BytesIO
from datetime import datetime

# 1. Configuración de página
st.set_page_config(page_title="Hipergas Sistema", page_icon="🔥")

# --- LISTA DE USUARIOS ---
usuarios = {
    "admin": "hiper2024",
    "juan": "1234",
    "pedro": "5678"
}

# --- MEMORIA DE VENTAS (Temporal por ahora) ---
if "ventas" not in st.session_state:
    st.session_state["ventas"] = []

# --- PORTERO (Login) ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.image("Logo-Hipergas.jpg", width=250)
    st.title("🔐 Acceso Personal")
    user = st.text_input("Usuario").lower()
    password = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        if user in usuarios and usuarios[user] == password:
            st.session_state["autenticado"] = True
            st.session_state["usuario"] = user
            st.rerun()
        else:
            st.error("Error de credenciales")
else:
    # SI YA ENTRÓ
    st.sidebar.write(f"Usuario: **{st.session_state['usuario']}**")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state["autenticado"] = False
        st.rerun()

    # --- CASO 1: VISTA DEL ADMINISTRADOR ---
    if st.session_state["usuario"] == "admin":
        st.title("📊 Panel de Control - Ventas del Día")
        
        if not st.session_state["ventas"]:
            st.info("Todavía no se registraron ventas hoy.")
        else:
            df = pd.DataFrame(st.session_state["ventas"])
            
            # Mostrar resumen por chofer
            st.subheader("Resumen por Chofer")
            resumen = df.groupby("Chofer")["Monto"].sum()
            st.table(resumen)
            
            # Mostrar detalle de todas las ventas
            st.subheader("Detalle de movimientos")
            st.dataframe(df)

    # --- CASO 2: VISTA DEL CHOFER ---
    else:
        st.image("Logo-Hipergas.jpg", width=180)
        st.title(f"🚚 Chofer: {st.session_state['usuario'].capitalize()}")
        
        token = st.secrets.get("MP_ACCESS_TOKEN")
        if not token:
            st.error("Error de conexión con Mercado Pago")
        else:
            sdk = mercadopago.SDK(token)
            prod = st.selectbox("Carga de producto:", ["Garrafa 10kg", "Garrafa 15kg", "Cilindro 45kg"])
            precios = {"Garrafa 10kg": 15000, "Garrafa 15kg": 22000, "Cilindro 45kg": 45000}
            monto = precios[prod]

            if st.button(f"Generar QR - ${monto}"):
                # Generar el cobro
                pref = {"items": [{"title": f"Hipergas - {prod}", "quantity": 1, "unit_price": monto}]}
                res = sdk.preference().create(pref)
                link = res["response"]["init_point"]
                
                # Guardar en la "memoria" de la App
                nueva_venta = {
                    "Hora": datetime.now().strftime("%H:%M:%S"),
                    "Chofer": st.session_state["usuario"],
                    "Producto": prod,
                    "Monto": monto
                }
                st.session_state["ventas"].append(nueva_venta)
                
                # Mostrar QR
                qr_img = qrcode.make(link)
                buf = BytesIO()
                qr_img.save(buf, format="PNG")
                st.image(buf, caption=f"QR para {prod}")
                st.success(f"Venta registrada en tu planilla del día.")
