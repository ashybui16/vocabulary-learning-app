# Sổ từ vựng

Bảng đơn giản để học từ vựng tiếng Anh. Bạn nhập một từ và một câu có chứa từ đó,
ứng dụng sẽ tự điền phiên âm, từ loại, nghĩa tiếng Việt, nghĩa tiếng Anh, cụm từ thường gặp,
từ đồng nghĩa và một ví dụ khác. Ứng dụng chỉ đưa ra **nghĩa của từ trong câu của bạn**,
không liệt kê tất cả các nghĩa.

## Cài đặt (một lần)

1. Lấy khóa API của Claude tại https://console.anthropic.com (mục *API Keys*).
2. Cài thư viện:

   ```
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```

## Chạy

```
export ANTHROPIC_API_KEY="khóa-của-bạn"
.venv/bin/python server.py
```

Sau đó mở http://localhost:8000.

Để không phải nhập khóa mỗi lần, hãy thêm dòng `export ANTHROPIC_API_KEY=...` vào file `~/.zshrc`.

## Sử dụng

- Nhập từ và câu, rồi bấm **Thêm**.
- Bấm vào ô bất kỳ để sửa. Nhấn Enter để lưu, Shift+Enter để xuống dòng.
- Dùng ô **Tìm kiếm** để lọc bảng. Bấm ✕ để xóa một từ.

Các từ được lưu trong file `words.json`. Hãy sao lưu file này để giữ dữ liệu.
Mỗi lần tra từ tốn một ít phí API (rất nhỏ) và cần có Internet.
