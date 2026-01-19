import sys
import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTextEdit, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
                             QLabel, QGroupBox, QSplitter, QMessageBox, QComboBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QTextCursor

class KeyTester(QThread):
    """后台线程，用于检测API Key有效性"""
    result_ready = pyqtSignal(dict)
    
    def __init__(self, api_key, selected_service):
        super().__init__()
        self.api_key = api_key
        self.selected_service = selected_service
        
    def run(self):
        services = {
            "高德webapi": {
                "url": f"https://restapi.amap.com/v3/direction/walking?origin=116.434307,39.90909&destination=116.434446,39.90816&key={self.api_key}"
            },
            "高德jsapi": {
                "url": f"https://restapi.amap.com/v3/geocode/regeo?key={self.api_key}&s=rsv3&location=116.434446,39.90816&callback=jsonp_258885_&platform=JS"
            },
            "高德小程序定位": {
                "url": f"https://restapi.amap.com/v3/geocode/regeo?key={self.api_key}&location=117.19674%2C39.14784&extensions=all&s=rsx&platform=WXJS&appname=c589cf63f592ac13bcab35f8cd18f495&sdkversion=1.2.0&logversion=2.0"
            },
            "百度webapi": {
                "url": f"https://api.map.baidu.com/place/v2/search?query=ATM机&tag=银行&region=北京&output=json&ak={self.api_key}"
            },
            "百度webapiIOS版": {
                "url": f"https://api.map.baidu.com/place/v2/search?query=ATM机&tag=银行&region=北京&output=json&ak={self.api_key}&mcode=com.didapinche.taxi"
            },
            "腾讯webapi": {
                "url": f"https://apis.map.qq.com/ws/place/v1/search?keyword=酒店&boundary=nearby(39.908491,116.374328,1000)&key={self.api_key}"
            }
        }
        
        service = services.get(self.selected_service)
        if service:
            try:
                response = requests.get(service['url'], timeout=10)
                success = self.check_response(response)
                result = {
                    "name": self.selected_service,
                    "success": success,
                    "status_code": response.status_code,
                    "content": response.text
                }
                self.result_ready.emit(result)
            except Exception as e:
                result = {
                    "name": self.selected_service,
                    "success": False,
                    "status_code": 0,
                    "content": f"Error: {str(e)}"
                }
                self.result_ready.emit(result)
    
    def check_response(self, response):
        error_keywords = [
            "key格式错误", "INVALID_KEY", "密钥错误", 
            "authentication error", "invalid key", 
            "AK有误", "key error", "INVALID_REQUEST", 
            "REQUEST_DENIED", "ERROR", "error",
            "密钥无效", "key 错误", "INVALID_USER_KEY",
            'infocode":"10001"', 'status":"0"'
        ]
        if response.status_code != 200:
            return False
        for keyword in error_keywords:
            if keyword in response.text:
                return False
        return True

class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("地图API Key 检测工具")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 顶部控制区域
        top_layout = QHBoxLayout()
        
        # 左侧下拉框选择（测试目标选择）
        service_group = QGroupBox("测试目标")
        service_layout = QVBoxLayout()
        
        self.service_combo = QComboBox()
        self.service_combo.addItems([
            "高德webapi",
            "高德jsapi",
            "高德小程序定位",
            "百度webapi",
            "百度webapiIOS版",
            "腾讯webapi"
        ])
        self.service_combo.setFont(QFont("微软雅黑", 10))
        service_layout.addWidget(self.service_combo)
        service_group.setLayout(service_layout)
        top_layout.addWidget(service_group)
        
        # 右侧输入组
        input_group = QGroupBox("API Key 输入")
        input_layout = QHBoxLayout()
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("请输入API Key...")
        self.key_input.setFont(QFont("微软雅黑", 10))
        
        self.test_btn = QPushButton("开始测试")
        self.test_btn.clicked.connect(self.start_test)
        
        input_layout.addWidget(self.key_input)
        input_layout.addWidget(self.test_btn)
        input_group.setLayout(input_layout)
        top_layout.addWidget(input_group)
        
        main_layout.addLayout(top_layout)
        
        # 结果显示区域
        result_group = QGroupBox("测试结果")
        result_layout = QVBoxLayout()
        
        # 分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 结果列表
        self.result_list = QListWidget()
        splitter.addWidget(self.result_list)
        
        # 响应内容
        self.response_text = QTextEdit()
        self.response_text.setReadOnly(True)
        self.response_text.setFont(QFont("Consolas", 9))
        splitter.addWidget(self.response_text)
        
        splitter.setSizes([300, 500])
        result_layout.addWidget(splitter)
        result_group.setLayout(result_layout)
        main_layout.addWidget(result_group)
        
        # 连接列表点击信号
        self.result_list.itemClicked.connect(self.show_response)
        
        # 存储结果数据
        self.results = []
    
    def start_test(self):
        api_key = self.key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "警告", "请输入API Key！")
            return
        
        selected_service = self.service_combo.currentText()
        if not selected_service:
            QMessageBox.warning(self, "警告", "请选择一个测试目标！")
            return
        
        self.result_list.clear()
        self.response_text.clear()
        self.results.clear()
        
        self.test_btn.setEnabled(False)
        self.test_btn.setText("测试中...")
        
        # 启动测试线程
        self.tester = KeyTester(api_key, selected_service)
        self.tester.result_ready.connect(self.add_result)
        self.tester.finished.connect(self.test_finished)
        self.tester.start()
    
    def add_result(self, result):
        self.results.append(result)
        item = QListWidgetItem(result['name'])
        item.setData(Qt.UserRole, len(self.results)-1)
        
        if result['success']:
            item.setForeground(Qt.green)
            item.setText(f"✓ {result['name']} - 有效")
        else:
            item.setForeground(Qt.red)
            item.setText(f"✗ {result['name']} - 无效")
        
        self.result_list.addItem(item)
    
    def test_finished(self):
        self.test_btn.setEnabled(True)
        self.test_btn.setText("开始测试")
        # 删除完成弹窗，不需要提示用户测试完成
    
    def show_response(self, item):
        index = item.data(Qt.UserRole)
        result = self.results[index]
        self.response_text.setPlainText(f"服务名称: {result['name']}\n状态码: {result['status_code']}\n状态: {'有效' if result['success'] else '无效'}\n\n完整响应:\n{result['content']}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())