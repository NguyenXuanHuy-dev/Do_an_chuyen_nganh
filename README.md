# HỆ THỐNG PHÂN TÍCH CẢM XÚC KHÁCH HÀNG TỪ VĂN BẢN (SENTIMENT AI)
> **Đồ án chuyên ngành**  
> Xây dựng bằng Python (Flask, SQLAlchemy, Chart.js, Vietnamese NLP Preprocessor & AI Chat Agent)

---

## 1. PHÂN TÍCH TÍNH HỢP LÝ CỦA CÁC CHỨC NĂNG (THEO FILE MÔ TẢ ĐỀ TÀI)

Dựa trên tài liệu mô tả đề tài, các chức năng được phân tích và đánh giá tính hợp lý, khả thi và giá trị thực tiễn như sau:

### A. Phân hệ USER (Người dùng)
1. **Đăng nhập / Đăng ký & Google One-Tap SSO:**
   - *Tính hợp lý:* **Rất hợp lý & Cần thiết**. Cho phép định danh người dùng, bảo mật các tập dữ liệu nhạy cảm của doanh nghiệp, lưu trữ lịch sử các phiên phân tích cá nhân.
2. **Quên mật khẩu (Xác thực mã OTP):**
   - *Tính hợp lý:* **Hợp lý**. Bảo vệ tài khoản an toàn với cơ chế mã OTP xác thực có giới hạn thời gian (15 phút).
3. **Tải lên tệp phản hồi (Excel .xlsx/.xls, CSV, Word .docx, TXT):**
   - *Tính hợp lý:* **Cực kỳ hợp lý & Giá trị cao**. Trong thực tế, dữ liệu nhận xét/đánh giá của khách hàng từ Shopee, Lazada, Tiki, TikTok Shop hoặc form khảo sát CSKH thường được xuất ra dưới dạng Excel/CSV.
4. **Nhập văn bản trực tiếp:**
   - *Tính hợp lý:* **Rất hợp lý**. Giúp người dùng kiểm tra nhanh (Quick test) một vài bình luận hoặc đoạn văn bản đơn lẻ mà không cần phải mất công tạo file Excel.
5. **Hồ sơ cá nhân & Quản lý Token/Quota tài nguyên:**
   - *Tính hợp lý:* **Hợp lý**. Kiểm soát tài nguyên tính toán/gọi API AI, minh bạch hóa hạn mức sử dụng và dung lượng lưu trữ của từng người dùng.
6. **Tiền xử lý văn bản tự động (Làm sạch teencode, emoji to sentiment label):**
   - *Tính hợp lý:* **Linh hồn của hệ thống NLP tiếng Việt**. Đánh giá trên mạng xã hội Việt Nam tràn ngập từ viết tắt teencode (`ko`, `k`, `dc`, `đc`, `ntn`, `ib`, `rep`, `ship`, `dth`, `bth`, `sz`, `thk`, `iu`,...) và icon/emoji (`😍`, `😡`, `😭`, `👍`, `⭐`,...). Nếu không tiền xử lý chuẩn hóa thì mô hình AI sẽ bị sai lệch nghiêm trọng.
7. **Gợi ý xử lý dữ liệu lỗi (Data Cleaning Suggestions):**
   - *Tính hợp lý:* **Rất thực tế**. File tải lên thường có dòng trống, dữ liệu rác hoặc các dòng copy lặp lại. Hệ thống phát hiện và cung cấp tùy chọn 1-click để khử trùng lặp và xóa dòng rác trước khi chạy mô hình.
8. **Phân loại cảm xúc tổng quát & Chi tiết (Aspect-Based Sentiment):**
   - *Tính hợp lý:* **Rất hợp lý & Toàn diện**. Phân loại 3 sắc thái (Tích cực, Tiêu cực, Trung tính) kèm theo độ tin cậy (Confidence Score) và bóc tách khía cạnh (Chất lượng, Giá cả, Dịch vụ, Giao hàng, Bao bì). Doanh nghiệp sẽ biết ngay khách hàng khen/chê cụ thể ở khâu nào.
9. **Tương tác dạng hỏi - đáp tự nhiên (Chat Agent + Prompt mẫu):**
   - *Tính hợp lý:* **Hiện đại & Đột phá**. Thay vì chỉ nhìn số liệu khô khan, người dùng có thể "trò chuyện" trực tiếp với tập dữ liệu thông qua Chat Agent và các nút Prompt mẫu (Ví dụ: "Tóm tắt 3 vấn đề nhức nhối nhất", "Đánh giá chất lượng vận chuyển shipper",...).
