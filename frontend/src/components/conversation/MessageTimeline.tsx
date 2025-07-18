import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Avatar,
  IconButton,
  TextField,
  InputAdornment,
  Chip,
  CircularProgress,
  Divider,
  Menu,
  MenuItem,
  Tooltip,
  Fab,
} from '@mui/material';
import {
  Search as SearchIcon,
  Bookmark as BookmarkIcon,
  BookmarkBorder as BookmarkBorderIcon,
  MoreVert as MoreVertIcon,
  Reply as ReplyIcon,
  Delete as DeleteIcon,
  ContentCopy as CopyIcon,
  KeyboardArrowDown as ScrollDownIcon,
  Image as ImageIcon,
  VideoLibrary as VideoIcon,
  AudioFile as AudioIcon,
  Description as DocumentIcon,
  LocationOn as LocationIcon,
  Contacts as ContactIcon,
} from '@mui/icons-material';
import { format, isToday, isYesterday, parseISO } from 'date-fns';
import type { Message, Participant } from '../../types/conversation.types';
import { useAppDispatch } from '../../hooks/redux';

interface MessageTimelineProps {
  conversationId: string;
  messages: Message[];
  participants: Participant[];
  loading?: boolean;
  onBookmarkMessage?: (messageId: string) => void;
  onDeleteMessage?: (messageId: string) => void;
  onReplyToMessage?: (message: Message) => void;
}

interface MessageGroup {
  date: string;
  messages: Message[];
}

