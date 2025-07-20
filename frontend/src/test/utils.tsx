import React from 'react';
import type { ReactElement } from 'react';
import { render } from '@testing-library/react';
import type { RenderOptions } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { configureStore } from '@reduxjs/toolkit';
import type { RootState } from '../store';
import authReducer from '../store/slices/authSlice';
import conversationReducer from '../store/slices/conversationSlice';
import uiReducer from '../store/slices/uiSlice';

const theme = createTheme();

interface ExtendedRenderOptions extends Omit<RenderOptions, 'queries'> {
  preloadedState?: Partial<RootState>;
  store?: ReturnType<typeof configureStore>;
}

export function renderWithProviders(
  ui: ReactElement,
  {
    preloadedState = {},
    store = configureStore({
      reducer: {
        auth: authReducer,
        conversation: conversationReducer,
        ui: uiReducer,
      } as any,
      preloadedState,
    }),
    ...renderOptions
  }: ExtendedRenderOptions = {}
) {
  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <Provider store={store}>
        <BrowserRouter>
          <ThemeProvider theme={theme}>
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              {children}
            </LocalizationProvider>
          </ThemeProvider>
        </BrowserRouter>
      </Provider>
    );
  }

  return { store, ...render(ui, { wrapper: Wrapper, ...renderOptions }) };
}

// Mock data generators
export const mockUser = (overrides = {}) => ({
  id: '1',
  email: 'test@example.com',
  full_name: 'Test User',
  roles: ['user'],
  is_active: true,
  created_at: new Date().toISOString(),
  last_login: new Date().toISOString(),
  ...overrides,
});

export const mockConversation = (overrides = {}) => ({
  id: '1',
  name: 'Test Conversation',
  user_id: '1',
  file_path: '/test/path.txt',
  file_size: 1024,
  message_count: 100,
  participant_count: 2,
  start_date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
  end_date: new Date().toISOString(),
  status: 'completed',
  created_at: new Date().toISOString(),
  metadata: {
    participants: ['Alice', 'Bob'],
  },
  ...overrides,
});

export const mockMessage = (overrides = {}) => ({
  id: '1',
  conversation_id: '1',
  sender: 'Alice',
  content: 'Test message content',
  timestamp: new Date().toISOString(),
  message_type: 'text',
  metadata: {},
  ...overrides,
});

export const mockAnalytics = (overrides = {}) => ({
  message_count: 100,
  participant_count: 2,
  date_range: {
    start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
    end: new Date().toISOString(),
  },
  participant_stats: [
    {
      name: 'Alice',
      message_count: 50,
      avg_message_length: 45.5,
      active_hours: [10, 11, 14, 15, 16, 20, 21],
    },
    {
      name: 'Bob',
      message_count: 50,
      avg_message_length: 38.2,
      active_hours: [9, 10, 11, 15, 16, 17, 21, 22],
    },
  ],
  timeline_data: Array.from({ length: 7 }, (_, i) => ({
    date: new Date(Date.now() - (6 - i) * 24 * 60 * 60 * 1000).toISOString(),
    message_count: Math.floor(Math.random() * 20) + 5,
  })),
  sentiment_analysis: {
    overall_sentiment: 'positive',
    sentiment_distribution: {
      positive: 0.6,
      neutral: 0.3,
      negative: 0.1,
    },
    sentiment_timeline: [],
  },
  top_keywords: [
    { keyword: 'test', score: 0.9, frequency: 15 },
    { keyword: 'message', score: 0.8, frequency: 12 },
    { keyword: 'hello', score: 0.7, frequency: 10 },
  ],
  top_entities: [
    { entity: 'Alice', type: 'PERSON', count: 50 },
    { entity: 'Bob', type: 'PERSON', count: 50 },
  ],
  message_types: {
    text: 90,
    media: 8,
    system: 2,
  },
  ...overrides,
});

// Re-export everything from React Testing Library
export * from '@testing-library/react';
export { default as userEvent } from '@testing-library/user-event';