# Lumina App Store

Marketplace nội bộ cho addon trong hệ sinh thái Lumina (Core / Plus / Storage / Care).

## Tính năng

- **Marketplace**: Duyệt, tìm kiếm, tải xuống app với filter theo hệ thống/danh mục
- **Live Skill Authoring**: Viết skill.md trong browser với Monaco editor, test AI ngay trong chat
- **Menu Apps**: Quản lý app đã cài, activate/deactivate, 1-click install từ store
- **App Engine**: Scan thư mục /Apps/, validate config, inject skill.md vào AI prompt
- **Dark mode**: Hỗ trợ tự động khi hệ thống ở chế độ tối
- **/LuminaApps/**: Kho lưu trữ ZIP trung tâm cho các app đã approved

## Kiến trúc

```
Lumina App Store (repo này)
├── Config Schema    → JSON Schema canonical, Python validator
├── App Engine       → Scanner, registry, activation, prompt injection
├── Store Backend    → FastAPI REST API (apps, admin, authoring)
├── Store Frontend   → Next.js marketplace + authoring IDE + Menu Apps
└── Infrastructure   → Docker (Postgres 16, Redis 7, MinIO)
```

## Quick Start (Windows)

```bash
# Double-click hoặc chạy trong terminal:
start_here.bat
```

Script tự động: cài dependencies, tạo DB + seed 4 app mẫu, chạy tests, start cả backend lẫn frontend.

## Cài đặt thủ công

### Prerequisites

- Python 3.11+
- Node.js 20+
- pnpm
- Docker & Docker Compose (tùy chọn, có SQLite fallback)

### Backend

```bash
# Với Docker
cd infra && docker compose up -d
cd apps/store_backend && uvicorn main:app --reload

# Không Docker (SQLite)
set LUMINA_DATABASE_URL=sqlite+aiosqlite:///./lumina_dev.db
python init_db.py                                    # Tạo DB + seed data
python -m uvicorn apps.store_backend.main:app --reload --port 8000
# → http://localhost:8000
# → http://localhost:8000/docs (Swagger UI)
```

### Frontend

```bash
cd apps/store-frontend
pnpm install
NEXT_PUBLIC_API_URL=http://localhost:8000 pnpm dev
# → http://localhost:3000
```

### Tests

```bash
# All backend tests (128 tests)
python -m pytest packages/config-schema/ apps/app_engine/ apps/store_backend/ -v

# Frontend build check
cd apps/store-frontend && pnpm build
```

## Cấu trúc một App

```
/Apps/{app-name}/
├── config.json      ← Metadata (bắt buộc)
├── skill.md         ← AI prompt definition (bắt buộc)
├── icon.png         ← 256x256 PNG (bắt buộc)
├── refs.md          ← Tài liệu bổ sung (tùy chọn)
└── tools/           ← API configs, handlers (tùy chọn)
    ├── api.json
    └── handler.py
```

## API Endpoints

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | /api/apps | Danh sách apps (filter, pagination, search) |
| GET | /api/apps/:id | Chi tiết app |
| GET | /api/apps/:id/download | Tải ZIP |
| POST | /api/admin/apps/:id/approve | Admin phê duyệt |
| POST | /api/admin/apps/:id/reject | Admin từ chối |
| POST | /api/authoring/new | Tạo app mới |
| GET | /api/authoring/:id/files | Liệt kê files |
| PUT | /api/authoring/:id/files/:path | Lưu file |
| POST | /api/authoring/:id/deploy | Deploy draft → live |
| POST | /api/authoring/:id/rollback/:ts | Rollback version |
| WS | /api/authoring/ws/:id | WebSocket real-time editing |

## License

MIT
