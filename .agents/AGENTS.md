# AGENTS.md - Quy ước và Luật cứng cho Coding Agent

## 1. Technology Stack Quy Định
- **Language:** Python 3.10+
- **Orchestration:** LangGraph (StateGraph), LangChain Core
- **Scraper Layer:** Scrapling (Ưu tiên StealthyFetcher cho Voz/Reddit)
- **Vector Database:** Chroma (Local) hoặc Supabase/pgvector
- **LLM API:** [Điền API bạn dùng, ví dụ: OpenAI/Gemini/Anthropic]

## 2. Cấu trúc thư mục bắt buộc
Dự án phải tuân thủ nghiêm ngặt layout cấu trúc dưới đây. Agent không tự ý sinh file ngoài cấu trúc này:
├── src/
│   ├── graph/          # Chứa định nghĩa LangGraph (nodes, edges, state)
│   ├── scraper/        # Chứa module Scrapling chuyên biệt cho từng forum
│   ├── rag/            # Chứa logic Embedding, VectorDB và Retriever
│   └── config.py       # Cấu hình môi trường và API Keys
├── tests/              # Thư mục chứa các file Test Suite (PyTest)
└── main.py             # Entrypoint của ứng dụng

## 3. Quy ước viết Code & Luật cứng (Hard Rules)
- **Luật về State:** Tất cả các Node trong LangGraph bắt buộc phải nhận vào `AgentState` và trả về một dict cập nhật `AgentState`. Tuyệt đối không thay đổi biến toàn cục bên ngoài State.
- **Luật về Scraper:** - Phải bọc toàn bộ tác vụ Fetch của Scrapling trong khối `try-except`. Nếu lỗi mạng hoặc bị chặn (Block), phải trả về thông báo lỗi tường minh thay vì để sập chương trình.
  - Phải sử dụng bộ chọn Adaptive của Scrapling để tránh gãy code khi cấu trúc HTML của forum thay đổi.
- **Luật về Kiểm thử:** Không được viết code tính năng trước khi file Test tương ứng trong thư mục `tests/` được tạo và định nghĩa rõ ràng (Kỷ luật TDD).
- **Luật về Log:** Luôn dùng thư viện `logging` của Python để ghi lại luồng đi của Agent (Ví dụ: "Router chọn: Scraper", "Scrapling đang quét URL: ..."). Không dùng hàm `print()` bừa bãi.

## 4. Nhật ký sai lầm (Agent Error Log)
*Mỗi lần Agent làm sai điều gì, hãy ghi thêm một dòng luật vào đây để răn đe hệ thống trong các phiên làm việc tiếp theo.*
- (Trống - Sẽ cập nhật trong quá trình chạy)

## 5. Quy ước Git & Commit
- **Branching:** Nhánh gốc là `main`, nhánh phát triển (development) là `dev`.
- **Commit Message:** Tuân thủ chặt chẽ Semantic Commit Messages. Các tiền tố hợp lệ bao gồm: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`, `test:`, `style:`, `perf:`.
