from flask import Flask, render_template, request, jsonify
import base64
import io
import json
import requests
from PIL import Image
import google.generativeai as genai
import os
from datetime import datetime

app = Flask(__name__)

# Configure Gemini API
genai.configure(api_key="AIzaSyAR1-TWKKqiVcEP0KBHFIMldKlMM94r0QE")

# Lưu trữ kết quả trong phiên làm việc
results_storage = []

def analyze_cccd_with_gemini(image_bytes):
    """Sử dụng Gemini để phân tích ảnh CCCD và trích xuất thông tin"""
    try:
        # Khởi tạo model
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Prompt chi tiết cho Gemini
        prompt = """
        Hãy phân tích ảnh căn cước công dân Việt Nam và trích xuất thông tin dưới dạng JSON. 
        Chỉ trả về JSON, không thêm bất kỳ văn bản giải thích nào.
        
        Định dạng JSON mong muốn:
        {
            "id": "số căn cước",
            "name": "họ và tên",
            "dob": "ngày tháng năm sinh (dd/mm/yyyy)",
            "sex": "giới tính",
            "nationality": "quốc tịch", 
            "hometown": "quê quán",
            "address": "địa chỉ thường trú",
            "issue_date": "ngày cấp (dd/mm/yyyy)",
            "issue_place": "nơi cấp"
        }
        
        Nếu không tìm thấy thông tin cho một trường, hãy để giá trị là "Không xác định".
        """
        
        # Chuyển đổi ảnh
        image = Image.open(io.BytesIO(image_bytes))
        
        # Gọi Gemini API
        response = model.generate_content([prompt, image])
        
        # Xử lý kết quả - loại bỏ markdown code blocks nếu có
        result_text = response.text.strip()
        if result_text.startswith('```json'):
            result_text = result_text[7:]
        if result_text.endswith('```'):
            result_text = result_text[:-3]
        result_text = result_text.strip()
        
        # Parse JSON
        data = json.loads(result_text)
        return data
        
    except Exception as e:
        return {"error": f"Lỗi khi phân tích ảnh: {str(e)}"}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_image():
    try:
        data = request.get_json()
        image_data = data['image'].split(',')[1]  # Remove data:image/... prefix
        image_bytes = base64.b64decode(image_data)
        
        # Process image with Gemini
        result = analyze_cccd_with_gemini(image_bytes)
        
        # Thêm timestamp và ID duy nhất
        result['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result['result_id'] = len(results_storage) + 1
        
        # Lưu ảnh gốc dưới dạng base64 để hiển thị
        result['image_data'] = data['image']
        
        # Thêm kết quả vào storage
        results_storage.append(result)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/results', methods=['GET'])
def get_all_results():
    """Lấy tất cả kết quả đã xử lý"""
    return jsonify(results_storage)

@app.route('/clear', methods=['POST'])
def clear_results():
    """Xóa tất cả kết quả"""
    global results_storage
    results_storage = []
    return jsonify({"status": "success", "message": "Đã xóa tất cả kết quả"})

@app.route('/copy', methods=['POST'])
def copy_results():
    """Trả về dữ liệu để sao chép (không bao gồm tiêu đề)"""
    try:
        data = request.get_json()
        selected_ids = data.get('selected_ids', [])
        
        # Nếu không có ID nào được chọn, trả về tất cả
        if not selected_ids:
            selected_results = results_storage
        else:
            selected_results = [r for r in results_storage if r['result_id'] in selected_ids]
        
        # Định dạng dữ liệu để sao chép (chỉ nội dung)
        copy_data = []
        for result in selected_results:
            copy_data.append({
                "Số CCCD": result.get('id', 'Không xác định'),
                "Họ và tên": result.get('name', 'Không xác định'),
                "Ngày sinh": result.get('dob', 'Không xác định'),
                "Giới tính": result.get('sex', 'Không xác định'),
                "Quốc tịch": result.get('nationality', 'Không xác định'),
                "Quê quán": result.get('hometown', 'Không xác định'),
                "Địa chỉ": result.get('address', 'Không xác định'),
                "Ngày cấp": result.get('issue_date', 'Không xác định'),
                "Nơi cấp": result.get('issue_place', 'Không xác định')
            })
        
        return jsonify({"data": copy_data})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)