# app/app.py
import os
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

# Город по умолчанию (исправлено: getenv вместо getevn)
DEFAULT_CITY = os.getenv("WEATHER_CITY", "Moscow")

class WeatherEchoHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        # 1. Получаем и показываем X-Forwarded-For
        xff = self.headers.get('X-Forwarded-For', 'Not set')
        
        # 2. Определяем город
        city = params.get('city', [DEFAULT_CITY])[0]
        
        # 3. Формат ответа
        response_format = params.get('format', ['text'])[0]
        
        try:
            # 4. Запрашиваем погоду через wttr.in
            weather_url = f"https://wttr.in/{city}?format=3&lang=ru"
            headers = {'User-Agent': 'curl/7.68.0'}
            weather_resp = requests.get(weather_url, headers=headers, timeout=5)
            weather_data = weather_resp.text.strip() if weather_resp.status_code == 200 else "Weather unavailable"
        except Exception as e:
            weather_data = f"Error: {str(e)}"
        
        # 5. Формируем ответ
        if response_format == 'json':
            response = {
                "X-Forwarded-For": xff,
                "weather": weather_data,
                "city": city,
                "note": "X-Forwarded-For contains proxy chain: client -> nginx1 -> ... -> app"
            }
            body = json.dumps(response, ensure_ascii=False).encode('utf-8')
            content_type = 'application/json; charset=utf-8'
        else:
            body = f"""╔════════════════════════════════════╗
║  PROXY CHAIN TEST + WEATHER APP   ║
╠════════════════════════════════════╣
🔗 X-Forwarded-For: {xff}
🌆 City: {city}
🌡️  Weather: {weather_data}
╚════════════════════════════════════╝
""".encode('utf-8')
            content_type = 'text/plain; charset=utf-8'
        
        # 6. Отправляем ответ
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)
    
    def log_message(self, format, *args):
        pass  # Тихий режим

if __name__ == '__main__':
    print(f"🌤️  Weather+Proxy app starting on port 80 (default city: {DEFAULT_CITY})")
    HTTPServer(('0.0.0.0', 80), WeatherEchoHandler).serve_forever()