10. **Trực quan hóa dữ liệu cảm xúc:**
    - *Tính hợp lý:* **Tuyệt vời**. Tự động sinh biểu đồ phân bổ tỷ lệ cảm xúc (tròn), biểu đồ khía cạnh (cột), xu hướng biến thiên (đường), cho phép đổi dạng biểu đồ trực tiếp trên giao diện bằng nút bấm.
11. **Tự động sinh báo cáo chi tiết & Tùy chỉnh văn phong:**
    - *Tính hợp lý:* **Rất hữu ích cho doanh nghiệp**. Cho phép lựa chọn 2 văn phong báo cáo:
      * *Báo cáo tóm tắt chỉ số VOC (Voice of Customer) cho Ban Giám Đốc:* Tập trung vào NSS, CSAT, rủi ro doanh thu và quyết sách cấp cao.
      * *Báo cáo chi tiết danh sách lỗi phản ánh cho CSKH/Kỹ thuật:* Tập trung vào bóc tách nguyên nhân cốt lõi (Root cause), quy trình chuẩn SOP xử lý khiếu nại.
12. **Lưu trữ & Chia sẻ báo cáo qua link công khai:**
    - *Tính hợp lý:* **Rất tiện lợi**. Cho phép gửi link báo cáo trực tuyến cho đối tác, sếp hoặc đồng nghiệp xem ngay mà không cần tài khoản đăng nhập.

---

### B. Phân hệ ADMIN (Quản trị viên)
1. **Đăng nhập Admin & Phân quyền:** Quản lý truy cập an toàn.
2. **Quản lý người dùng:** Danh sách tài khoản, phân quyền (user/admin), theo dõi token quota, khóa/mở tài khoản.
3. **Cấu hình hệ thống AI & Prompt mẫu:** Cho phép Admin cập nhật thêm, sửa, xóa các "Prompt mẫu" để định hướng AI phân tích chuẩn xác hơn.
4. **Thống kê hệ thống (Admin Dashboard):** Biểu đồ tỷ lệ cảm xúc toàn hệ thống, số lượng phiên phân tích, số file xử lý, độ hài lòng về AI.
5. **Quản lý phản hồi (Feedbacks):** Tiếp nhận đánh giá Like/Dislike của người dùng về câu trả lời của AI để tinh chỉnh mô hình.

---

## 2. CẤU TRÚC DỰ ÁN (PROJECT STRUCTURE)

Dự án được phân chia theo mô hình MVC / Service-Oriented Architecture chuẩn mực:

