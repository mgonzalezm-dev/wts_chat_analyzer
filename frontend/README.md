# WhatsApp Conversation Reader - Frontend

A React-based web application for reading, analyzing, and managing WhatsApp conversations.

## Features

- **Authentication & Authorization**: JWT-based authentication with role-based access control
- **Conversation Management**: Import, view, search, and export WhatsApp conversations
- **Analytics Dashboard**: Visualize conversation statistics and insights
- **File Upload**: Drag-and-drop interface for importing conversation files
- **Dark/Light Theme**: Toggle between themes for comfortable viewing
- **Responsive Design**: Works on desktop and tablet devices

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Material-UI (MUI)** for UI components
- **Redux Toolkit** for state management
- **React Router** for navigation
- **Axios** for API calls
- **React Hook Form** for form handling
- **Recharts** for data visualization
- **date-fns** for date manipulation

## Prerequisites

- Node.js 18+ and npm
- Backend API running on http://localhost:8000

## Installation

1. Install dependencies:
```bash
npm install
```

2. Copy environment variables:
```bash
cp .env.example .env
```

3. Update `.env` with your configuration if needed

## Development

Start the development server:
```bash
npm run dev
```

The application will be available at http://localhost:3000

## Building

Build for production:
```bash
npm run build
```

Preview production build:
```bash
npm run preview
```

## Project Structure

```
src/
├── components/       # Reusable UI components
│   ├── auth/        # Authentication components
│   ├── common/      # Common/shared components
│   ├── conversation/# Conversation-related components
│   ├── dashboard/   # Dashboard components
│   └── analytics/   # Analytics components
├── pages/           # Page components (routes)
├── services/        # API services
├── hooks/           # Custom React hooks
├── store/           # Redux store and slices
├── types/           # TypeScript type definitions
├── utils/           # Utility functions
├── App.tsx          # Main app component
└── main.tsx         # Application entry point
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking

## API Integration

The frontend connects to the backend API at `http://localhost:8000/v1`. During development, Vite proxies API requests to avoid CORS issues.

## Authentication Flow

1. User logs in with email/password
2. Backend returns JWT access and refresh tokens
3. Tokens are stored in localStorage
4. Access token is included in API request headers
5. When access token expires, refresh token is used to get new tokens
6. User is redirected to login if refresh fails

## State Management

The application uses Redux Toolkit with the following slices:
- `auth` - User authentication state
- `conversation` - Conversations and messages
- `ui` - UI state (theme, notifications, loading)

## Contributing

1. Follow the existing code style
2. Write meaningful commit messages
3. Add appropriate TypeScript types
4. Test your changes thoroughly
5. Update documentation as needed

## License

This project is part of the WhatsApp Conversation Reader system.
