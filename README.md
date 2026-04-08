# HomeTask — Платформа управления бытовыми задачами

## Быстрый старт

### Вариант A: Docker (рекомендуется)

```bash
docker-compose up --build
# В новом терминале:
docker-compose exec backend python -m app.seed
```

Открой: http://localhost:5173  
Логин: `alex@home.ru` / `password123`

### Вариант B: Локально

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # при необходимости отредактируй
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Стек

- **Backend**: FastAPI + SQLAlchemy (async) + PostgreSQL + Alembic
- **Frontend**: React 18 + TypeScript + Tailwind CSS + React Query + Zustand
- **Auth**: JWT (jose) + bcrypt
- **Charts**: Recharts
- **PWA**: manifest.json готов; Service Worker добавить в следующей итерации

## API Документация

После запуска бэкенда: http://localhost:8000/docs

## Архитектура

```
backend/app/
  api/v1/endpoints/  — FastAPI роутеры
  services/          — бизнес-логика
  models/            — SQLAlchemy ORM
  schemas/           — Pydantic схемы
  core/              — config, database, security

frontend/src/
  api/               — axios клиенты
  hooks/             — React Query хуки
  pages/             — страницы
  components/        — переиспользуемые компоненты
  store/             — Zustand auth store
  utils/             — recurrence, dates
```

## PWA roadmap

- [ ] Service Worker (Workbox) для офлайн-кэша
- [ ] Push-уведомления (Web Push API)
- [ ] Background Sync для офлайн-очереди событий
- [ ] Install prompt
