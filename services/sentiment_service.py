import re
import json
import requests
from typing import Dict, List, Tuple, Optional
from services.preprocess_service import PreprocessService
from database.connection import db_session
from models.config import SystemSetting

class SentimentService:
    # Vietnamese Sentiment Lexicon (Fallback & Lexicon Base)
    POSITIVE_WORDS = {
        "tuyệt vời": 2.5, "xuất sắc": 2.5, "rất tốt": 2.2, "tốt": 1.5, "ưng ý": 2.0, "hài lòng": 2.0,
        "đẹp": 1.5, "cực đẹp": 2.3, "chuẩn": 1.4, "chất lượng": 1.5, "chất lượng cao": 2.2, "xịn": 1.8,
        "xịn xò": 2.2, "đáng tiền": 2.0, "rẻ": 1.3, "hợp lý": 1.3, "nhanh": 1.4, "nhanh chóng": 1.7,
        "hỏa tốc": 1.8, "nhiệt tình": 1.8, "chu đáo": 1.8, "dễ thương": 1.5, "thân thiện": 1.5,
        "chuyên nghiệp": 2.0, "cẩn thận": 1.5, "chắc chắn": 1.4, "đầy đủ": 1.2, "yêu thích": 2.0,
        "thích": 1.4, "mê": 1.6, "đỉnh": 2.0, "hoàn hảo": 2.5, "tặng quà": 1.2, "ủng hộ": 1.5,
        "tiện lợi": 1.5, "chính hãng": 1.8, "uy tín": 2.0, "đúng mô tả": 1.8, "dễ dùng": 1.4,
        "bền": 1.6, "thơm": 1.3, "mềm mại": 1.3, "gọn gàng": 1.3, "sạch sẽ": 1.4, "đáng mua": 2.0
    }

    NEGATIVE_WORDS = {
        "tệ": -2.0, "rất tệ": -2.5, "tệ hại": -2.8, "thất vọng": -2.3, "kém": -1.8, "kém chất lượng": -2.4,
        "dở": -1.8, "xấu": -1.5, "cực xấu": -2.2, "chậm": -1.4, "chậm trễ": -1.8, "lâu": -1.3,
        "chờ lâu": -1.7, "đắt": -1.4, "chát": -1.4, "phí tiền": -2.4, "phí thời gian": -2.0,
        "thô lỗ": -2.2, "thái độ kém": -2.5, "cộc cằn": -2.2, "thờ ơ": -1.8, "không trả lời": -1.8,
        "hỏng": -2.0, "hư": -1.8, "lỗi": -1.8, "vỡ": -2.2, "móp": -1.5, "móp méo": -1.8,
        "rách": -1.8, "bẩn": -1.6, "giả": -2.5, "hàng nhái": -2.5, "lừa đảo": -3.0, "treo đầu dê": -2.8,
        "không đúng mô tả": -2.2, "khác hình": -1.8, "sai mẫu": -2.0, "thiếu": -1.6, "thiếu hàng": -2.0,
        "bực mình": -2.2, "ức chế": -2.5, "tức giận": -2.5, "cạch mặt": -2.5, "không mua lại": -2.2,
        "phí": -1.3, "dỏm": -2.0, "lởm": -2.0, "phèn": -1.6, "chán": -1.5, "rác": -2.8,
        "ngu": -2.8, "ngu ngốc": -2.8, "dốt": -2.5, "ngáo": -2.2, "khốn nạn": -3.0, "mất dạy": -3.0,
        "vô văn hóa": -2.8, "vô duyên": -2.2, "hãm": -2.5, "hãm tài": -2.5, "bẩn bựa": -2.5,
        "cẩu thả": -2.0, "quỵt": -2.8, "lừa": -2.5, "bịp": -2.5, "cay": -2.0, "cay cú": -2.2
    }

    NEGATION_WORDS = {
        "không", "chẳng", "chả", "chưa", "k", "ko", "khum", "không phải", "đâu có", "hổng", "hem"
    }

    INTENSIFIERS = {
        "rất": 1.4, "cực kỳ": 1.6, "vô cùng": 1.7, "quá": 1.3, "siêu": 1.5, "hết sảy": 1.6,
        "tuyệt đối": 1.5, "thật sự": 1.3, "quá đỗi": 1.4, "ghê": 1.2, "lắm": 1.3
    }

    ASPECT_KEYWORDS = {
        "Chất lượng": [
            "chất kem", "kem", "thấm nhanh", "mịn da", "ẩm mượt", "sáng da", "nâng tone", "son lì",
            "mềm môi", "thơm dịu", "kiềm dầu", "kích ứng", "dị ứng", "ngứa", "nổi mụn", "châm chích",
            "bết rít", "bóng dầu", "nồng hắc", "hàng fake", "kem trộn", "bí da", "nặng mặt", "chất lượng",
            "chất liệu", "vải", "xịn", "bền", "hỏng", "hư", "lỗi", "đẹp", "xấu", "dỏm", "lởm", "phèn",
            "đúng mô tả", "khác hình", "chính hãng", "nhái", "giả", "bền bỉ"
        ],
        "Giá cả": [
            "giá", "tiền", "săn sale", "sale", "khuyến mãi", "phí", "voucher", "mã giảm", "đáng tiền",
            "phí tiền", "chát", "bình dân", "giá cả", "hạt dẻ", "vừa túi tiền", "quà tặng", "hời"
        ],
        "Dịch vụ": [
            "thái độ", "tư vấn", "nhiệt tình", "trả lời", "rep", "nhắn tin", "chăm sóc", "cskh",
            "hỗ trợ", "thờ ơ", "khó chịu", "thân thiện", "dễ thương", "thô lỗ", "cộc cằn", "chu đáo",
            "đổi hàng", "bảo hành", "không thèm rep"
        ],
        "Giao hàng": [
            "giao hàng", "ship", "vận chuyển", "người giao", "shipper", "nhanh", "chậm", "lâu", "trễ",
            "hỏa tốc", "đúng hẹn", "chậm trễ", "giao trễ", "chờ mòn mỏi", "chậm như rùa", "gắt gỏng"
        ],
        "Bao bì": [
            "đóng gói", "bao bì", "hộp", "móp méo", "móp", "bọc", "chống sốc", "rách hộp",
            "nắp", "vỡ nắp", "nứt", "tràn", "tràn kem", "vỏ nhám", "sang xịn", "thiết kế",
            "cẩn thận", "kỹ càng", "bảo quản", "bìa"
        ]
    }

    # PROMPT TEMPLATES THEO TỪNG CẢM XÚC / MỤC ĐÍCH PHÂN TÍCH
    PROMPT_TEMPLATES = {
        "general": """Bạn là chuyên gia phân tích cảm xúc khách hàng (Customer Sentiment & Aspect Analysis) chuyên sâu về tiếng Việt và thị trường thương mại điện tử.
Hãy phân tích đoạn bình luận của khách hàng sau đây theo các tiêu chí:
1. "sentiment": Chọn chính xác 1 trong 3 nhãn: "Tích cực", "Tiêu cực", "Trung tính".
2. "score": Thang điểm số từ -5.0 (cực kỳ bức xúc, thất vọng) đến +5.0 (cực kỳ hài lòng, xuất sắc). 0.0 là trung tính.
3. "emotion_detail": Nêu rõ sắc thái cảm xúc chi tiết (Ví dụ: "Hài lòng và biết ơn", "Bực mình vì giao trễ", "Tức giận vì hàng lỗi", "Phân vân đắn đo",...).
4. "aspect": Chọn khía cạnh nổi bật nhất trong: ["Chất lượng", "Giá cả", "Dịch vụ", "Giao hàng", "Bao bì", "Khác"].
5. "confidence": Độ tin cậy của bạn từ 0.0 đến 1.0 (ví dụ: 0.95).
6. "positive_words": Danh sách các từ ngữ hoặc cụm từ mang ý khen ngợi, tích cực.
7. "negative_words": Danh sách các từ ngữ chê bai, tiêu cực, teencode xúc phạm hoặc phàn nàn.
8. "reasoning": Giải thích ngắn gọn 1-2 câu vì sao bạn đánh giá như vậy.

Đoạn văn bản của khách hàng:
\"\"\"{text}\"\"\"

Trả về DUY NHẤT một chuỗi JSON hợp lệ không kèm văn bản thừa:
{
  "sentiment": "Tích cực" | "Tiêu cực" | "Trung tính",
  "score": float,
  "emotion_detail": "...",
  "aspect": "...",
  "confidence": float,
  "positive_words": [...],
  "negative_words": [...],
  "reasoning": "..."
}""",

        "negative_focus": """Bạn là trợ lý AI chuyên bóc tách các điểm nghẽn (Pain points) và khủng hoảng khách hàng.
Hãy tập trung phân tích sâu vào các cảm xúc TIÊU CỰC, lời phàn nàn, sự thất vọng hoặc ngôn từ bức xúc trong đoạn văn bản sau:
1. "sentiment": "Tiêu cực", "Trung tính" hoặc "Tích cực".
2. "score": Điểm số (-5.0 đến +5.0).
3. "emotion_detail": Bóc tách rõ mức độ bức xúc (ví dụ: "Phẫn nộ vì hàng giả", "Thất vọng về thái độ nhân viên",...).
4. "aspect": Khâu nào đang gặp sự cố lớn nhất: ["Chất lượng", "Giá cả", "Dịch vụ", "Giao hàng", "Bao bì", "Khác"].
5. "confidence": Độ tin cậy (0.0 đến 1.0).
6. "positive_words": Từ khen (nếu có).
7. "negative_words": Toàn bộ các từ ngữ chê trách, khiếu nại, ngôn từ gay gắt.
8. "reasoning": Phân tích nguyên nhân gốc rễ (Root Cause) khiến khách hàng không hài lòng.

Đoạn văn bản:
\"\"\"{text}\"\"\"

Trả về JSON:
{
  "sentiment": "Tiêu cực" | "Trung tính" | "Tích cực",
  "score": float,
  "emotion_detail": "...",
  "aspect": "...",
  "confidence": float,
  "positive_words": [...],
  "negative_words": [...],
  "reasoning": "..."
}""",

        "positive_focus": """Bạn là chuyên gia khai thác sự thỏa mãn của khách hàng và định vị thương hiệu.
Hãy tập trung nhận diện các cảm xúc TÍCH CỰC, lời khen ngợi, sự gắn kết thương hiệu trong đoạn văn bản sau:
1. "sentiment": "Tích cực", "Trung tính" hoặc "Tiêu cực".
2. "score": Điểm số (-5.0 đến +5.0).
3. "emotion_detail": Sắc thái yêu mến (ví dụ: "Rất mê sản phẩm", "Cảm kích vì shipper chu đáo",...).
4. "aspect": Lợi thế cạnh tranh vượt trội thuộc về: ["Chất lượng", "Giá cả", "Dịch vụ", "Giao hàng", "Bao bì", "Khác"].
5. "confidence": Độ tin cậy (0.0 đến 1.0).
6. "positive_words": Toàn bộ lời khen và biểu cảm tốt.
7. "negative_words": Lời chê (nếu có).
8. "reasoning": Điều gì tạo nên trải nghiệm WOW cho khách hàng.

Đoạn văn bản:
\"\"\"{text}\"\"\"

Trả về JSON:
{
  "sentiment": "Tích cực" | "Trung tính" | "Tiêu cực",
  "score": float,
  "emotion_detail": "...",
  "aspect": "...",
  "confidence": float,
  "positive_words": [...],
  "negative_words": [...],
  "reasoning": "..."
}"""
    }

    @classmethod
    def get_configured_api_key(cls) -> str:
        """
        Retrieves Gemini API Key from database SystemSetting or config.
        """
        from config import Config
        setting = db_session.query(SystemSetting).filter(SystemSetting.setting_key == 'gemini_api_key').first()
        if setting and setting.setting_value.strip():
            return setting.setting_value.strip()
        return Config.GEMINI_API_KEY.strip()

    @classmethod
    def set_configured_api_key(cls, api_key: str) -> bool:
        """
        Saves user-provided Gemini API Key into database SystemSetting.
        """
        setting = db_session.query(SystemSetting).filter(SystemSetting.setting_key == 'gemini_api_key').first()
        if not setting:
            setting = SystemSetting(
                setting_key='gemini_api_key',
                setting_value=api_key.strip(),
                description='Google Gemini API Key for LLM sentiment analysis'
            )
            db_session.add(setting)
        else:
            setting.setting_value = api_key.strip()
        db_session.commit()
        return True

    @classmethod
    def analyze_with_llm(
        cls, 
        text: str, 
        api_key: Optional[str] = None, 
        prompt_mode: str = 'general', 
        model_name: str = 'gemini-3.8-flash',
        custom_prompt: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Calls Google Gemini API with tailored Prompt to analyze customer sentiment.
        """
        key = (api_key or cls.get_configured_api_key()).strip()
        if not key:
            return None

        # Build Prompt
        if custom_prompt and "{text}" in custom_prompt:
            prompt_content = custom_prompt.replace("{text}", text)
        else:
            template = cls.PROMPT_TEMPLATES.get(prompt_mode, cls.PROMPT_TEMPLATES['general'])
            prompt_content = template.replace("{text}", text)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": prompt_content}]
            }],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
                "thinkingConfig": {"thinkingBudget": 0}
            }
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts:
                        raw_json_str = parts[0].get('text', '').strip()
                        # Clean markdown code blocks if any
                        if raw_json_str.startswith('```json'):
                            raw_json_str = raw_json_str[7:]
                        if raw_json_str.endswith('```'):
                            raw_json_str = raw_json_str[:-3]
                        
                        parsed = json.loads(raw_json_str.strip())
                        
                        score = float(parsed.get('score', 0.0))
                        sentiment = parsed.get('sentiment', 'Trung tính')
                        confidence = float(parsed.get('confidence', 0.9))
                        aspect = parsed.get('aspect', 'Khác')
                        pos_words = parsed.get('positive_words', [])
                        neg_words = parsed.get('negative_words', [])
                        reasoning = parsed.get('reasoning', '')
                        action_suggestion = parsed.get('action_suggestion', '')
                        emotion_detail = parsed.get('emotion_detail', '')

                        # Spectrum percentage (-5.0 to +5.0 mapped to 0% - 100%)
                        spectrum_pct = round(max(5.0, min(95.0, 50.0 + (score / 5.0) * 45.0)), 1)
                        
                        words = [w for w in text.split() if w]
                        words_count = len(words)
                        match_count = len(pos_words) + len(neg_words)
                        match_pct = round((match_count / max(1, words_count)) * 100, 1)

                        rating_star = 5 if score >= 2.5 else 4 if score > 0.5 else 3 if score >= -0.5 else 2 if score >= -2.5 else 1

                        return {
                            'engine': 'Gemini LLM AI',
                            'model': model_name,
                            'prompt_mode': prompt_mode,
                            'original_text': text,
                            'cleaned_text': PreprocessService.clean_text(text),
                            'sentiment': sentiment,
                            'confidence': round(confidence, 2),
                            'aspect': aspect,
                            'aspect_sentiment': sentiment,
                            'rating_star': rating_star,
                            'score': round(score, 2),
                            'comparative': round(score / max(1, words_count), 2),
                            'spectrum_pct': spectrum_pct,
                            'words_analyzed': words_count,
                            'lexicon_matches_count': match_count,
                            'lexicon_matches_pct': match_pct,
                            'positive_words': pos_words,
                            'negative_words': neg_words,
                            'emotion_detail': emotion_detail,
                            'reasoning': reasoning,
                            'action_suggestion': action_suggestion,
                            'sentence_breakdown': [{
                                'sentence': text,
                                'score': round(score, 2),
                                'sentiment': sentiment
                            }]
                        }
            else:
                print(f"Gemini API returned error {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"Error calling Gemini API: {e}")

        return None

    @classmethod
    def analyze_single(
        cls, 
        text: str, 
        api_key: Optional[str] = None, 
        prompt_mode: str = 'general',
        custom_prompt: Optional[str] = None
    ) -> Dict:
        """
        Unified analyzer:
        1. If API Key is configured (or passed), calls Gemini LLM with structured prompt.
        2. If API Key is not configured or network error, falls back seamlessly to rule-based engine.
        """
        key = api_key or cls.get_configured_api_key()
        if key:
            llm_result = cls.analyze_with_llm(
                text=text, 
                api_key=key, 
                prompt_mode=prompt_mode, 
                custom_prompt=custom_prompt
            )
            if llm_result:
                return llm_result

        # Fallback to Local Vietnamese NLP Rule-based Engine
        return cls._analyze_local_rule_based(text)

    @classmethod
    def _analyze_local_rule_based(cls, text: str) -> Dict:
        cleaned = PreprocessService.clean_text(text)
        if not cleaned:
            return {
                'engine': 'Rule-Based NLP',
                'original_text': text,
                'cleaned_text': '',
                'sentiment': 'Trung tính',
                'confidence': 0.5,
                'aspect': 'Khác',
                'aspect_sentiment': 'Trung tính',
                'rating_star': 3,
                'score': 0.0,
                'comparative': 0.0,
                'spectrum_pct': 50.0,
                'words_analyzed': 0,
                'lexicon_matches_count': 0,
                'lexicon_matches_pct': 0.0,
                'positive_words': [],
                'negative_words': [],
                'emotion_detail': 'Chưa xác định',
                'reasoning': 'Không có đủ nội dung văn bản để đánh giá.',
                'action_suggestion': 'Yêu cầu khách hàng cung cấp thêm thông tin chi tiết.',
                'sentence_breakdown': []
            }

        eval_res = cls._evaluate_text(cleaned)
        score = eval_res['score']
        pos_words = eval_res['pos_matched']
        neg_words = eval_res['neg_matched']

        words = [w for w in cleaned.split() if w]
        words_count = len(words)
        match_count = len(pos_words) + len(neg_words)
        match_pct = round((match_count / max(1, words_count)) * 100, 1)

        comparative = round(score / max(1, words_count), 2)

        # Detect Aspect
        aspect = "Khác"
        lower_cleaned = cleaned.lower()
        aspect_matches = {k: 0 for k in cls.ASPECT_KEYWORDS}
        for asp, keywords in cls.ASPECT_KEYWORDS.items():
            for kw in keywords:
                if kw in lower_cleaned:
                    aspect_matches[asp] += 1
        best_aspect, count = max(aspect_matches.items(), key=lambda x: x[1])
        if count > 0:
            aspect = best_aspect

        # Spectrum Bar Percentage: 50% = Neutral (score 0), 0% = Very Negative (-4 or less), 100% = Very Positive (+4 or more)
        normalized_shift = (score / 4.0) * 50.0
        spectrum_pct = round(max(5.0, min(95.0, 50.0 + normalized_shift)), 1)

        if score > 0.4:
            sentiment = "Tích cực"
            confidence = min(0.98, 0.65 + min(score * 0.08, 0.32))
            rating_star = 5 if score >= 2.0 else 4
            emotion_detail = "Hài lòng và đánh giá cao"
            reasoning = f"Câu chứa nhiều từ tích cực ({', '.join(pos_words) if pos_words else 'khen ngợi'})."
            action_suggestion = "Gửi lời cảm ơn khách hàng và mời đánh giá 5 sao trên trang mua sắm."
        elif score < -0.4:
            sentiment = "Tiêu cực"
            confidence = min(0.98, 0.65 + min(abs(score) * 0.08, 0.32))
            rating_star = 1 if score <= -2.0 else 2
            emotion_detail = "Bức xúc và thất vọng"
            reasoning = f"Phát hiện các từ ngữ khiếu nại, chê bai hoặc xúc phạm ({', '.join(neg_words) if neg_words else 'chê trách'})."
            action_suggestion = f"Chủ động liên hệ xin lỗi, giải thích thỏa đáng và kiểm tra khâu {aspect}."
        else:
            sentiment = "Trung tính"
            confidence = 0.65 if match_count == 0 else 0.75
            rating_star = 3
            spectrum_pct = 50.0
            emotion_detail = "Bình thường / Tạm ổn"
            reasoning = "Nội dung mang tính trung lập, không có nhiều từ ngữ khen ngợi hay chê bai rõ rệt."
            action_suggestion = "Theo dõi thêm các đơn hàng tiếp theo của khách hàng."

        # Sentence Breakdown
        raw_sentences = re.split(r'[.!?\n]+', text)
        sentences_breakdown = []
        for s in raw_sentences:
            s_clean = s.strip()
            if len(s_clean) >= 2:
                s_eval = cls._evaluate_text(PreprocessService.clean_text(s_clean))
                s_score = round(s_eval['score'], 2)
                s_sent = "Tích cực" if s_score > 0.3 else "Tiêu cực" if s_score < -0.3 else "Trung tính"
                sentences_breakdown.append({
                    'sentence': s_clean,
                    'score': s_score,
                    'sentiment': s_sent
                })

        if not sentences_breakdown:
            sentences_breakdown.append({
                'sentence': text,
                'score': round(score, 2),
                'sentiment': sentiment
            })

        return {
            'engine': 'Bộ Quy Tắc NLP Tiếng Việt (Nội Bộ)',
            'original_text': text,
            'cleaned_text': cleaned,
            'sentiment': sentiment,
            'confidence': round(confidence, 2),
            'aspect': aspect,
            'aspect_sentiment': sentiment,
            'rating_star': rating_star,
            'score': round(score, 2),
            'comparative': comparative,
            'spectrum_pct': spectrum_pct,
            'words_analyzed': words_count,
            'lexicon_matches_count': match_count,
            'lexicon_matches_pct': match_pct,
            'positive_words': pos_words,
            'negative_words': neg_words,
            'emotion_detail': emotion_detail,
            'reasoning': reasoning,
            'action_suggestion': action_suggestion,
            'sentence_breakdown': sentences_breakdown
        }

    @classmethod
    def _evaluate_text(cls, text: str) -> Dict:
        lower_text = text.lower()
        tokens = lower_text.split()
        score = 0.0
        
        pos_matched = []
        neg_matched = []

        # Multi-word phrases match
        for phrase, weight in cls.POSITIVE_WORDS.items():
            if " " in phrase and phrase in lower_text:
                pattern = rf"(không|chẳng|chả|chưa|k|ko)\s+{re.escape(phrase)}"
                if re.search(pattern, lower_text):
                    score -= weight * 1.2
                    neg_matched.append(f"không {phrase}")
                else:
                    score += weight
                    pos_matched.append(phrase)

        for phrase, weight in cls.NEGATIVE_WORDS.items():
            if " " in phrase and phrase in lower_text:
                pattern = rf"(không|chẳng|chả|chưa|k|ko)\s+{re.escape(phrase)}"
                if re.search(pattern, lower_text):
                    score += abs(weight) * 0.8
                    pos_matched.append(f"không {phrase}")
                else:
                    score += weight
                    neg_matched.append(phrase)

        # Single token evaluation
        i = 0
        while i < len(tokens):
            token = tokens[i]
            prev_token = tokens[i - 1] if i > 0 else ""
            prev_prev_token = tokens[i - 2] if i > 1 else ""

            is_negated = (prev_token in cls.NEGATION_WORDS) or (prev_prev_token in cls.NEGATION_WORDS)
            multiplier = cls.INTENSIFIERS.get(prev_token, 1.0)
            if prev_prev_token in cls.INTENSIFIERS:
                multiplier *= cls.INTENSIFIERS[prev_prev_token]

            if token in cls.POSITIVE_WORDS and " " not in token:
                base_w = cls.POSITIVE_WORDS[token]
                if is_negated:
                    score -= (base_w * 1.3)
                    neg_matched.append(f"{prev_token} {token}")
                else:
                    score += (base_w * multiplier)
                    pos_matched.append(token)
            elif token in cls.NEGATIVE_WORDS and " " not in token:
                base_w = cls.NEGATIVE_WORDS[token]
                if is_negated:
                    score += (abs(base_w) * 0.9)
                    pos_matched.append(f"{prev_token} {token}")
                else:
                    score += (base_w * multiplier)
                    neg_matched.append(token)

            i += 1

        return {
            'score': score,
            'pos_matched': list(set(pos_matched)),
            'neg_matched': list(set(neg_matched))
        }

    @classmethod
    def analyze_batch(cls, texts: List[str], api_key: Optional[str] = None) -> Tuple[List[Dict], Dict]:
        results = []
        pos_cnt = 0
        neg_cnt = 0
        neu_cnt = 0
        conf_sum = 0.0

        aspect_stats = {asp: {'Tích cực': 0, 'Tiêu cực': 0, 'Trung tính': 0, 'total': 0} 
                        for asp in list(cls.ASPECT_KEYWORDS.keys()) + ['Khác']}

        for t in texts:
            # High-speed batch processing using optimized Vietnamese NLP engine
            res = cls._analyze_local_rule_based(t)
            results.append(res)
            
            s = res['sentiment']
            if s == 'Tích cực':
                pos_cnt += 1
            elif s == 'Tiêu cực':
                neg_cnt += 1
            else:
                neu_cnt += 1

            conf_sum += res['confidence']

            asp = res['aspect']
            if asp in aspect_stats:
                aspect_stats[asp][s] += 1
                aspect_stats[asp]['total'] += 1

        total = len(results) or 1
        summary = {
            'total': len(results),
            'positive_count': pos_cnt,
            'negative_count': neg_cnt,
            'neutral_count': neu_cnt,
            'positive_pct': round((pos_cnt / total) * 100, 1),
            'negative_pct': round((neg_cnt / total) * 100, 1),
            'neutral_pct': round((neu_cnt / total) * 100, 1),
            'avg_confidence': round(conf_sum / total, 2),
            'aspect_breakdown': aspect_stats
        }

        return results, summary
