from flask import Flask, request
import requests

app = Flask(__name__)

# --- 配置区 ---
gaode_key = "USE YOUR OWN"
qweather_key = "USE YOUR OWN"
API_host = "USE YOUR OWN"

def get_location_by_ip(user_ip):
    try:
        # 1. 调用高德 IP 定位
        url = f"https://restapi.amap.com/v3/ip?ip={user_ip}&output=json&key={gaode_key}"
        response = requests.get(url, timeout=5)
        data = response.json()

        if data.get("status") == "1":
            rect = data.get("rectangle", "0,0;0,0")
            first_point = rect.split(';')[0]  # "经度,纬度"
            return {
                "province": data.get("province", "未知省份"),
                "city": data.get("city", "未知城市"),
                "lon_lat": first_point 
            }
    except Exception as e:
        pass
    return None

def get_weather_by_coords(lon_lat):
    try:
        # 2. 直接用坐标查询实时天气
        url = f"https://{API_host}/v7/weather/now?location={lon_lat}&key={qweather_key}"
        res = requests.get(url, timeout=5)
        res_json = res.json()

        if res_json.get("code") == "200":
            return res_json.get("now")
    except Exception as e:
        pass
    return None

@app.route('/weather')
def weather_service():
    user_ip = request.remote_addr
    
    # 第一步：获取位置
    loc = get_location_by_ip(user_ip)
    if not loc:
        return "无法定位您的位置"

    # 第二步：获取天气
    weather = get_weather_by_coords(loc['lon_lat'])
    
    if weather:
        return (f"您当前处于：{loc['province']} {loc['city']}<br>"
                f"🌤️ 天气状况：{weather['text']}<br>"
                f"🌡️ 实时气温：{weather['temp']}℃<br>"
                f"🌬️ 风向：{weather['windDir']}<br>"
                f"🤗 体感温度：{weather['feelsLike']}℃<br>"
                f"💧 空气湿度：{weather['humidity']}%<br>"
                f"<br>"
                f"(当前信息获取于 {weather['obsTime']})")
    else:
        return f"您在 {loc['city']}，但天气数据获取失败。"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
