from flask import Flask, request, jsonify
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 定义各地图服务的测试配置
services = {
    'amap-webapi': {
        'name': '高德webapi',
        'test_url': lambda key: f'https://restapi.amap.com/v3/direction/walking?origin=116.434307,39.90909&destination=116.434446,39.90816&key={key}'
    },
    'amap-jsapi': {
        'name': '高德jsapi',
        'test_url': lambda key: f'https://restapi.amap.com/v3/geocode/regeo?key={key}&s=rsv3&location=116.434446,39.90816&callback=jsonp_258885_&platform=JS'
    },
    'amap-miniprogram': {
        'name': '高德小程序定位',
        'test_url': lambda key: f'https://restapi.amap.com/v3/geocode/regeo?key={key}&location=117.19674%2C39.14784&extensions=all&s=rsx&platform=WXJS&appname=c589cf63f592ac13bcab35f8cd18f495&sdkversion=1.2.0&logversion=2.0'
    },
    'baidu-webapi': {
        'name': '百度webapi',
        'test_url': lambda key: f'https://api.map.baidu.com/place/v2/search?query=ATM机&tag=银行&region=北京&output=json&ak={key}'
    },
    'baidu-webapi-ios': {
        'name': '百度webapiIOS版',
        'test_url': lambda key: f'https://api.map.baidu.com/place/v2/search?query=ATM机&tag=银行&region=北京&output=json&ak={key}&mcode=com.didapinche.taxi'
    },
    'tencent-webapi': {
        'name': '腾讯webapi',
        'test_url': lambda key: f'https://apis.map.qq.com/ws/place/v1/search?keyword=酒店&boundary=nearby(39.908491,116.374328,1000)&key={key}'
    }
}

@app.route('/test', methods=['POST'])
def test_key():
    data = request.get_json()
    api_key = data.get('key')
    selected_services = data.get('services', [])
    
    if not api_key:
        return jsonify({'error': '缺少 API Key 参数'}), 400
    
    if not selected_services:
        return jsonify({'error': '请至少选择一个测试服务'}), 400
    
    results = []
    
    for service in selected_services:
        if service in services:
            service_config = services[service]
            test_url = service_config['test_url'](api_key)
            
            try:
                response = requests.get(test_url, timeout=10)
                status_code = response.status_code
                content = response.text
                
                success = False
                if status_code == 200:
                    error_keywords = [
                        'key格式错误', 'INVALID_KEY', '密钥错误', 
                        'authentication error', 'invalid key', 
                        'AK有误', 'key error', 'INVALID_REQUEST',
                        'REQUEST_DENIED', 'ERROR', 'error',
                        '密钥无效', 'key 错误', 'INVALID_USER_KEY',
                        'infocode":"10001", 'status":"0"'
                    ]
                    has_error = any(keyword in content for keyword in error_keywords)
                    success = not has_error
                
                results.append({
                    'service': service_config['name'],
                    'status': success,
                    'content': content
                })
            except requests.exceptions.RequestException as e:
                results.append({
                    'service': service_config['name'],
                    'status': False,
                    'content': f'请求异常: {str(e)}'
                })
    
    return jsonify({'results': results})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)