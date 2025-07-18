import { describe, it, expect, vi } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import ExportDialog from '../ExportDialog';
import { renderWithProviders } from '../../../test/utils';

describe('ExportDialog', () => {
  const defaultProps = {
    open: true,
    onClose: vi.fn(),
    conversationId: 'test-conversation-id',
    conversationName: 'Test Conversation',
  };

  it('renders dialog when open', () => {
    renderWithProviders(<ExportDialog {...defaultProps} />);
    
    expect(screen.getByText('Export Conversation')).toBeInTheDocument();
    expect(screen.getByText(/Choose export format and options/)).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    renderWithProviders(<ExportDialog {...defaultProps} open={false} />);
    
    expect(screen.queryByText('Export Conversation')).not.toBeInTheDocument();
  });

  it('displays all export format options', () => {
    renderWithProviders(<ExportDialog {...defaultProps} />);
    
    expect(screen.getByLabelText('PDF Document')).toBeInTheDocument();
    expect(screen.getByLabelText('CSV Spreadsheet')).toBeInTheDocument();
    expect(screen.getByLabelText('JSON Data')).toBeInTheDocument();
    expect(screen.getByLabelText('Text File')).toBeInTheDocument();
    expect(screen.getByLabelText('HTML Document')).toBeInTheDocument();
  });

  it('allows format selection', () => {
    renderWithProviders(<ExportDialog {...defaultProps} />);
    
    const csvOption = screen.getByLabelText('CSV Spreadsheet');
    fireEvent.click(csvOption);
    
    expect(csvOption).toBeChecked();
  });

  it('displays export options', () => {
    renderWithProviders(<ExportDialog {...defaultProps} />);
    
    expect(screen.getByLabelText('Include media files')).toBeInTheDocument();
    expect(screen.getByLabelText('Include analytics')).toBeInTheDocument();
    expect(screen.getByLabelText('Include timestamps')).toBeInTheDocument();
    expect(screen.getByLabelText('Include participant info')).toBeInTheDocument();
  });

  it('allows toggling export options', () => {
    renderWithProviders(<ExportDialog {...defaultProps} />);
    
    const includeMedia = screen.getByLabelText('Include media files');
    expect(includeMedia).not.toBeChecked();
    
    fireEvent.click(includeMedia);
    expect(includeMedia).toBeChecked();
  });

  it('allows date range selection', () => {
    renderWithProviders(<ExportDialog {...defaultProps} />);
    
    const dateRangeCheckbox = screen.getByLabelText('Export specific date range');
    fireEvent.click(dateRangeCheckbox);
    
    expect(screen.getByLabelText('Start Date')).toBeInTheDocument();
    expect(screen.getByLabelText('End Date')).toBeInTheDocument();
  });

  it('calls onClose when cancel is clicked', () => {
    const onClose = vi.fn();
    renderWithProviders(<ExportDialog {...defaultProps} onClose={onClose} />);
    
    fireEvent.click(screen.getByText('Cancel'));
    expect(onClose).toHaveBeenCalled();
  });

  it('submits export request with correct data', async () => {
    // Mock the export API call
    const mockExport = vi.fn().mockResolvedValue({ data: { id: 'export-123' } });
    vi.mock('../../../services/api', () => ({
      exportService: {
        createExport: mockExport,
      },
    }));
    
    renderWithProviders(<ExportDialog {...defaultProps} />);
    
    // Select CSV format
    fireEvent.click(screen.getByLabelText('CSV Spreadsheet'));
    
    // Enable some options
    fireEvent.click(screen.getByLabelText('Include analytics'));
    fireEvent.click(screen.getByLabelText('Include timestamps'));
    
    // Click export
    fireEvent.click(screen.getByText('Export'));
    
    await waitFor(() => {
      expect(mockExport).toHaveBeenCalledWith({
        conversation_id: 'test-conversation-id',
        format: 'csv',
        options: {
          include_media: false,
          include_analytics: true,
          include_timestamps: true,
          include_participants: false,
        },
      });
    });
  });

  it('shows loading state during export', async () => {
    const mockExport = vi.fn().mockImplementation(() => 
      new Promise(resolve => setTimeout(resolve, 100))
    );
    vi.mock('../../../services/api', () => ({
      exportService: {
        createExport: mockExport,
      },
    }));
    
    renderWithProviders(<ExportDialog {...defaultProps} />);
    
    fireEvent.click(screen.getByText('Export'));
    
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('shows error message on export failure', async () => {
    const mockExport = vi.fn().mockRejectedValue(new Error('Export failed'));
    vi.mock('../../../services/api', () => ({
      exportService: {
        createExport: mockExport,
      },
    }));
    
    renderWithProviders(<ExportDialog {...defaultProps} />);
    
    fireEvent.click(screen.getByText('Export'));
    
    await waitFor(() => {
      expect(screen.getByText(/Export failed/)).toBeInTheDocument();
    });
  });

  it('disables media option for text format', () => {
    renderWithProviders(<ExportDialog {...defaultProps} />);
    
    // Select text format
    fireEvent.click(screen.getByLabelText('Text File'));
    
    const includeMedia = screen.getByLabelText('Include media files');
    expect(includeMedia).toBeDisabled();
  });

  it('shows format-specific options', () => {
    renderWithProviders(<ExportDialog {...defaultProps} />);
    
    // Select PDF format
    fireEvent.click(screen.getByLabelText('PDF Document'));
    
    // PDF should have page size option
    expect(screen.getByText(/Page size/)).toBeInTheDocument();
  });
});