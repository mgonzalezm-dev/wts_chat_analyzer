import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import ConversationListPage from '../ConversationListPage';
import { renderWithProviders, mockConversation } from '../../test/utils';
import * as api from '../../services/api';

// Mock the API service
vi.mock('../../services/api', () => ({
  conversationService: {
    getConversations: vi.fn(),
    deleteConversation: vi.fn(),
  },
}));

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

describe('ConversationListPage', () => {
  const mockConversations = [
    mockConversation({ id: '1', name: 'Family Chat' }),
    mockConversation({ id: '2', name: 'Work Discussion' }),
    mockConversation({ id: '3', name: 'Friends Group' }),
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders page title and upload button', () => {
    renderWithProviders(<ConversationListPage />);
    
    expect(screen.getByText('Conversations')).toBeInTheDocument();
    expect(screen.getByText('Upload New')).toBeInTheDocument();
  });

  it('loads and displays conversations', async () => {
    vi.mocked(api.conversationService.getConversations).mockResolvedValue({
      data: { items: mockConversations, total: 3 },
    });
    
    renderWithProviders(<ConversationListPage />);
    
    await waitFor(() => {
      expect(screen.getByText('Family Chat')).toBeInTheDocument();
      expect(screen.getByText('Work Discussion')).toBeInTheDocument();
      expect(screen.getByText('Friends Group')).toBeInTheDocument();
    });
  });

  it('shows loading state while fetching conversations', () => {
    vi.mocked(api.conversationService.getConversations).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );
    
    renderWithProviders(<ConversationListPage />);
    
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('shows empty state when no conversations', async () => {
    vi.mocked(api.conversationService.getConversations).mockResolvedValue({
      data: { items: [], total: 0 },
    });
    
    renderWithProviders(<ConversationListPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/No conversations yet/i)).toBeInTheDocument();
      expect(screen.getByText(/Upload your first WhatsApp chat/i)).toBeInTheDocument();
    });
  });

  it('handles search functionality', async () => {
    vi.mocked(api.conversationService.getConversations).mockResolvedValue({
      data: { items: mockConversations, total: 3 },
    });
    
    renderWithProviders(<ConversationListPage />);
    
    await waitFor(() => {
      expect(screen.getByText('Family Chat')).toBeInTheDocument();
    });
    
    const searchInput = screen.getByPlaceholderText(/Search conversations/i);
    fireEvent.change(searchInput, { target: { value: 'Family' } });
    
    await waitFor(() => {
      expect(api.conversationService.getConversations).toHaveBeenCalledWith(
        expect.objectContaining({ search: 'Family' })
      );
    });
  });

  it('handles conversation deletion', async () => {
    vi.mocked(api.conversationService.getConversations).mockResolvedValue({
      data: { items: mockConversations, total: 3 },
    });
    vi.mocked(api.conversationService.deleteConversation).mockResolvedValue({});
    
    renderWithProviders(<ConversationListPage />);
    
    await waitFor(() => {
      expect(screen.getByText('Family Chat')).toBeInTheDocument();
    });
    
    // Click delete button on first conversation
    const deleteButtons = screen.getAllByLabelText(/delete/i);
    fireEvent.click(deleteButtons[0]);
    
    // Confirm deletion in dialog
    const confirmButton = await screen.findByText('Delete', { selector: 'button' });
    fireEvent.click(confirmButton);
    
    await waitFor(() => {
      expect(api.conversationService.deleteConversation).toHaveBeenCalledWith('1');
    });
  });

  it('displays conversation metadata correctly', async () => {
    const conversationWithDetails = mockConversation({
      id: '1',
      name: 'Detailed Chat',
      message_count: 150,
      participant_count: 5,
      created_at: new Date('2024-01-15').toISOString(),
    });
    
    vi.mocked(api.conversationService.getConversations).mockResolvedValue({
      data: { items: [conversationWithDetails], total: 1 },
    });
    
    renderWithProviders(<ConversationListPage />);
    
    await waitFor(() => {
      expect(screen.getByText('Detailed Chat')).toBeInTheDocument();
      expect(screen.getByText(/150 messages/i)).toBeInTheDocument();
      expect(screen.getByText(/5 participants/i)).toBeInTheDocument();
      expect(screen.getByText(/Jan 15, 2024/i)).toBeInTheDocument();
    });
  });

  it('handles pagination', async () => {
    vi.mocked(api.conversationService.getConversations).mockResolvedValue({
      data: { items: mockConversations, total: 30 }, // More than one page
    });
    
    renderWithProviders(<ConversationListPage />);
    
    await waitFor(() => {
      expect(screen.getByRole('navigation')).toBeInTheDocument(); // Pagination component
    });
    
    // Click next page
    const nextButton = screen.getByLabelText(/next page/i);
    fireEvent.click(nextButton);
    
    await waitFor(() => {
      expect(api.conversationService.getConversations).toHaveBeenCalledWith(
        expect.objectContaining({ page: 2 })
      );
    });
  });

  it('opens upload dialog when upload button is clicked', async () => {
    renderWithProviders(<ConversationListPage />);
    
    const uploadButton = screen.getByText('Upload New');
    fireEvent.click(uploadButton);
    
    await waitFor(() => {
      expect(screen.getByText('Upload WhatsApp Chat')).toBeInTheDocument();
    });
  });

  it('handles error state', async () => {
    vi.mocked(api.conversationService.getConversations).mockRejectedValue(
      new Error('Failed to load conversations')
    );
    
    renderWithProviders(<ConversationListPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/Failed to load conversations/i)).toBeInTheDocument();
      expect(screen.getByText('Retry')).toBeInTheDocument();
    });
  });

  it('filters by status', async () => {
    vi.mocked(api.conversationService.getConversations).mockResolvedValue({
      data: { items: mockConversations, total: 3 },
    });
    
    renderWithProviders(<ConversationListPage />);
    
    await waitFor(() => {
      expect(screen.getByText('Family Chat')).toBeInTheDocument();
    });
    
    // Open status filter
    const statusFilter = screen.getByLabelText(/Filter by status/i);
    fireEvent.click(statusFilter);
    
    // Select "completed" status
    const completedOption = screen.getByText('Completed');
    fireEvent.click(completedOption);
    
    await waitFor(() => {
      expect(api.conversationService.getConversations).toHaveBeenCalledWith(
        expect.objectContaining({ status: 'completed' })
      );
    });
  });

  it('sorts conversations', async () => {
    vi.mocked(api.conversationService.getConversations).mockResolvedValue({
      data: { items: mockConversations, total: 3 },
    });
    
    renderWithProviders(<ConversationListPage />);
    
    await waitFor(() => {
      expect(screen.getByText('Family Chat')).toBeInTheDocument();
    });
    
    // Open sort menu
    const sortButton = screen.getByLabelText(/Sort by/i);
    fireEvent.click(sortButton);
    
    // Select sort by name
    const nameOption = screen.getByText('Name');
    fireEvent.click(nameOption);
    
    await waitFor(() => {
      expect(api.conversationService.getConversations).toHaveBeenCalledWith(
        expect.objectContaining({ sort_by: 'name' })
      );
    });
  });
});