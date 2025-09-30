import os
import base64
import io
import json
from PIL import Image
import google.generativeai as genai

# Configure Gemini API
gemini_api_key = os.getenv('GEMINI_API_KEY')
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)

def analyze_cccd_with_gemini(image_base64):
    """Sử dụng Gemini để phân tích ảnh CCCD và trích xuất thông tin"""
    try:
        # Kiểm tra API key
        if not gemini_api_key:
            return {"error": "API key chưa được cấu hình"}
        
        # Thử các model khác nhau
        available_models = [
            'gemini-1.5-pro',
            'gemini-1.0-pro',
            'gemini-pro',
            'models/gemini-1.5-pro-latest',
            'models/gemini-1.0-pro-latest'
        ]
        
        model = None
        for model_name in available_models:
            try:
                model = genai.GenerativeModel(model_name)
                break
            except Exception:
                continue
        
        if model is None:
            return {"error": "Không tìm thấy model nào khả dụng"}
        
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
        Lưu ý: Chỉ trả về JSON, không thêm bất kỳ text nào khác.
        """
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_base64)
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
        
    except json.JSONDecodeError as e:
        return {"error": f"Lỗi phân tích kết quả từ AI: {str(e)}", "raw_response": result_text}
    except Exception as e:
        return {"error": f"Lỗi khi phân tích ảnh: {str(e)}"}