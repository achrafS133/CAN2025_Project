# Guardian AI - Frontend

Modern, production-ready React frontend for the Guardian AI security system.

## 🎨 Tech Stack

- **React 18** with TypeScript
- **Vite** for blazing-fast development
- **Tailwind CSS** for styling
- **React Router** for navigation
- **Axios** for API communication
- **Lucide React** for icons
- **Bun** as package manager

## ✨ Features

- 🌓 **Dark/Light Mode** - Seamless theme switching with system preference detection
- 📱 **Responsive Design** - Works perfectly on all devices
- 🔐 **JWT Authentication** - Secure API integration with token refresh
- ⚡ **Fast Performance** - Optimized with Vite and React 18
- 🎯 **Type-Safe** - Full TypeScript support throughout
- 🎨 **Modern UI** - Clean, professional interface with Tailwind CSS

## 🚀 Quick Start

### Prerequisites

- Bun >= 1.0.0
- FastAPI backend running on port 8888

### Installation

```bash
# Install dependencies
bun install

# Copy environment variables
cp .env.example .env

# Start development server
bun run dev
```

The frontend will be available at `http://localhost:5173`

### Build for Production

```bash
# Create production build
bun run build

# Preview production build
bun run preview
```

## 📁 Project Structure

```
src/
├── components/        # Reusable UI components
│   ├── ui/           # Base UI components (Button, Card, etc.)
│   ├── Layout.tsx    # Main layout wrapper
│   ├── Sidebar.tsx   # Navigation sidebar
│   └── ThemeToggle.tsx
├── contexts/         # React contexts
│   └── ThemeContext.tsx
├── lib/              # Utility libraries
│   └── utils.ts      # Helper functions (cn, etc.)
├── pages/            # Application pages
│   ├── Dashboard.tsx
│   ├── Threats.tsx
│   ├── AIChat.tsx
│   ├── Analytics.tsx
│   ├── Streams.tsx
│   ├── Alerts.tsx
│   └── Settings.tsx
├── services/         # API services
│   ├── api.ts        # Axios instance with interceptors
│   └── auth.ts       # Authentication service
├── App.tsx           # Root component with routing
├── main.tsx          # Application entry point
└── index.css         # Global styles with Tailwind

```

## 🎯 Available Pages

- **Dashboard** (`/`) - Overview with stats and activity feed
- **Threats** (`/threats`) - Threat monitoring and management
- **AI Chat** (`/ai-chat`) - Interact with AI models (GPT-4, Gemini, Claude)
- **Analytics** (`/analytics`) - Security analytics and reports
- **Streams** (`/streams`) - Live camera feeds
- **Alerts** (`/alerts`) - SMS alert configuration
- **Settings** (`/settings`) - System settings

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
VITE_API_URL=http://localhost:8888
```

### API Integration

The application connects to the FastAPI backend. Make sure the backend is running on the configured port (default: 8888).

## 🎨 Theming

The app supports light and dark modes out of the box:

- Click the theme toggle in the sidebar header
- Theme preference is saved in localStorage
- Follows system preference by default

### Customizing Colors

Edit the CSS variables in `src/index.css`:

```css
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  /* ... more variables */
}

.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  /* ... more variables */
}
```

## 🔐 Authentication

The app uses JWT tokens for authentication:

- Tokens are stored in localStorage
- Axios interceptors automatically add tokens to requests
- Automatic token refresh on 401 responses
- Redirects to login on authentication failure

## 🛠️ Available Scripts

```bash
# Development
bun run dev          # Start dev server with HMR

# Production
bun run build        # Create production build
bun run preview      # Preview production build locally

# Code Quality
bun run lint         # Run ESLint
```

## 👥 Developers

- **Achraf ERRAHAOUTI** - [@achraf-errahaoui](https://github.com/achraf-errahaoui)
- **Tajeddine BOURHIM** - [@scorpiontaj](https://github.com/scorpiontaj)
