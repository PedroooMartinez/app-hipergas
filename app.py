import streamlit as st
import mercadopago
import qrcode
from io import BytesIO

# 1. Configuración de página
st.set_page_config(page_title="Hipergas Pay", page_icon="🔥")

# --- LISTA DE CHOFERES (Cambiá esto cuando quieras) ---
# El formato es "usuario": "contraseña"
usuarios = {
    "admin": "hiper2024",
    "juan": "1234",
    "pedro": "5678"
}

# --- ESTO ES EL 'PORTERO' DE LA APP (El Login) ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

# Si no está identificado, le mostramos la puerta cerrada
if not st.session_state["autenticado"]:
    st.image("Logo-Hipergas.jpg", width=250)
    st.title("🔐 Acceso Choferes")
    
    usuario = st.text_input("Nombre de Usuario").lower()
    clave = st.text_input("Contraseña", type="password")

    if st.button("Entrar"):
        if usuario in usuarios and usuarios[usuario] == clave:
            st.session_state["autenticado"] = True
            st.session_state["usuario"] = usuario
            st.rerun()
        else:
            st.error("Nombre o clave incorrectos")

# --- SI PASÓ EL PORTERO, VE LA APP DE COBRO ---
else:
    # Botoncito para salir
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state["autenticado"] = False
        st.rerun()

    st.image("Logo-Hipergas.jpg", width=200)
    st.title(f"Hola {st.session_state['usuario'].capitalize()} 👋")
    
    # Aquí empieza tu app de siempre
    token = st.secrets.get("MP_ACCESS_TOKEN")
    if not token:
        st.error("Falta el Token de Mercado Pago")
    else:
        sdk = mercadopago.SDK(token)
        producto = st.selectbox("¿Qué vas a cobrar?", ["Garrafa 10kg", "Garrafa 15kg", "Cilindro 45kg"])
        precios = {"Garrafa 10kg": 15000, "Garrafa 15kg": 22000, "Cilindro 45kg": 45000}
        monto = precios[producto]

        if st.button(f"Generar QR de ${monto}"):
            preference_data = {"items": [{"title": f"Hipergas - {producto}", "quantity": 1, "unit_price": monto}]}
            res = sdk.preference().create(preference_data)
            link = res["response"]["init_point"]
            
            qr_img = qrcode.make(link)
            buf = BytesIO()
            qr_img.save(buf, format="PNG")
            
            st.image(buf, caption=f"Cobro de {producto} para {st.session_state['usuario']}")
  
