import re
from typing import Dict, List, Tuple

class PreprocessService:
    # Extensive Vietnamese teencode & acronym dictionary
    TEENCODE_DICT: Dict[str, str] = {
        # Phủ định & cơ bản
        "ko": "không",
        "k": "không",
        "kh": "không",
        "khum": "không",
        "hok": "không",
        "hông": "không",
        "hong": "không",
        "hem": "không",
        "hổng": "không",
        "chả": "không",
        "dc": "được",
        "đc": "được",
        "dk": "được",
        "đk": "được",
        "ntn": "như thế nào",
        "sao": "sao",
        
        # Sản phẩm & thương mại
        "sp": "sản phẩm",
        "san pham": "sản phẩm",
        "sz": "kích cỡ",
        "size": "kích cỡ",
        "form": "kiểu dáng",
        "cl": "chất liệu",
        "chat lieu": "chất liệu",
        "hang": "hàng",
        "order": "đặt hàng",
        "ship": "giao hàng",
        "shipper": "người giao hàng",
        "shiper": "người giao hàng",
        "shop": "cửa hàng",
        "shopp": "cửa hàng",
        "sop": "cửa hàng",
        "sale": "giảm giá",
        "km": "khuyến mãi",
        "voucher": "mã giảm giá",
        "ma giam": "mã giảm giá",
        "bill": "hóa đơn",
        "auth": "chính hãng",
        "fake": "hàng giả",
        "rep 1:1": "hàng nhái",
        
        # Giao tiếp & dịch vụ
        "ib": "nhắn tin",
        "inbox": "nhắn tin",
        "rep": "trả lời",
        "tl": "trả lời",
        "tks": "cảm ơn",
        "thks": "cảm ơn",
        "thanks": "cảm ơn",
        "ty": "cảm ơn",
        "cam on": "cảm ơn",
        "cảm ơn": "cảm ơn",
        "nv": "nhân viên",
        "nvien": "nhân viên",
        "cskh": "chăm sóc khách hàng",
        "dt": "điện thoại",
        "đt": "điện thoại",
        "sdt": "số điện thoại",
        "sđt": "số điện thoại",
        "fb": "mạng xã hội",
        
        # Đại từ & từ xưng hô
        "m": "mình",
        "mk": "mình",
        "mik": "mình",
        "t": "tôi",
        "toi": "tôi",
        "ad": "quản trị viên",
        "mn": "mọi người",
        "mng": "mọi người",
        "ng": "người",
        "b": "bạn",
        "bn": "bạn",
        "e": "em",
        "a": "anh",
        "c": "chị",
        
        # Trạng từ & Tính từ
        "dth": "dễ thương",
        "cute": "dễ thương",
        "bth": "bình thường",
        "bt": "bình thường",
        "thk": "thích",
        "iu": "yêu",
        "cx": "cũng",
        "cung": "cũng",
        "vs": "với",
        "voi": "với",
        "lun": "luôn",
        "luon": "luôn",
        "r": "rồi",
        "roi": "rồi",
        "roii": "rồi",
        "wa": "quá",
        "qua": "quá",
        "qúa": "quá",
        "nhah": "nhanh",
        "nhah chóng": "nhanh chóng",
        "chậm": "chậm",
        "cham": "chậm",
        "oke": "tốt",
        "ok": "tốt",
        "okie": "tốt",
        "okela": "rất tốt",
        "okey": "tốt",
        "đỉnh": "rất tốt",
        "dinh": "rất tốt",
        "xịn": "rất tốt",
        "xin": "rất tốt",
        "xin xo": "chất lượng cao",
        "xịn xò": "chất lượng cao",
        "dỏm": "kém chất lượng",
        "dom": "kém chất lượng",
        "lởm": "kém chất lượng",
        "phèn": "chất lượng kém",
        "cùi": "chất lượng kém",
        "cùi bắp": "chất lượng kém",
        "tệ": "tệ",
        "te": "tệ",
        "bực": "bực mình",
        "ức chế": "rất bực mình",
        "đáng tiền": "rất xứng đáng",
        "phí tiền": "rất lãng phí",
        "phí thoi gian": "lãng phí thời gian",
        "như hạch": "rất tệ",
        "vãi": "rất",
        "kinh": "rất",
        "toẹt vời": "tuyệt vời",
        "tuyet voi": "tuyệt vời",
        "đẹp": "rất đẹp",
        "dep": "đẹp",
        "xấu": "xấu",
        "xau": "xấu",
        
        # Cụm từ không dấu phổ biến trong đánh giá mỹ phẩm & mua sắm
        "sieu thich": "siêu thích",
        "thich": "thích",
        "rat thich": "rất thích",
        "rat tot": "rất tốt",
        "tot": "tốt",
        "can than": "cẩn thận",
        "dong goi": "đóng gói",
        "hai long": "hài lòng",
        "mat ruoi": "mát rượi",
        "tham thau": "thẩm thấu",
        "cang bong": "căng bóng",
        "min mang": "mịn màng",
        "mo tham": "mờ thâm",
        "kho moi": "khô môi",
        "von cuc": "vón cục",
        "nut vo": "nứt vỡ",
        "ngua rat": "ngứa rát",
        "noi mun": "nổi mụn",
        "that vong": "thất vọng",
        "giao hang cham": "giao hàng chậm",
        "tho o": "thờ ơ",
        "kiem dau": "kiềm dầu",
        "trang da": "trắng da",
        "chinh hang": "chính hãng",
        "san sale": "săn sale",
        "doi hang": "đổi hàng",
        "hoan tien": "hoàn tiền",
        "tam on": "tạm ổn",
        "tam dc": "tạm được",
        "5 sao": "năm sao xuất sắc"
    }

    # Emoji mapping to descriptive sentiment text
    EMOJI_SENTIMENT_MAP: Dict[str, Tuple[str, str]] = {
        # Emoji: (replacement_text, sentiment_category)
        "❤️": (" rất yêu thích ", "Tích cực"),
        "💖": (" vô cùng thích ", "Tích cực"),
        "💕": (" rất yêu thích ", "Tích cực"),
        "😍": (" cực kỳ mê mẩn hài lòng ", "Tích cực"),
        "🥰": (" rất ưng ý ", "Tích cực"),
        "😘": (" gửi lời cảm ơn ", "Tích cực"),
        "👍": (" đánh giá tốt ", "Tích cực"),
        "👏": (" rất đáng khen ", "Tích cực"),
        "⭐": (" năm sao xuất sắc ", "Tích cực"),
        "🌟": (" chất lượng vượt trội ", "Tích cực"),
        "🔥": (" quá xuất sắc ", "Tích cực"),
        "💯": (" một trăm điểm hoàn hảo ", "Tích cực"),
        "🎉": (" rất vui và hài lòng ", "Tích cực"),
        "😊": (" nụ cười hài lòng ", "Tích cực"),
        "😁": (" rất vui tươi ", "Tích cực"),
        "😃": (" rất hào hứng ", "Tích cực"),
        "👌": (" rất chuẩn chỉ ", "Tích cực"),
        
        "😡": (" cực kỳ phẫn nộ tức giận ", "Tiêu cực"),
        "🤬": (" vô cùng bức xúc chửi bới ", "Tiêu cực"),
        "👿": (" rất phẫn uất ", "Tiêu cực"),
        "😤": (" bực bội khó chịu ", "Tiêu cực"),
        "👎": (" đánh giá rất tệ ", "Tiêu cực"),
        "😭": (" quá thất vọng khóc ròng ", "Tiêu cực"),
        "😢": (" rất buồn và thất vọng ", "Tiêu cực"),
        "💔": (" thất vọng tràn trề ", "Tiêu cực"),
        "💩": (" chất lượng như rác ", "Tiêu cực"),
        "🤮": (" kinh tởm muốn nôn ", "Tiêu cực"),
        "🤢": (" ghê tởm khó chịu ", "Tiêu cực"),
        "😒": (" chán nản ngao ngán ", "Tiêu cực"),
        "🙄": (" coi thường khó chịu ", "Tiêu cực"),
        "😠": (" khó chịu bực mình ", "Tiêu cực"),
        
        "😐": (" bình thường không có gì đặc sắc ", "Trung tính"),
        "😑": (" tạm chấp nhận được ", "Trung tính"),
        "🤔": (" còn băn khoăn suy nghĩ ", "Trung tính"),
        "😶": (" không biết nói gì thêm ", "Trung tính"),
        "🤨": (" nghi ngờ phân vân ", "Trung tính")
    }

    @classmethod
    def clean_text(cls, text: str) -> str:
        """
        Cleans text: converts emojis, normalizes teencode, fixes spaces & punctuation.
        """
        if not text or not isinstance(text, str):
            return ""

        cleaned = text.strip()

        # 1. Emoji normalization
        for emoji, (replacement, _) in cls.EMOJI_SENTIMENT_MAP.items():
            if emoji in cleaned:
                cleaned = cleaned.replace(emoji, replacement)

        # 2. Lowercase for word matching
        words = re.findall(r'\b\w+\b|[^\w\s]', cleaned.lower(), flags=re.UNICODE)
        
        # 3. Teencode normalization
        normalized_words = []
        for word in words:
            if word in cls.TEENCODE_DICT:
                normalized_words.append(cls.TEENCODE_DICT[word])
            else:
                normalized_words.append(word)

        # 4. Reconstruct and clean up spaces
        reconstructed = " ".join(normalized_words)
        # Fix punctuation spacing
        reconstructed = re.sub(r'\s+([.,!?;:])', r'\1', reconstructed)
        reconstructed = re.sub(r'\s+', ' ', reconstructed).strip()

        return reconstructed

    @classmethod
    def detect_noise_and_errors(cls, raw_list: List[str]) -> Dict:
        """
        Detects blank rows, duplicates, and invalid format lines.
        Returns statistics and cleaned list proposal.
        """
        total = len(raw_list)
        empty_count = 0
        duplicate_count = 0
        valid_items = []
        seen = set()

        for idx, item in enumerate(raw_list):
            if item is None:
                empty_count += 1
                continue
                
            text = str(item).strip()
            if not text or len(text) < 2:
                empty_count += 1
                continue

            # Check if junk string like "..." or "1111"
            if re.match(r'^[.\-_/\\=\s0-9]{1,4}$', text):
                empty_count += 1
                continue

            normalized_key = text.lower()
            if normalized_key in seen:
                duplicate_count += 1
            else:
                seen.add(normalized_key)
                valid_items.append({
                    'original_index': idx + 1,
                    'original_text': text,
                    'cleaned_text': cls.clean_text(text)
                })

        return {
            'total_raw': total,
            'empty_count': empty_count,
            'duplicate_count': duplicate_count,
            'clean_count': len(valid_items),
            'valid_items': valid_items
        }