const MessageTimeline: React.FC<MessageTimelineProps> = ({
  conversationId,
  messages,
  participants,
  loading = false,
  onBookmarkMessage,
  onDeleteMessage,
  onReplyToMessage,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredMessages, setFilteredMessages] = useState<Message[]>(messages);
  const [selectedMessage, setSelectedMessage] = useState<string | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Group messages by date
  const groupMessagesByDate = useCallback((msgs: Message[]): MessageGroup[] => {
    const groups: { [key: string]: Message[] } = {};

    msgs.forEach((message) => {
      const date = format(parseISO(message.timestamp), 'yyyy-MM-dd');
      if (!groups[date]) {
        groups[date] = [];
      }
      groups[date].push(message);
    });

    return Object.entries(groups)
      .map(([date, msgs]) => ({ date, messages: msgs }))
      .sort((a, b) => a.date.localeCompare(b.date));
  }, []);

  // Filter messages based on search
  useEffect(() => {
    if (searchQuery) {
      const filtered = messages.filter((msg) =>
        msg.content.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setFilteredMessages(filtered);
    } else {
      setFilteredMessages(messages);
    }
  }, [searchQuery, messages]);

  // Scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Handle scroll to show/hide scroll button
  const handleScroll = () => {
    if (scrollContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
      setShowScrollButton(scrollHeight - scrollTop - clientHeight > 100);
    }
  };

  // Get participant info
  const getParticipant = (participantId: string): Participant | undefined => {
    return participants.find((p) => p.id === participantId);
  };

  // Format date header
  const formatDateHeader = (dateStr: string): string => {
    const date = parseISO(dateStr);
    if (isToday(date)) return 'Today';
    if (isYesterday(date)) return 'Yesterday';
    return format(date, 'MMMM d, yyyy');
  };

  // Get message type icon
  const getMessageTypeIcon = (type: string) => {
    switch (type) {
      case 'image':
        return <ImageIcon fontSize="small" />;
      case 'video':
        return <VideoIcon fontSize="small" />;
      case 'audio':
        return <AudioIcon fontSize="small" />;
      case 'document':
        return <DocumentIcon fontSize="small" />;
      case 'location':
        return <LocationIcon fontSize="small" />;
      case 'contact':
        return <ContactIcon fontSize="small" />;
      default:
        return null;
    }
  };

  // Handle message menu
  const handleMessageMenu = (event: React.MouseEvent<HTMLElement>, messageId: string) => {
    setAnchorEl(event.currentTarget);
    setSelectedMessage(messageId);
  };

  const handleCloseMenu = () => {
    setAnchorEl(null);
    setSelectedMessage(null);
  };

  // Copy message content
  const handleCopyMessage = () => {
    const message = messages.find((m) => m.id === selectedMessage);
    if (message) {
      navigator.clipboard.writeText(message.content);
    }
    handleCloseMenu();
  };

  const messageGroups = groupMessagesByDate(filteredMessages);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100%">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Search Bar */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <TextField
          fullWidth
          size="small"
          placeholder="Search messages..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
        />
      </Box>

      {/* Messages Container */}
      <Box
        ref={scrollContainerRef}
        onScroll={handleScroll}
        sx={{
          flex: 1,
          overflowY: 'auto',
          p: 2,
          backgroundColor: 'background.default',
        }}
      >
        {messageGroups.map((group) => (
          <Box key={group.date}>
            {/* Date Header */}
            <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
              <Chip
                label={formatDateHeader(group.date)}
                size="small"
                sx={{ backgroundColor: 'background.paper' }}
              />
            </Box>

            {/* Messages */}
            {group.messages.map((message) => {
              const participant = getParticipant(message.sender_id);
              const isDeleted = message.is_deleted;

              return (
                <Box
                  key={message.id}
                  sx={{
                    display: 'flex',
                    mb: 2,
                    alignItems: 'flex-start',
                  }}
                >
                  {/* Avatar */}
                  <Avatar
                    sx={{
                      width: 40,
                      height: 40,
                      mr: 1,
                      bgcolor: 'primary.main',
                    }}
                  >
                    {participant?.display_name?.[0] || participant?.phone_number?.[0] || '?'}
                  </Avatar>

                  {/* Message Content */}
                  <Paper
                    elevation={1}
                    sx={{
                      flex: 1,
                      p: 1.5,
                      backgroundColor: isDeleted ? 'action.disabledBackground' : 'background.paper',
                    }}
                  >
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="subtitle2" color="primary">
                        {participant?.display_name || participant?.phone_number || 'Unknown'}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <Typography variant="caption" color="text.secondary">
                          {format(parseISO(message.timestamp), 'HH:mm')}
                        </Typography>
                        <IconButton
                          size="small"
                          onClick={(e) => handleMessageMenu(e, message.id)}
                        >
                          <MoreVertIcon fontSize="small" />
                        </IconButton>
                      </Box>
                    </Box>

                    {/* Message Type Icon */}
                    {message.message_type !== 'text' && (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                        {getMessageTypeIcon(message.message_type)}
                        <Typography variant="caption" color="text.secondary">
                          {message.message_type}
                        </Typography>
                      </Box>
                    )}

                    {/* Message Text */}
                    <Typography
                      variant="body2"
                      sx={{
                        fontStyle: isDeleted ? 'italic' : 'normal',
                        color: isDeleted ? 'text.disabled' : 'text.primary',
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                      }}
                    >
                      {isDeleted ? 'This message was deleted' : message.content}
                    </Typography>

                    {/* Reply To */}
                    {message.reply_to_id && (
                      <Box
                        sx={{
                          mt: 1,
                          p: 1,
                          borderLeft: 3,
                          borderColor: 'primary.main',
                          backgroundColor: 'action.hover',
                        }}
                      >
                        <Typography variant="caption" color="text.secondary">
                          Replying to a message
                        </Typography>
                      </Box>
                    )}

                    {/* Edited Indicator */}
                    {message.is_edited && (
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                        (edited)
                      </Typography>
                    )}
                  </Paper>
                </Box>
              );
            })}
          </Box>
        ))}

        {/* Scroll anchor */}
        <div ref={messagesEndRef} />
      </Box>

      {/* Scroll to bottom button */}
      {showScrollButton && (
        <Fab
          size="small"
          color="primary"
          onClick={scrollToBottom}
          sx={{
            position: 'absolute',
            bottom: 16,
            right: 16,
          }}
        >
          <ScrollDownIcon />
        </Fab>
      )}

      {/* Message Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleCloseMenu}
      >
        <MenuItem onClick={handleCopyMessage}>
          <CopyIcon fontSize="small" sx={{ mr: 1 }} />
          Copy
        </MenuItem>
        {onBookmarkMessage && (
          <MenuItem
            onClick={() => {
              if (selectedMessage) onBookmarkMessage(selectedMessage);
              handleCloseMenu();
            }}
          >
            <BookmarkBorderIcon fontSize="small" sx={{ mr: 1 }} />
            Bookmark
          </MenuItem>
        )}
        {onReplyToMessage && (
          <MenuItem
            onClick={() => {
              const message = messages.find((m) => m.id === selectedMessage);
              if (message) onReplyToMessage(message);
              handleCloseMenu();
            }}
          >
            <ReplyIcon fontSize="small" sx={{ mr: 1 }} />
            Reply
          </MenuItem>
        )}
        {onDeleteMessage && (
          <MenuItem
            onClick={() => {
              if (selectedMessage) onDeleteMessage(selectedMessage);
              handleCloseMenu();
            }}
          >
            <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
            Delete
          </MenuItem>
        )}
      </Menu>
    </Box>
  );
};

export default MessageTimeline;