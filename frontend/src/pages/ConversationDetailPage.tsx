import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Box,
  Paper,
  Button,
  IconButton,
  Chip,
  CircularProgress,
  Alert,
  Breadcrumbs,
  Link,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Download as DownloadIcon,
  Analytics as AnalyticsIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import conversationService from '../services/conversation.service';
import MessageTimeline from '../components/conversation/MessageTimeline';
import type { ConversationDetail, Message} from '../types/conversation.types';

const ConversationDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();  
  const [conversation, setConversation] = useState<ConversationDetail | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [exportFormat, setExportFormat] = useState<'pdf' | 'csv' | 'json'>('pdf');
  const [bookmarkDialogOpen, setBookmarkDialogOpen] = useState(false);
  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(null);
  const [bookmarkTitle, setBookmarkTitle] = useState('');
  const [bookmarkDescription, setBookmarkDescription] = useState('');

  // Load conversation details
  useEffect(() => {
    const loadConversation = async () => {
      if (!id) return;
      
      try {
        setLoading(true);
        setError(null);
        
        // Load conversation details
        const convResponse = await conversationService.getConversation(id);
        setConversation(convResponse);
        
        // Load messages
        const messagesResponse = await conversationService.getMessages(id, {
          page: 1,
          limit: 1000, // Load all messages for now
        });
        setMessages(messagesResponse.items);
      } catch (err) {
        setError('Failed to load conversation');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadConversation();
  }, [id]);

  const handleExport = async () => {
    if (!id) return;
    
    try {
      await conversationService.exportConversation(id, {
        format: exportFormat,
        options: {
          include_media: false,
          include_analytics: conversation?.analytics_available || false,
        },
      });
      
      // Show success message
      setExportDialogOpen(false);
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  const handleBookmarkMessage = (messageId: string) => {
    setSelectedMessageId(messageId);
    setBookmarkDialogOpen(true);
  };

  const handleCreateBookmark = async () => {
    if (!selectedMessageId) return;
    
    try {
      // TODO: Implement bookmark creation
      console.log('Creating bookmark:', {
        messageId: selectedMessageId,
        title: bookmarkTitle,
        description: bookmarkDescription,
      });
      
      setBookmarkDialogOpen(false);
      setBookmarkTitle('');
      setBookmarkDescription('');
      setSelectedMessageId(null);
    } catch (err) {
      console.error('Failed to create bookmark:', err);
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg">
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error || !conversation) {
    return (
      <Container maxWidth="lg">
        <Box mt={4}>
          <Alert severity="error">{error || 'Conversation not found'}</Alert>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/conversations')}
            sx={{ mt: 2 }}
          >
            Back to Conversations
          </Button>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      {/* Breadcrumbs */}
      <Breadcrumbs sx={{ mb: 2 }}>
        <Link
          component="button"
          variant="body2"
          onClick={() => navigate('/dashboard')}
          underline="hover"
        >
          Dashboard
        </Link>
        <Link
          component="button"
          variant="body2"
          onClick={() => navigate('/conversations')}
          underline="hover"
        >
          Conversations
        </Link>
        <Typography variant="body2" color="text.primary">
          {conversation.title}
        </Typography>
      </Breadcrumbs>

      {/* Header */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
          <Box display="flex" alignItems="center" gap={1}>
            <IconButton onClick={() => navigate('/conversations')} size="small">
              <ArrowBackIcon />
            </IconButton>
            <Box>
              <Typography variant="h5">{conversation.title}</Typography>
              <Box display="flex" gap={1} mt={0.5}>
                <Chip
                  label={`${conversation.message_count} messages`}
                  size="small"
                  variant="outlined"
                />
                <Chip
                  label={`${conversation.participant_count} participants`}
                  size="small"
                  variant="outlined"
                />
                {conversation.analytics_available && (
                  <Chip
                    label="Analytics available"
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                )}
              </Box>
            </Box>
          </Box>
          <Box display="flex" gap={1}>
            <Button
              startIcon={<SearchIcon />}
              variant="outlined"
              onClick={() => navigate(`/search?conversation=${id}`)}
            >
              Search
            </Button>
            {conversation.analytics_available && (
              <Button
                startIcon={<AnalyticsIcon />}
                variant="outlined"
                onClick={() => navigate(`/analytics/${id}`)}
              >
                Analytics
              </Button>
            )}
            <Button
              startIcon={<DownloadIcon />}
              variant="outlined"
              onClick={() => setExportDialogOpen(true)}
            >
              Export
            </Button>
          </Box>
        </Box>
      </Paper>

      {/* Message Timeline */}
      <Paper sx={{ height: 'calc(100vh - 300px)', display: 'flex', flexDirection: 'column' }}>
        <MessageTimeline
          conversationId={id!}
          messages={messages}
          participants={conversation.participants}
          loading={loading}
          onBookmarkMessage={handleBookmarkMessage}
        />
      </Paper>

      {/* Export Dialog */}
      <Dialog open={exportDialogOpen} onClose={() => setExportDialogOpen(false)}>
        <DialogTitle>Export Conversation</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Format</InputLabel>
            <Select
              value={exportFormat}
              onChange={(e) => setExportFormat(e.target.value as 'pdf' | 'csv' | 'json')}
              label="Format"
            >
              <MenuItem value="pdf">PDF</MenuItem>
              <MenuItem value="csv">CSV</MenuItem>
              <MenuItem value="json">JSON</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleExport} variant="contained">
            Export
          </Button>
        </DialogActions>
      </Dialog>

      {/* Bookmark Dialog */}
      <Dialog open={bookmarkDialogOpen} onClose={() => setBookmarkDialogOpen(false)}>
        <DialogTitle>Create Bookmark</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Title"
            value={bookmarkTitle}
            onChange={(e) => setBookmarkTitle(e.target.value)}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Description"
            value={bookmarkDescription}
            onChange={(e) => setBookmarkDescription(e.target.value)}
            margin="normal"
            multiline
            rows={3}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBookmarkDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleCreateBookmark}
            variant="contained"
            disabled={!bookmarkTitle}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default ConversationDetailPage;