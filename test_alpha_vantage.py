import requests

# Configura tu clave API y el ticker que quieres probar
API_KEY = "FT7MM3CGLH6PGW2J"  # Reemplaza con tu clave real
TICKER = "AAPL"  # Ticker a probar (puedes cambiarlo a otro como MSFT, GOOGL, etc.)

# URL de la API para datos intradía (1 minuto)
URL = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={TICKER}&interval=1min&apikey={API_KEY}"

try:
    # Hacer la solicitud a la API
    response = requests.get(URL)
    response.raise_for_status()  # Levanta una excepción si hay un error HTTP

    # Convertir la respuesta a JSON
    data = response.json()

    # Verificar si la solicitud fue exitosa
    if "Time Series (1min)" in data:
        # Obtener el último precio disponible
        latest_time = list(data["Time Series (1min)"].keys())[0]
        latest_price = float(data["Time Series (1min)"][latest_time]["4. close"])
        print(f"Último precio de {TICKER}: ${latest_price:.2f} (a las {latest_time})")
        print("La clave API parece funcionar correctamente.")
    else:
        print("Error: La solicitud fue exitosa, pero no se encontraron datos de Time Series.")
        print("Respuesta completa:", data)

except requests.exceptions.HTTPError as e:
    print(f"Error HTTP: {e}")
    print(f"Detalles: {response.text if 'response' in locals() else 'No response'}")
except requests.exceptions.RequestException as e:
    print(f"Error de conexión: {e}")
except ValueError as e:
    print(f"Error al procesar los datos: {e}")
    print("Respuesta completa:", data if 'data' in locals() else "No data")
except Exception as e:
    print(f"Error inesperado: {e}")
