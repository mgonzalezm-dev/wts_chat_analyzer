import { describe, it, expect, vi } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import MessageTimeline from '../MessageTimeline';
import { renderWithProviders, mockMessage } from '../../../test/utils';

describe('MessageTimeline', () => {
  const mockMessages = [
    mockMessage({ id: '1', sender: 'Alice', content: 'Hello Bob!' }),
    mockMessage({ id: '2', sender: 'Bob', content: 'Hi Alice, how are you?' }),
    mockMessage({ id: '3', sender: 'Alice', content: 'I am doing great, thanks!' }),
    mockMessage({ id: '4', sender: 'Bob', content: 'That is wonderful to hear!' }),
    mockMessage({ id: '5', sender: 'Alice', content: 'How about you?' }),
  ];

  const defaultProps = {
    messages: mockMessages,
    loading: false,
    onLoadMore: vi.fn(),
    hasMore: false,
    searchQuery: '',
    onSearchChange: vi.fn(),
    selectedSender: '',
    onSenderChange: vi.fn(),
    participants: ['Alice', 'Bob'],
  };

  it('renders messages correctly', () => {
    renderWithProviders(<MessageTimeline {...defaultProps} />);
    
    // Check if all messages are rendered
    expect(screen.getByText('Hello Bob!')).toBeInTheDocument();
    expect(screen.getByText('Hi Alice, how are you?')).toBeInTheDocument();
    expect(screen.getByText('I am doing great, thanks!')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    renderWithProviders(<MessageTimeline {...defaultProps} loading={true} />);
    
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('handles search input', async () => {
    const onSearchChange = vi.fn();
    renderWithProviders(
      <MessageTimeline {...defaultProps} onSearchChange={onSearchChange} />
    );
    
    const searchInput = screen.getByPlaceholderText('Search messages...');
    fireEvent.change(searchInput, { target: { value: 'hello' } });
    
    await waitFor(() => {
      expect(onSearchChange).toHaveBeenCalledWith('hello');
    });
  });

  it('filters messages by sender', () => {
    const onSenderChange = vi.fn();
    renderWithProviders(
      <MessageTimeline {...defaultProps} onSenderChange={onSenderChange} />
    );
    
    // Open sender filter
    const senderFilter = screen.getByLabelText('Filter by sender');
    fireEvent.mouseDown(senderFilter);
    
    // Select Alice
    const aliceOption = screen.getByText('Alice', { selector: 'li' });
    fireEvent.click(aliceOption);
    
    expect(onSenderChange).toHaveBeenCalledWith('Alice');
  });

  it('loads more messages when scrolling to top', async () => {
    const onLoadMore = vi.fn();
    renderWithProviders(
      <MessageTimeline {...defaultProps} hasMore={true} onLoadMore={onLoadMore} />
    );
    
    const scrollContainer = screen.getByTestId('message-list');
    
    // Simulate scroll to top
    fireEvent.scroll(scrollContainer, { target: { scrollTop: 0 } });
    
    await waitFor(() => {
      expect(onLoadMore).toHaveBeenCalled();
    });
  });

  it('groups messages by date', () => {
    const messagesWithDifferentDates = [
      mockMessage({
        id: '1',
        content: 'Yesterday message',
        timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      }),
      mockMessage({
        id: '2',
        content: 'Today message',
        timestamp: new Date().toISOString(),
      }),
    ];
    
    renderWithProviders(
      <MessageTimeline {...defaultProps} messages={messagesWithDifferentDates} />
    );
    
    // Should show date dividers
    expect(screen.getByText(/Yesterday/i)).toBeInTheDocument();
    expect(screen.getByText(/Today/i)).toBeInTheDocument();
  });

  it('highlights search results', () => {
    renderWithProviders(
      <MessageTimeline {...defaultProps} searchQuery="great" />
    );
    
    // Message containing "great" should be highlighted
    const highlightedMessage = screen.getByText(/great/i).closest('[data-testid="message-item"]');
    expect(highlightedMessage).toHaveStyle({ backgroundColor: expect.stringContaining('yellow') });
  });

  it('shows empty state when no messages', () => {
    renderWithProviders(<MessageTimeline {...defaultProps} messages={[]} />);
    
    expect(screen.getByText('No messages to display')).toBeInTheDocument();
  });

  it('handles message selection', () => {
    const onMessageSelect = vi.fn();
    renderWithProviders(
      <MessageTimeline {...defaultProps} onMessageSelect={onMessageSelect} />
    );
    
    const firstMessage = screen.getByText('Hello Bob!').closest('[data-testid="message-item"]');
    fireEvent.click(firstMessage!);
    
    expect(onMessageSelect).toHaveBeenCalledWith(mockMessages[0]);
  });

  it('displays message metadata correctly', () => {
    const messageWithMedia = mockMessage({
      id: '1',
      content: '<Media omitted>',
      message_type: 'media',
      metadata: { media_type: 'image', filename: 'photo.jpg' },
    });
    
    renderWithProviders(
      <MessageTimeline {...defaultProps} messages={[messageWithMedia]} />
    );
    
    expect(screen.getByText('📷 photo.jpg')).toBeInTheDocument();
  });
});