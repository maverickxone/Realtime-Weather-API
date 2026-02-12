from flask import Flask, request, render_template, Response
import requests
from openai import OpenAI

app = Flask(__name__)

# --- 配置区 ---
gaode_key = "YOUR-API-KEY"
qweather_key = "YOUR-API-KEY"
API_host = "n75xme78wg.re.qweatherapi.com" # 和风天气API

qwen_client = OpenAI(
    api_key = "YOUR-API-KEY",
    base_url = "https://api.siliconflow.cn"
)

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
    # 第零步：获取IP
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    if user_ip and ',' in user_ip:
        user_ip = user_ip.split(',')[0].strip()
    
    # 第一步：获取位置
    loc = get_location_by_ip(user_ip)
    if not loc:
        return "无法定位您的位置"

    # 第二步：获取天气
    weather = get_weather_by_coords(loc['lon_lat'])
    
    if weather:
        return render_template('weather.html', 
                               province=loc['province'],
                               city=loc['city'],
                               temp=weather['temp'],
                               text=weather['text'],
                               feelsLike=weather['feelsLike'],
                               humidity=weather['humidity'],
                               obsTime=weather['obsTime'])
    else:
        return f"您在 {loc['city']}，但天气数据获取失败。"

@app.route('/weather/ai')
def get_ai_message():
    args = {
        "province": request.args.get('province'),
        "city": request.args.get('city'),
        "text": request.args.get('text'),
        "temp": request.args.get('temp'),
        "feelsLike": request.args.get('feelsLike'),
        "humidity": request.args.get('humidity')
    }
    
    def generate(data):
        province = data.get("province", "未知省份")
        city = data.get("city", "未知城市")
        text = data.get("text", "未知天气")
        temp = data.get("temp", "未知")
        feelsLike = data.get("feelsLike", "未知")
        humidity = data.get("humidity", "未知")
        
        weather_info = f"位置：{province}{city}，天气：{text}，实际气温：{temp}度，体感温度：{feelsLike}度，湿度：{humidity}%"
        try:
            response = qwen_client.chat.completions.create(
                model = "Qwen/Qwen3-8B",
                messages=[
                    {
                        "role": "system", 
                        "content": (
                            "你是一个AI天气助手，请极致模仿《Portal》系列中GlaDOS的口吻。针对提供的天气数据，"
                            "进行刻薄、充满科学优越感且略带威胁的点评，但仍需给测试对象（单数）有用的建议。"
                            "字数控制在150-200字之间。请确保逻辑自然收尾，"
                        )
                    },
                    {"role": "user", "content": weather_info}
                ],
                stream = True,
                # 每生成一个字立刻传输
                temperature = 1.2
            )
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            print(f"Error: {e}")
            yield "检测到严重错误。也许你应该去检查一下你的代码，或者去吃个蛋糕。虽然没有蛋糕（笑）"
    
    return Response(generate(args), mimetype='text/event-stream')
    # 确保流式输出，不会立刻中断连接

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
