# Lumina App Store

Marketplace nội bộ cho addon trong hệ sinh thái Lumina (Core / Plus / Storage / Care).

## Tính năng

- **Marketplace**: Duyệt, tìm kiếm, tải xuống app với filter theo hệ thống/danh mục
- **Live Skill Authoring**: Viết skill.md trong browser với Monaco editor, test AI ngay trong chat
- **Menu Apps**: Quản lý app đã cài, activate/deactivate, 1-click install từ store
- **App Engine**: Scan thư mục /Apps/, validate config, inject skill.md vào AI prompt

## Kiến trúc

```
Lumina App Store (repo này)
├── Config Schema    → JSON Schema canonical, Python validator
├── App Engine       → Scanner, registry, activation, prompt injection
├── Store Backend    → FastAPI REST API (apps, admin, authoring)
├── Store Frontend   → Next.js marketplace + authoring IDE + Menu Apps
└── Infrastructure   → Docker (Postgres 16, Redis 7, MinIO)
```

## Cài đặt

### Prerequisites

- Python 3.11+
- Node.js 20+
- pnpm
- Docker & Docker Compose

### Backend

```bash
# Start infrastructure
cd infra && docker compose up -d

# Run backend
cd apps/store_backend
pip install -e ".[dev]"
uvicorn main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs (Swagger UI)
```

### Frontend

```bash
cd apps/store-frontend
pnpm install
pnpm dev
# → http://localhost:3000
```

### Tests

```bash
# All backend tests (127 tests)
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
