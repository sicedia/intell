# Intelli - Monorepo Application

Monorepo application with Django backend (REST API) and Next.js frontend (TypeScript).

## 📁 Project Structure

```
intell/
├── backend/          # Django REST API
│   ├── config/       # Main Django configuration
│   ├── apps/         # Django applications
│   │   └── core/     # Main backend app
│   ├── manage.py     # Django management script
│   └── requirements.txt
├── frontend/         # Next.js Application
│   ├── app/          # Next.js App Router
│   ├── public/       # Static files
│   └── package.json
└── README.md         # This file
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** (recommended 3.11+)
- **Node.js 18+** (recommended 20+)
- **npm** or **yarn** or **pnpm**

### Installation and Setup

#### Backend (Django)

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create and activate virtual environment (if it doesn't exist):**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser (optional):**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start development server:**
   ```bash
   python manage.py runserver
   ```
   
   Backend will be available at: **http://localhost:8000**
   - Admin panel: http://localhost:8000/admin
   - API: http://localhost:8000/api/

#### Frontend (Next.js)

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   # or
   yarn install
   # or
   pnpm install
   ```

3. **Start development server:**
   ```bash
   npm run dev
   # or
   yarn dev
   # or
   pnpm dev
   ```
   
   Frontend will be available at: **http://localhost:3000**

## 🔧 Configuration

### Backend - CORS Configuration

The backend is configured to allow requests from the frontend. CORS configuration is located in `backend/api/settings.py`:

- **CORS_ALLOWED_ORIGINS**: Allows requests from `http://localhost:3000`
- **CORS_ALLOW_CREDENTIALS**: Enabled for authentication

### Frontend - API Configuration

The frontend is configured to make requests to the backend. Make sure to configure the API base URL as needed.

## 🛠️ Technologies Used

### Backend
- **Django 5.2.8** - Python web framework
- **Django REST Framework 3.16.1** - REST API framework
- **django-cors-headers 4.9.0** - CORS handling
- **SQLite** - Database (development)

### Frontend
- **Next.js 16.0.6** - React framework
- **React 19.2.0** - UI library
- **TypeScript 5** - Static typing
- **Tailwind CSS 4** - CSS framework
- **@tanstack/react-query 5.90.11** - Server state management
- **Zustand 5.0.9** - Client state management
- **Axios 1.13.2** - HTTP client

## 📝 Useful Commands

### Backend

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver

# Run server on specific port
python manage.py runserver 8000

# Run tests
python manage.py test
```

### Frontend

```bash
# Development
npm run dev

# Production build
npm run build

# Start production server
npm run start

# Linter
npm run lint
```

## 🧪 Development

### Recommended Workflow

1. **Start both servers:**
   - Terminal 1: Backend (`cd backend && python manage.py runserver`)
   - Terminal 2: Frontend (`cd frontend && npm run dev`)

2. **Backend Development:**
   - Create models in `backend/apps/core/models.py`
   - Create views/viewsets in `backend/apps/core/views.py`
   - Configure URLs in `backend/config/urls.py` or create `backend/apps/core/urls.py`
   - Create serializers if using DRF

3. **Frontend Development:**
   - Create components in `frontend/app/`
   - Configure API calls using Axios or React Query
   - Use Zustand for global client state

### API Structure

The backend exposes a REST API. Example structure:

```
GET    /api/endpoint/          # List resources
POST   /api/endpoint/          # Create resource
GET    /api/endpoint/:id/      # Get resource
PUT    /api/endpoint/:id/      # Update resource
PATCH  /api/endpoint/:id/      # Partial update
DELETE /api/endpoint/:id/      # Delete resource
```

## 📚 Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Next.js Documentation](https://nextjs.org/docs)
- [React Query](https://tanstack.com/query/latest)
- [Zustand](https://zustand-demo.pmnd.rs/)

## 🔒 Security Notes

- The Django `SECRET_KEY` in `settings.py` is for development only. **NEVER** use this value in production.
- In production, use environment variables for sensitive configurations.
- Configure `ALLOWED_HOSTS` appropriately in production.
- Set `DEBUG = False` in production.

## 🤝 Contributing

To contribute to the project:

1. Create a branch for your feature
2. Make your changes
3. Ensure both servers work correctly
4. Create a pull request

## 📄 License

[Specify license if applicable]

