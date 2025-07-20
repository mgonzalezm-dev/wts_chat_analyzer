import React, { useEffect, useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  LinearProgress,
  Button,
} from '@mui/material';
import {
  Chat as ChatIcon,
  People as PeopleIcon,
  Message as MessageIcon,
  TrendingUp as TrendingUpIcon,
  CloudUpload as UploadIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../hooks/redux';
import { fetchConversations } from '../store/slices/conversationSlice';
import type { DashboardStats } from '../types/analytics.types';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon, color }) => (
  <Card>
    <CardContent>
      <Box display="flex" alignItems="center" justifyContent="space-between">
        <Box>
          <Typography color="textSecondary" gutterBottom variant="body2">
            {title}
          </Typography>
          <Typography variant="h4" component="div">
            {value}
          </Typography>
        </Box>
        <Box
          sx={{
            backgroundColor: color,
            borderRadius: '50%',
            width: 56,
            height: 56,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {icon}
        </Box>
      </Box>
    </CardContent>
  </Card>
);

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { conversations, isLoading } = useAppSelector(state => state.conversation);
  const [stats, setStats] = useState<DashboardStats>({
    total_conversations: 0,
    total_messages: 0,
    total_participants: 0,
    active_conversations: 0,
    date_range: {
      from: new Date().toISOString(),
      to: new Date().toISOString(),
    },
  });

  useEffect(() => {
    // Fetch conversations
    dispatch(fetchConversations({ page: 1, limit: 10 }));
  }, [dispatch]);

  useEffect(() => {
    // Calculate stats from conversations
    if (conversations.length > 0) {
      const totalMessages = conversations.reduce((sum, conv) => sum + conv.message_count, 0);
      const totalParticipants = conversations.reduce((sum, conv) => sum + conv.participant_count, 0);
      const activeConversations = conversations.filter(conv => conv.status === 'ready').length;

      setStats({
        total_conversations: conversations.length,
        total_messages: totalMessages,
        total_participants: totalParticipants,
        active_conversations: activeConversations,
        date_range: {
          from: new Date().toISOString(),
          to: new Date().toISOString(),
        },
      });
    }
  }, [conversations]);

  const recentConversations = conversations.slice(0, 5);

  return (
    <Container maxWidth="lg">
      <Box mb={4}>
        <Typography variant="h4" gutterBottom>
          Dashboard
        </Typography>
        <Typography variant="body1" color="textSecondary">
          Welcome back! Here's an overview of your WhatsApp conversations.
        </Typography>
      </Box>

      {isLoading && <LinearProgress sx={{ mb: 2 }} />}

      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: 3 }}>
        {/* Statistics Cards */}
        <Box sx={{ gridColumn: { xs: 'span 12', sm: 'span 6', md: 'span 3' }, p: 1.5 }}>
          <StatCard
            title="Total Conversations"
            value={stats.total_conversations}
            icon={<ChatIcon sx={{ color: 'white' }} />}
            color="#1976d2"
          />
        </Box>
        <Box sx={{ gridColumn: { xs: 'span 12', sm: 'span 6', md: 'span 3' }, p: 1.5 }}>
          <StatCard
            title="Total Messages"
            value={stats.total_messages.toLocaleString()}
            icon={<MessageIcon sx={{ color: 'white' }} />}
            color="#388e3c"
          />
        </Box>
        <Box sx={{ gridColumn: { xs: 'span 12', sm: 'span 6', md: 'span 3' }, p: 1.5 }}>
          <StatCard
            title="Total Participants"
            value={stats.total_participants}
            icon={<PeopleIcon sx={{ color: 'white' }} />}
            color="#f57c00"
          />
        </Box>
        <Box sx={{ gridColumn: { xs: 'span 12', sm: 'span 6', md: 'span 3' }, p: 1.5 }}>
          <StatCard
            title="Active Conversations"
            value={stats.active_conversations}
            icon={<TrendingUpIcon sx={{ color: 'white' }} />}
            color="#7b1fa2"
          />
        </Box>

        {/* Quick Actions */}
        <Box sx={{ gridColumn: { xs: 'span 12', md: 'span 6' }, p: 1.5 }}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Box display="flex" flexDirection="column" gap={2}>
              <Button
                variant="contained"
                startIcon={<UploadIcon />}
                onClick={() => navigate('/conversations?action=import')}
                fullWidth
              >
                Import New Conversation
              </Button>
              <Button
                variant="outlined"
                startIcon={<ChatIcon />}
                onClick={() => navigate('/conversations')}
                fullWidth
              >
                View All Conversations
              </Button>
            </Box>
          </Paper>
        </Box>

        {/* Recent Conversations */}
        <Box sx={{ gridColumn: { xs: 'span 12', md: 'span 6' }, p: 1.5 }}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                Recent Conversations
              </Typography>
              <Button size="small" onClick={() => navigate('/conversations')}>
                View All
              </Button>
            </Box>
            {recentConversations.length === 0 ? (
              <Box textAlign="center" py={4}>
                <Typography color="textSecondary">
                  No conversations yet
                </Typography>
                <Button
                  variant="text"
                  startIcon={<AddIcon />}
                  onClick={() => navigate('/conversations?action=import')}
                  sx={{ mt: 2 }}
                >
                  Import your first conversation
                </Button>
              </Box>
            ) : (
              <Box display="flex" flexDirection="column" gap={1}>
                {recentConversations.map((conv) => (
                  <Box
                    key={conv.id}
                    sx={{
                      p: 2,
                      border: '1px solid',
                      borderColor: 'divider',
                      borderRadius: 1,
                      cursor: 'pointer',
                      '&:hover': {
                        backgroundColor: 'action.hover',
                      },
                    }}
                    onClick={() => navigate(`/conversations/${conv.id}`)}
                  >
                    <Typography variant="subtitle1">{conv.title}</Typography>
                    <Typography variant="body2" color="textSecondary">
                      {conv.message_count} messages • {conv.participant_count} participants
                    </Typography>
                  </Box>
                ))}
              </Box>
            )}
          </Paper>
        </Box>
      </Box>
    </Container>
  );
};

export default DashboardPage;