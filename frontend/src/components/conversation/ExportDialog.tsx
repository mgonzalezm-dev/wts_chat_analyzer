import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Box,
  Typography,
  Alert,
  LinearProgress,
  Chip,
  Stack,
} from '@mui/material';
import {
  Download as DownloadIcon,
  PictureAsPdf as PdfIcon,
  TableChart as CsvIcon,
  Code as JsonIcon,
  TextFields as TxtIcon,
  Html as HtmlIcon,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import type { ExportRequest } from '../../types/conversation.types';
import conversationService from '../../services/conversation.service';

interface ExportDialogProps {
  open: boolean;
  onClose: () => void;
  conversationId: string;
  conversationTitle: string;
  participants?: Array<{ id: string; display_name: string; phone_number: string }>;
}

const formatIcons = {
  pdf: <PdfIcon />,
  csv: <CsvIcon />,
  json: <JsonIcon />,
};

const ExportDialog: React.FC<ExportDialogProps> = ({
  open,
  onClose,
  conversationId,
  conversationTitle,
  participants = [],
}) => {
  const [format, setFormat] = useState<'pdf' | 'csv' | 'json'>('pdf');
  const [includeMedia, setIncludeMedia] = useState(false);
  const [includeAnalytics, setIncludeAnalytics] = useState(false);
  const [includeMetadata, setIncludeMetadata] = useState(true);
  const [dateFrom, setDateFrom] = useState<Date | null>(null);
  const [dateTo, setDateTo] = useState<Date | null>(null);
  const [selectedParticipants, setSelectedParticipants] = useState<string[]>([]);
  const [exporting, setExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [exportJobId, setExportJobId] = useState<string | null>(null);

  const handleExport = async () => {
    try {
      setExporting(true);
      setError(null);
      setExportProgress(0);

      const exportRequest: ExportRequest = {
        format,
        filters: {
          date_from: dateFrom?.toISOString(),
          date_to: dateTo?.toISOString(),
          participants: selectedParticipants.length > 0 ? selectedParticipants : undefined,
        },
        options: {
          include_media: includeMedia,
          include_analytics: includeAnalytics,
        },
      };

      // Start export job
      const response = await conversationService.exportConversation(conversationId, exportRequest);
      setExportJobId(response.job_id);

      // Poll for export status
      const pollInterval = setInterval(async () => {
        try {
          const status = await conversationService.getExportStatus(response.job_id);
          setExportProgress(status.progress);

          if (status.status === 'completed' && status.download_url) {
            clearInterval(pollInterval);
            // Download the file
            window.open(status.download_url, '_blank');
            setExporting(false);
            onClose();
          } else if (status.status === 'failed') {
            clearInterval(pollInterval);
            setError('Export failed. Please try again.');
            setExporting(false);
          }
        } catch (err) {
          clearInterval(pollInterval);
          setError('Failed to check export status');
          setExporting(false);
        }
      }, 2000);
    } catch (err) {
      setError('Failed to start export');
      setExporting(false);
    }
  };

  const getFormatDescription = (fmt: string) => {
    switch (fmt) {
      case 'pdf':
        return 'Best for printing and sharing. Includes formatting and optional charts.';
      case 'csv':
        return 'Spreadsheet format. Good for data analysis in Excel or Google Sheets.';
      case 'json':
        return 'Machine-readable format. Ideal for developers and data processing.';
      default:
        return '';
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        Export Conversation
        <Typography variant="body2" color="text.secondary">
          {conversationTitle}
        </Typography>
      </DialogTitle>
      
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {exporting ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="h6" gutterBottom>
              Exporting conversation...
            </Typography>
            <LinearProgress
              variant="determinate"
              value={exportProgress}
              sx={{ mb: 2 }}
            />
            <Typography variant="body2" color="text.secondary">
              {exportProgress}% complete
            </Typography>
          </Box>
        ) : (
          <Stack spacing={3}>
            {/* Format Selection */}
            <FormControl fullWidth>
              <InputLabel>Export Format</InputLabel>
              <Select
                value={format}
                onChange={(e) => setFormat(e.target.value as any)}
                label="Export Format"
              >
                {Object.entries(formatIcons).map(([key, icon]) => (
                  <MenuItem key={key} value={key}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {icon}
                      <Box>
                        <Typography variant="body2">{key.toUpperCase()}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {getFormatDescription(key)}
                        </Typography>
                      </Box>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Date Range */}
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <DatePicker
                  label="From Date"
                  value={dateFrom}
                  onChange={setDateFrom}
                  slotProps={{ textField: { fullWidth: true } }}
                />
                <DatePicker
                  label="To Date"
                  value={dateTo}
                  onChange={setDateTo}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </Box>
            </LocalizationProvider>

            {/* Participant Filter */}
            {participants.length > 0 && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Filter by Participants
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {participants.map((participant) => (
                    <Chip
                      key={participant.id}
                      label={participant.display_name || participant.phone_number}
                      onClick={() => {
                        setSelectedParticipants((prev) =>
                          prev.includes(participant.id)
                            ? prev.filter((id) => id !== participant.id)
                            : [...prev, participant.id]
                        );
                      }}
                      color={selectedParticipants.includes(participant.id) ? 'primary' : 'default'}
                      variant={selectedParticipants.includes(participant.id) ? 'filled' : 'outlined'}
                    />
                  ))}
                </Box>
              </Box>
            )}

            {/* Options */}
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Export Options
              </Typography>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={includeMedia}
                    onChange={(e) => setIncludeMedia(e.target.checked)}
                    disabled={format === 'csv'}
                  />
                }
                label="Include media files"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={includeAnalytics}
                    onChange={(e) => setIncludeAnalytics(e.target.checked)}
                    disabled={false}
                  />
                }
                label="Include analytics data"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={includeMetadata}
                    onChange={(e) => setIncludeMetadata(e.target.checked)}
                  />
                }
                label="Include message metadata"
              />
            </Box>

            {/* Format-specific notes */}
            {format === 'pdf' && (
              <Alert severity="info">
                PDF exports include formatting, emojis, and optional charts. Large conversations may take longer to process.
              </Alert>
            )}
            {format === 'csv' && (
              <Alert severity="info">
                CSV format exports message data in a tabular format. Media and formatting will not be included.
              </Alert>
            )}
          </Stack>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} disabled={exporting}>
          Cancel
        </Button>
        <Button
          onClick={handleExport}
          variant="contained"
          startIcon={<DownloadIcon />}
          disabled={exporting}
        >
          Export
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ExportDialog;