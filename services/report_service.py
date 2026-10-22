from typing import Dict, List
from datetime import datetime

class ReportService:
    @classmethod
    def generate_bod_report(cls, session: Dict, items: List[Dict]) -> str:
        """
        Generates Voice of Customer (VOC) executive summary for Board of Directors.
        """
        total = session.get('cleaned_count') or len(items) or 1
        pos = session.get('positive_count', 0)
        neg = session.get('negative_count', 0)
        neu = session.get('neutral_count', 0)
        
        pos_pct = round((pos / total) * 100, 1)
        neg_pct = round((neg / total) * 100, 1)
        neu_pct = round((neu / total) * 100, 1)
        
        # Net Sentiment Score (NSS = % Positive - % Negative)
        nss = round(pos_pct - neg_pct, 1)
        # Estimated Customer Satisfaction Score (CSAT on 100 scale)
        csat_est = round((pos * 100 + neu * 50) / total, 1)

        # Aspects
        aspect_breakdown = {}
        for it in items:
            asp = it.get('aspect', 'Khác')
            sent = it.get('sentiment', 'Trung tính')
            if asp not in aspect_breakdown:
                aspect_breakdown[asp] = {'pos': 0, 'neg': 0, 'neu': 0, 'total': 0}
            if sent == 'Tích cực': aspect_breakdown[asp]['pos'] += 1
            elif sent == 'Tiêu cực': aspect_breakdown[asp]['neg'] += 1
            else: aspect_breakdown[asp]['neu'] += 1
            aspect_breakdown[asp]['total'] += 1

        top_strength = max(aspect_breakdown.items(), key=lambda x: x[1]['pos'])[0] if aspect_breakdown else "Sản phẩm"
        top_weakness = max(aspect_breakdown.items(), key=lambda x: x[1]['neg'])[0] if aspect_breakdown else "Vận hành"

        report_md = f"""# BÁO CÁO TÓM TẮT CHỈ SỐ VOC (VOICE OF CUSTOMER) DÀNH CHO BAN GIÁM ĐỐC
**Phiên phân tích:** {session.get('title')} | **Ngày lập báo cáo:** {datetime.now().strftime('%d/%m/%Y')}
**Nguồn dữ liệu:** {session.get('file_name') or 'Văn bản trực tiếp'} ({total} ý kiến phản hồi)

---

### 1. CÁC CHỈ SỐ CHIẾN LƯỢC CỐT LÕI (EXECUTIVE KPI DASHBOARD)
- **Net Sentiment Score (NSS):** `{nss:+}%` ({'Tốt - Khách hàng có xu hướng ủng hộ thương hiệu' if nss >= 30 else 'Cần cải thiện - Tỷ lệ chỉ trích cao' if nss < 0 else 'Trung bình'})
- **Chỉ số thỏa mãn ước tính (CSAT Score):** `{csat_est}/100`
- **Tỷ lệ cảm xúc tích cực:** `{pos_pct}%` ({pos} phản hồi)
- **Tỷ lệ cảm xúc tiêu cực:** `{neg_pct}%` ({neg} phản hồi)
- **Tỷ lệ cảm xúc trung tính/băn khoăn:** `{neu_pct}%` ({neu} phản hồi)

---

### 2. PHÂN TÍCH TÁC ĐỘNG DOANH THU & UY TÍN THƯƠNG HIỆU
1. **Lợi thế cạnh tranh & Điểm mạnh chủ lực:**
   Khách hàng đánh giá rất cao về khía cạnh **`{top_strength}`** (chiếm tỷ trọng hài lòng lớn nhất). Đây là điểm khác biệt cốt lõi cần được tiếp tục duy trì và đưa vào các chiến dịch truyền thông định vị thương hiệu.
2. **Rủi ro sụt giảm doanh thu & Khách hàng rời bỏ (Churn Risk):**
   Có đến **{neg_pct}% khách hàng bày tỏ sự thất vọng**, tập trung nhiều nhất ở khâu **`{top_weakness}`**. Theo mô hình kinh doanh, mỗi khách hàng không hài lòng có thể truyền miệng tiêu cực đến 9-15 người khác, gây ảnh hưởng trực tiếp đến tỷ lệ tái mua (Repeat Purchase Rate).

---

### 3. QUYẾT SÁCH & ĐỀ XUẤT HÀNH ĐỘNG CẤP CAO
- [x] **Ưu tiên 1 (Cấp thiết):** Chỉ đạo bộ phận Quản lý chất lượng & Vận hành giải quyết dứt điểm các phàn nàn thuộc khía cạnh `{top_weakness}` trong vòng 14 ngày tới.
- [x] **Ưu tiên 2:** Thiết lập quy trình bồi hoàn và tặng quà tri ân đối với nhóm khách hàng để lại đánh giá tiêu cực để khôi phục niềm tin thương hiệu (Service Recovery Paradox).
- [x] **Ưu tiên 3:** Tiếp tục đầu tư nâng cấp hệ thống giám sát cảm xúc tự động định kỳ hàng tuần để phát hiện sớm các khủng hoảng truyền thông tiềm ẩn.
"""
        return report_md

    @classmethod
    def generate_cskh_report(cls, session: Dict, items: List[Dict]) -> str:
        """
        Generates Operational & Technical defect report for CSKH & Technical teams.
        """
        total = session.get('cleaned_count') or len(items) or 1
        neg_items = [it for it in items if it.get('sentiment') == 'Tiêu cực']
        neu_items = [it for it in items if it.get('sentiment') == 'Trung tính']

        # Group negative items by aspect
        defect_groups = {}
        for it in neg_items:
            asp = it.get('aspect', 'Khác')
            defect_groups.setdefault(asp, []).append(it.get('original_text', ''))

        report_md = f"""# BÁO CÁO CHI TIẾT DANH SÁCH LỖI & PHẢN HỒI CHO CSKH VÀ KỸ THUẬT
**Phiên:** {session.get('title')} | **Thời gian:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
**Tổng phản hồi tiêu cực cần xử lý:** {len(neg_items)} trường hợp / {total} lượt khảo sát

---

### 1. PHÂN LOẠI DANH MỤC LỖI KỸ THUẬT & DỊCH VỤ (DEFECT CLUSTERS)
"""
        for asp, samples in defect_groups.items():
            report_md += f"\n#### 🚨 Nhóm lỗi: `{asp}` ({len(samples)} trường hợp)\n"
            report_md += f"- **Mức độ nghiêm trọng:** {'🔴 Rất cao (P1)' if len(samples) >= 5 else '🟠 Trung bình (P2)'}\n"
            report_md += "- **Danh sách phản ánh thực tế từ khách hàng:**\n"
            for s in samples[:5]:
                report_md += f"  + *\"{s}\"*\n"
            report_md += "- **Nguyên nhân cốt lõi (Root Cause) & Bộ phận chịu trách nhiệm:** Kiểm tra lại quy trình đóng gói, rà soát nhà cung cấp và thái độ tư vấn.\n"

        report_md += f"""
---

### 2. QUY TRÌNH CHUẨN XỬ LÝ SỰ CỐ (SOP CHO NHÂN VIÊN CSKH)
1. **Bước 1 - Tiếp nhận & Đồng cảm (0-2 giờ):**
   Liên hệ trực tiếp qua điện thoại hoặc tin nhắn cho khách hàng có phản hồi tiêu cực. Sử dụng mẫu câu xin lỗi chân thành, lắng nghe không tranh cãi.
2. **Bước 2 - Phương án bồi thường/Đổi trả (2-12 giờ):**
   - Lỗi kỹ thuật / sản phẩm hư hỏng: Đổi mới 100% miễn phí vận chuyển tận nhà.
   - Giao hàng chậm / thái độ shipper: Tặng mã ưu đãi 15% - 20% cho đơn hàng kế tiếp.
3. **Bước 3 - Cập nhật trạng thái hệ thống:**
   Đánh dấu phiếu xử lý thành công sau khi khách hàng xác nhận đã hài lòng.

---

### 3. HÀNH ĐỘNG DÀNH CHO BỘ PHẬN KỸ THUẬT / KHO VẬN
- Rà soát ngay tem kiểm định chất lượng (QC Passed) trước khi niêm phong bưu phẩm.
- Làm việc với đơn vị vận chuyển đối tác về tỷ lệ trễ hẹn và cách ứng xử của tài xế.
"""
        return report_md
