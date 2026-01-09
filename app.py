import streamlit as st
import mercadopago
import qrcode
from io import BytesIO

# Título de la App
st.title("🔥 Hipergas Pagos")
st.write("Sistema de cobro para repartidores")

# Configurar Mercado Pago (Aquí después pondrás tu Token real)
# Por ahora dejamos un espacio para que no falle
access_token = st.text_input("Ingresá tu Access Token de MP para probar:", type="password")

if access_token:
    sdk = mercadopago.SDK(access_token)
    
    # Selección de productos
    producto = st.selectbox("Producto:", ["Garrafa 10kg", "Garrafa 15kg", "Cilindro 45kg"])
    precios = {"Garrafa 10kg": 15000, "Garrafa 15kg": 22000, "Cilindro 45kg": 45000}
    monto = precios[producto]

    if st.button(f"Cobrar ${monto}"):
        # Crear link de pago
        preference_data = {
            "items": [{"title": producto, "quantity": 1, "unit_price": monto}]
        }
        res = sdk.preference().create(preference_data)
        link_pago = res["response"]["init_point"]

        # Generar imagen QR
        qr = qrcode.make(link_pago)
        buf = BytesIO()
        qr.save(buf, format="PNG")
        
        st.success("¡QR Generado! Pedile al cliente que escanee:")
        st.image(buf)
else:
    st.warning("Por favor, ingresá un Access Token de Mercado Pago para generar cobros reales.")
