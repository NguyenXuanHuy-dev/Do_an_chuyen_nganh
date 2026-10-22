import re
from typing import Dict, List, Optional
from config import Config

class ChatAgentService:
    @classmethod
    def answer_question(
        cls, 
        question: str, 
        session_info: Dict, 
        feedback_items: List[Dict],
        prompt_template: Optional[str] = None
    ) -> str:
        """
        Answers natural language questions about customer feedback session.
        Combines deterministic NLP analytics with structured business insights.
        """
        q_lower = (question or "").lower().strip()
        
        # Calculate key metrics
        total = session_info.get('cleaned_count') or len(feedback_items) or 1
        pos_cnt = session_info.get('positive_count', 0)
        neg_cnt = session_info.get('negative_count', 0)
        neu_cnt = session_info.get('neutral_count', 0)
        
        pos_pct = round((pos_cnt / total) * 100, 1)
        neg_pct = round((neg_cnt / total) * 100, 1)
        neu_pct = round((neu_cnt / total) * 100, 1)
        
        # Aggregate aspect breakdown
        aspects = {}
        for item in feedback_items:
            asp = item.get('aspect', 'Khác')
            sent = item.get('sentiment', 'Trung tính')
            if asp not in aspects:
                aspects[asp] = {'Tích cực': 0, 'Tiêu cực': 0, 'Trung tính': 0, 'total': 0, 'samples_neg': [], 'samples_pos': []}
            aspects[asp][sent] += 1
            aspects[asp]['total'] += 1
            if sent == 'Tiêu cực' and len(aspects[asp]['samples_neg']) < 3:
                aspects[asp]['samples_neg'].append(item.get('original_text', ''))
            elif sent == 'Tích cực' and len(aspects[asp]['samples_pos']) < 3:
                aspects[asp]['samples_pos'].append(item.get('original_text', ''))

        # Sort aspects by negative count
        sorted_aspects_neg = sorted(aspects.items(), key=lambda x: x[1]['Tiêu cực'], reverse=True)
        # Sort aspects by positive count
        sorted_aspects_pos = sorted(aspects.items(), key=lambda x: x[1]['Tích cực'], reverse=True)

        # 1. Câu hỏi về tỷ lệ / tổng quan
        if any(k in q_lower for k in ['tỷ lệ', 'bao nhiêu %', 'phần trăm', 'tổng quan', 'thống kê', 'số lượng']):
            return (
                f"### 📊 Tổng quan phân bổ cảm xúc phiên phân tích:\n\n"
                f"- **Tổng số phản hồi:** {total} lượt đánh giá\n"
                f"- **Tích cực (Positive):** **{pos_cnt}** phản hồi ({pos_pct}%)\n"
                f"- **Tiêu cực (Negative):** **{neg_cnt}** phản hồi ({neg_pct}%)\n"
                f"- **Trung tính (Neutral):** **{neu_cnt}** phản hồi ({neu_pct}%)\n"
                f"- **Độ tin cậy trung bình:** {session_info.get('avg_confidence', 0)}%\n\n"
                f"💡 **Nhận xét nhanh:** "
                + ("Đa số khách hàng có phản hồi tích cực và hài lòng với sản phẩm/dịch vụ." if pos_pct >= 50 else
                   "Tỷ lệ phản hồi tiêu cực đang ở mức đáng báo động, cần rà soát khẩn cấp các khâu vận hành." if neg_pct > 35 else
                   "Khách hàng có tâm lý phân vân hoặc kỳ vọng chưa được đáp ứng trọn vẹn, cần thêm các khảo sát chuyên sâu.")
            )

        # 2. Câu hỏi về điểm nghẽn / phàn nàn / chê / tiêu cực
        elif any(k in q_lower for k in ['chê', 'phàn nàn', 'tiêu cực', 'tệ', 'kém', 'điểm nghẽn', 'pain point', 'bực', 'lỗi']):
            top_neg_aspect = sorted_aspects_neg[0] if sorted_aspects_neg and sorted_aspects_neg[0][1]['Tiêu cực'] > 0 else None
            
            resp = f"### ⚠️ Các điểm nghẽn và phàn nàn nổi cộm của khách hàng:\n\n"
            if top_neg_aspect:
                asp_name, asp_data = top_neg_aspect
                resp += f"1. **Khía cạnh bị phàn nàn nhiều nhất là `{asp_name}`** với **{asp_data['Tiêu cực']} lượt đánh giá tiêu cực** (chiếm {round((asp_data['Tiêu cực']/max(1, neg_cnt))*100, 1)}% tổng số phản hồi tiêu cực).\n"
                if asp_data['samples_neg']:
                    resp += f"   - *Trích dẫn thực tế:* \"{asp_data['samples_neg'][0]}\"\n\n"
            
            # Liệt kê các khía cạnh tiêu cực tiếp theo
            resp += "2. **Chi tiết các khía cạnh cần khắc phục:**\n"
            for asp_name, asp_data in sorted_aspects_neg[:3]:
                if asp_data['Tiêu cực'] > 0:
                    resp += f"   - **{asp_name}:** {asp_data['Tiêu cực']} phàn nàn. *Ví dụ:* \"{asp_data['samples_neg'][0] if asp_data['samples_neg'] else 'Nhiều phản ánh thất vọng'}\"\n"
            
            resp += (
                f"\n🎯 **Hành động đề xuất ngay:**\n"
                f"- Liên hệ xin lỗi và giải quyết bồi thường/đổi trả cho các khách hàng để lại phản hồi bức xúc.\n"
                f"- Họp nội bộ với bộ phận phụ trách `{top_neg_aspect[0] if top_neg_aspect else 'Vận hành'}` để rà soát quy trình trong 48h tới."
            )
            return resp

        # 3. Câu hỏi về điểm mạnh / khen / tích cực
        elif any(k in q_lower for k in ['khen', 'điểm mạnh', 'tích cực', 'thích', 'tốt nhất', 'ưu điểm']):
            top_pos_aspect = sorted_aspects_pos[0] if sorted_aspects_pos and sorted_aspects_pos[0][1]['Tích cực'] > 0 else None
            resp = f"### 🌟 Điểm mạnh nổi bật được khách hàng khen ngợi:\n\n"
            if top_pos_aspect:
                asp_name, asp_data = top_pos_aspect
                resp += f"- **Khía cạnh được yêu thích nhất:** `{asp_name}` với **{asp_data['Tích cực']} phản hồi tích cực**.\n"
                if asp_data['samples_pos']:
                    resp += f"- *Đánh giá tiêu biểu:* \"{asp_data['samples_pos'][0]}\"\n\n"
            
            resp += "**Phân bổ khen ngợi theo các khía cạnh:**\n"
            for asp_name, asp_data in sorted_aspects_pos[:3]:
                if asp_data['Tích cực'] > 0:
                    resp += f"- **{asp_name}:** {asp_data['Tích cực']} lượt đánh giá 5 sao/tích cực.\n"

            resp += "\n✨ **Khuyến nghị phát huy:** Tiếp tục duy trì chuẩn chất lượng này và dùng các phản hồi tích cực làm tư liệu truyền thông/Marketing."
            return resp

        # 4. Câu hỏi về một khía cạnh cụ thể (Giao hàng, Giá cả, Dịch vụ, Chất lượng, Bao bì)
        for asp_key in ['giao hàng', 'vận chuyển', 'ship']:
            if asp_key in q_lower:
                data = aspects.get('Giao hàng', {'Tích cực': 0, 'Tiêu cực': 0, 'total': 0, 'samples_neg': [], 'samples_pos': []})
                return (
                    f"### 🚚 Đánh giá về khía cạnh Giao hàng / Vận chuyển:\n\n"
                    f"- Tổng số lượt nhắc đến: **{data['total']}** phản hồi\n"
                    f"- Khen (Giao nhanh, đúng hẹn): **{data['Tích cực']}**\n"
                    f"- Chê (Giao chậm, thái độ shipper, trễ): **{data['Tiêu cực']}**\n\n"
                    f"📌 **Trích dẫn minh họa:**\n"
                    + (f"- Tiêu cực: \"{data['samples_neg'][0]}\"\n" if data['samples_neg'] else "")
                    + (f"- Tích cực: \"{data['samples_pos'][0]}\"\n" if data['samples_pos'] else "")
                )

        for asp_key in ['giá', 'tiền', 'đắt', 'rẻ']:
            if asp_key in q_lower:
                data = aspects.get('Giá cả', {'Tích cực': 0, 'Tiêu cực': 0, 'total': 0, 'samples_neg': [], 'samples_pos': []})
                return (
                    f"### 💰 Đánh giá về khía cạnh Giá cả & Khuyến mãi:\n\n"
                    f"- Tổng số lượt nhắc đến: **{data['total']}** phản hồi\n"
                    f"- Đánh giá hợp lý/rẻ/đáng tiền: **{data['Tích cực']}**\n"
                    f"- Đánh giá đắt/phí tiền: **{data['Tiêu cực']}**\n"
                )

        # 5. Câu hỏi về đề xuất cải thiện / hành động (Action plan)
        if any(k in q_lower for k in ['đề xuất', 'hành động', 'cải thiện', 'giải pháp', 'làm gì', 'khắc phục']):
            return (
                f"### 🚀 Đề xuất kế hoạch hành động cải thiện chất lượng:\n\n"
                f"1. **Xử lý nhanh khâu `{sorted_aspects_neg[0][0] if sorted_aspects_neg else 'CSKH'}`:** "
                f"Tập trung đào tạo lại quy trình và giảm thiểu các phản ánh tiêu cực hiện hữu.\n"
                f"2. **Chính sách chăm sóc khách hàng chủ động:** "
                f"Gửi mã ưu đãi xin lỗi các đơn hàng giao trễ hoặc sản phẩm lỗi phát sinh.\n"
                f"3. **Đồng bộ thông tin sản phẩm:** "
                f"Cập nhật lại mô tả kích thước và hình ảnh chân thực để tránh khách hàng hụt hẫng sau khi nhận hàng.\n"
                f"4. **Kiểm soát chất lượng đầu ra:** "
                f"Thực hiện kiểm tra kép (Double check) khâu đóng gói chống sốc trước khi bàn giao cho đơn vị vận chuyển."
            )

        # Fallback tổng hợp thông minh
        return (
            f"Dựa trên dữ liệu **{total} phản hồi** của phiên này:\n\n"
            f"- **Tỷ lệ cảm xúc:** {pos_pct}% Tích cực | {neg_pct}% Tiêu cực | {neu_pct}% Trung tính.\n"
            f"- **Khía cạnh nổi bật nhất:** `{sorted_aspects_pos[0][0] if sorted_aspects_pos else 'Sản phẩm'}` (Tích cực: {sorted_aspects_pos[0][1]['Tích cực'] if sorted_aspects_pos else 0}).\n"
            f"- **Khía cạnh cần chú ý nhất:** `{sorted_aspects_neg[0][0] if sorted_aspects_neg else 'Khác'}` (Tiêu cực: {sorted_aspects_neg[0][1]['Tiêu cực'] if sorted_aspects_neg else 0}).\n\n"
            f"Bạn có thể bấm vào các câu hỏi gợi ý bên dưới hoặc hỏi cụ thể về *khía cạnh giao hàng*, *chất lượng*, *giá cả*, hoặc *đề xuất khắc phục*!"
        )