```
Hệ thống cảm xúc/
├── app.py                     # Entry point khởi chạy ứng dụng Flask
├── config.py                  # Cấu hình ứng dụng, Database URI, Secret key, Quota
├── requirements.txt           # Danh sách thư viện phụ thuộc
├── sentiment_system.db        # Cơ sở dữ liệu SQLite
│
├── database/                  # Quản lý kết nối SQL
│   ├── __init__.py
│   └── connection.py          # Kết nối SQLAlchemy engine, scoped_session, Base ORM
│
├── models/                    # Khai báo các bảng dữ liệu (ORM Models)
│   ├── __init__.py
│   ├── user.py                # Bảng Users & PasswordResetToken (mã OTP)
│   ├── session.py             # Bảng AnalysisSession & FeedbackItem (dữ liệu đánh giá)
│   ├── chat.py                # Bảng ChatMessage & FeedbackRating (lịch sử chat và rating)
│   └── config.py              # Bảng PromptTemplate & SystemSetting
│
├── controllers/               # Bộ điều khiển (Routes / Endpoints)
│   ├── __init__.py
│   ├── auth_controller.py     # Đăng nhập, đăng ký, Google SSO, quên mật khẩu OTP, hồ sơ
│   ├── analysis_controller.py # Upload file, tiền xử lý, chạy mô hình, chi tiết phiên, xuất Excel
│   ├── chat_controller.py     # Chat Agent thông minh, câu hỏi gợi ý, rating câu trả lời
│   ├── report_controller.py   # Báo cáo VOC BOD, báo cáo lỗi CSKH, chia sẻ link công khai
│   └── admin_controller.py    # Quản lý người dùng, quản trị dữ liệu, prompt templates
│
├── services/                  # Xử lý nghiệp vụ chuyên sâu
│   ├── __init__.py
│   ├── preprocess_service.py  # Chuẩn hóa teencode tiếng Việt phong phú, chuyển đổi emoji, làm sạch
│   ├── sentiment_service.py   # Phân loại cảm xúc (Tích cực/Tiêu cực/Trung tính), Aspect extraction, Confidence score
│   ├── file_service.py        # Đọc file Excel (.xlsx, .xls), CSV, Word (.docx), TXT và chẩn đoán lỗi
│   ├── chat_agent_service.py  # AI Chat Agent hỏi đáp thông minh dựa trên ngữ cảnh dữ liệu phiên
│   ├── report_service.py      # Tự động viết báo cáo chiến lược VOC cho BOD và danh mục lỗi cho CSKH
│   ├── user_service.py        # Xác thực, OTP, mã hóa mật khẩu, quản lý token quota
│   └── admin_service.py       # Thống kê toàn hệ thống, quản lý người dùng, gieo prompt mặc định
│
├── static/                    # Giao diện UI/UX hiện đại
│   ├── css/
│   │   └── style.css          # CSS Glassmorphism, Theme Sáng/Tối, animations, layout responsive
│   └── js/
│       ├── main.js            # Đổi Theme Sáng/Tối, Toast alert, navigation
│       ├── analysis.js        # Drag-and-drop file, Chart.js linh hoạt (Tròn, Cột, Đường), bộ lọc
│       ├── chat_agent.js      # Giao diện bong bóng chat, typing indicator, prompt chips, like/dislike
│       └── admin.js           # Biểu đồ admin dashboard, modal CRUD prompt mẫu, khóa/mở user
│
├── templates/                 # Giao diện Jinja2 HTML5
│   ├── base.html              # Layout khung chuẩn, Sidebar, Topbar, Flash message
│   ├── auth/                  # Giao diện xác thực (login, register, forgot_password)
│   ├── analysis/              # Giao diện phân tích (index, session_detail, history)
│   ├── chat/                  # Giao diện Chat Agent (agent.html)
│   ├── report/                # Giao diện báo cáo (view.html, public_shared.html)
│   ├── profile/               # Giao diện hồ sơ cá nhân và quản lý token (profile.html)
│   └── admin/                 # Giao diện quản trị (dashboard, users, prompts, feedbacks)
│
└── sample_data/               # Dữ liệu mẫu kiểm thử
    └── sample_customer_feedback.xlsx # File Excel chứa 20+ đánh giá thực tế (có teencode, emoji, dòng trống/trùng lặp)
```

---

## 3. HƯỚNG DẪN CÀI ĐẶT & CHẠY DỰ ÁN

### Bước 1: Cài đặt thư viện phụ thuộc
Mở terminal tại thư mục dự án và chạy:
```bash
pip install -r requirements.txt
```

### Bước 2: Khởi chạy ứng dụng
```bash
python app.py
```
Ứng dụng sẽ tự động:
- Khởi tạo cơ sở dữ liệu `sentiment_system.db` với đầy đủ các bảng.
- Tạo sẵn tài khoản Quản trị viên (Admin).
- Nạp sẵn các Prompt mẫu định hướng AI thông minh.
- Chạy máy chủ tại: **`http://127.0.0.1:5000`**

### Bước 3: Tài khoản đăng nhập mặc định
- **Tài khoản Admin:** `admin` | Mật khẩu: `admin123`
- **Đăng nhập một chạm:** Bạn có thể bấm nút **"Đăng nhập một chạm bằng Google"** trên màn hình đăng nhập để vào ngay lập tức.
- **Tạo tài khoản mới:** Người dùng mới đăng ký sẽ tự động được cấp **50,000 token**.

---

## 4. DỮ LIỆU KIỂM THỬ (SAMPLE DATA)
Hệ thống đã chuẩn bị sẵn tệp Excel mẫu tại:
`sample_data/sample_customer_feedback.xlsx`  
Bao gồm:
- Các bình luận tích cực, tiêu cực và trung tính với đủ sắc thái.
- Teencode tiếng Việt phong phú (`nhah`, `dth`, `xịn xò`, `như hạch`,...).
- Emoji cảm xúc (`😍`, `❤️`, `😡`, `🤬`, `👎`, `💯`,...).
- Các dòng trống và dòng trùng lặp để người dùng trải nghiệm ngay tính năng **"Kiểm tra & Gợi ý làm sạch dữ liệu lỗi tự động"**.
