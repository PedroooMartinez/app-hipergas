import streamlit as st
import mercadopago
import qrcode
from io import BytesIO

# 1. Configuración de página
st.set_page_config(page_title="Hipergas Pay", page_icon="🔥")

st.title("🔥 Hipergas Pagos")
st.write("Sistema de cobro para repartidores")

# 2. Intentar sacar el Token de los "Secrets" (la caja fuerte)
token = st.secrets.get("MP_ACCESS_TOKEN")

if not token:
    st.error("No se encontró el Token en los Secrets de Streamlit.")
    st.info("Por favor, asegúrate de haberlo configurado en Settings > Secrets.")
else:
    try:
        # 3. Conectar con Mercado Pago usando el Token secreto
        sdk = mercadopago.SDK(token)
        st.success("✅ Sistema Conectado con Mercado Pago")
        
        # 4. Interfaz de productos
        producto = st.selectbox("Seleccione el producto a cobrar:", 
                                ["Garrafa 10kg", "Garrafa 15kg", "Cilindro 45kg"])
        
        precios = {"Garrafa 10kg": 15000, "Garrafa 15kg": 22000, "Cilindro 45kg": 45000}
        monto = precios[producto]
        
        if st.button(f"Generar QR para cobrar ${monto}"):
            # Crear la orden de pago
            preference_data = {
                "items": [
                    {
                        "title": f"Hipergas - {producto}",
                        "quantity": 1,
                        "unit_price": monto,
                    }
                ]
            }
            preference_response = sdk.preference().create(preference_data)
            link_pago = preference_response["response"]["init_point"]

            # Generar el código QR
            qr = qrcode.make(link_pago)
            buf = BytesIO()
            qr.save(buf, format="PNG")
            
            st.write("---")
            st.subheader("¡QR Generado!")
            st.image(buf, caption="Mostrá este QR al cliente para que escanee")
            st.balloons()

    except Exception as e:
        st.error(f"Hubo un problema con el Token: {e}")
