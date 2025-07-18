import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Box,
  Paper,
  Button,
  CircularProgress,
  Alert,
  Breadcrumbs,
  Link,
  Tabs,
  Tab,
  IconButton,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Share as ShareIcon,
  MoreVert as MoreVertIcon,
} from '@mui/icons-material';
import { useAppDispatch } from '../hooks/redux';
import AnalyticsCharts from '../components/analytics/AnalyticsCharts';
import type { ConversationAnalytics } from '../types/analytics.types';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`analytics-tabpanel-${index}`}
      aria-labelledby={`analytics-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

const AnalyticsPage: React.FC = () => {
  const { conversationId } = useParams<{ conversationId: string }>();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();

  const [analytics, setAnalytics] = useState<ConversationAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [refreshing, setRefreshing] = useState(false);

  // Load analytics data
  useEffect(() => {
    const loadAnalytics = async () => {
      if (!conversationId) return;

      try {
        setLoading(true);
        setError(null);

        // TODO: Replace with actual API call
        // const response = await analyticsService.getConversationAnalytics(conversationId);
        // setAnalytics(response);

        // Mock data for now
        const mockAnalytics: ConversationAnalytics = {
          conversation_id: conversationId,
          generated_at: new Date().toISOString(),
          processing_time_seconds: 2.5,
          total_messages: 1500,
          total_participants: 5,
          date_range: {
            start: '2023-01-01T00:00:00Z',
            end: '2024-01-01T00:00:00Z',
          },
          avg_messages_per_day: 4.1,
          sentiment_analysis: {
            overall_sentiment: {
              positive: 0.65,
              negative: 0.15,
              neutral: 0.20,
              compound: 0.50,
            },
            sentiment_by_participant: {},
            sentiment_timeline: [],
            most_positive_messages: [],
            most_negative_messages: [],
          },
          keyword_analysis: {
            top_keywords: [
              { keyword: 'hello', count: 150, frequency: 0.05 },
              { keyword: 'thanks', count: 120, frequency: 0.04 },
              { keyword: 'meeting', count: 100, frequency: 0.03 },
              { keyword: 'project', count: 90, frequency: 0.03 },
              { keyword: 'tomorrow', count: 80, frequency: 0.02 },
            ],
            keyword_trends: [],
            keyword_by_participant: {},
            word_cloud_data: [],
          },
          entity_analysis: {
            entities: {
              PERSON: [
                { text: 'John', count: 45, confidence: 0.95 },
                { text: 'Sarah', count: 38, confidence: 0.92 },
              ],
              LOCATION: [
                { text: 'New York', count: 12, confidence: 0.90 },
                { text: 'Office', count: 25, confidence: 0.88 },
              ],
              ORGANIZATION: [
                { text: 'Google', count: 8, confidence: 0.88 },
              ],
            },
            entity_frequency: {},
            entity_timeline: [],
          },
          timeline_analysis: {
            messages_by_hour: {
              '9': 120,
              '10': 150,
              '11': 180,
              '12': 100,
              '13': 90,
              '14': 160,
              '15': 200,
              '16': 180,
              '17': 150,
              '18': 120,
              '19': 80,
              '20': 70,
            },
            messages_by_day: {
              Monday: 234,
              Tuesday: 189,
              Wednesday: 256,
              Thursday: 298,
              Friday: 312,
              Saturday: 156,
              Sunday: 55,
            },
            messages_by_month: {},
            activity_heatmap: [],
            peak_hours: [15, 16, 11],
            peak_days: ['Friday', 'Thursday', 'Wednesday'],
            response_time_analysis: {
              avg_response_time: 5.2,
              median_response_time: 3.8,
              by_participant: {},
            },
          },
          participant_analytics: [
            {
              participant_id: '1',
              phone_number: '+1234567890',
              display_name: 'John Doe',
              message_count: 450,
              avg_message_length: 45.2,
              response_time_avg: 4.5,
              active_hours: [9, 10, 11, 14, 15, 16],
              emoji_usage: { '😊': 25, '👍': 18, '😂': 15 },
              media_shared: { image: 12, video: 3 },
              sentiment_score: {
                positive: 0.70,
                negative: 0.10,
                neutral: 0.20,
                compound: 0.60,
              },
              top_keywords: [
                { keyword: 'project', count: 25 },
                { keyword: 'meeting', count: 20 },
              ],
            },
            {
              participant_id: '2',
              phone_number: '+1234567891',
              display_name: 'Jane Smith',
              message_count: 380,
              avg_message_length: 52.8,
              response_time_avg: 6.2,
              active_hours: [10, 11, 14, 15, 16, 17],
              emoji_usage: { '😊': 30, '❤️': 22, '🎉': 18 },
              media_shared: { image: 8, document: 5 },
              sentiment_score: {
                positive: 0.75,
                negative: 0.08,
                neutral: 0.17,
                compound: 0.67,
              },
              top_keywords: [
                { keyword: 'thanks', count: 30 },
                { keyword: 'great', count: 25 },
              ],
            },
          ],
          media_stats: {
            image: 45,
            video: 12,
            audio: 8,
            document: 15,
          },
          link_stats: {
            total_links: 67,
            unique_domains: 23,
            top_domains: [
              { domain: 'youtube.com', count: 15 },
              { domain: 'github.com', count: 12 },
            ],
          },
        };

        setAnalytics(mockAnalytics);
      } catch (err) {
        setError('Failed to load analytics');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadAnalytics();
  }, [conversationId]);

  const handleRefresh = async () => {
    setRefreshing(true);
    // TODO: Implement analytics refresh
    setTimeout(() => setRefreshing(false), 2000);
  };

  const handleExport = () => {
    // TODO: Implement analytics export
    console.log('Export analytics');
    setAnchorEl(null);
  };

  const handleShare = () => {
    // TODO: Implement analytics sharing
    console.log('Share analytics');
    setAnchorEl(null);
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

  if (error || !analytics) {
    return (
      <Container maxWidth="lg">
        <Box mt={4}>
          <Alert severity="error">{error || 'Analytics not found'}</Alert>
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
        <Link
          component="button"
          variant="body2"
          onClick={() => navigate(`/conversations/${conversationId}`)}
          underline="hover"
        >
          Conversation Detail
        </Link>
        <Typography variant="body2" color="text.primary">
          Analytics
        </Typography>
      </Breadcrumbs>

      {/* Header */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box display="flex" alignItems="center" gap={1}>
            <IconButton onClick={() => navigate(`/conversations/${conversationId}`)} size="small">
              <ArrowBackIcon />
            </IconButton>
            <Box>
              <Typography variant="h5">Conversation Analytics</Typography>
              <Typography variant="body2" color="text.secondary">
                Generated {new Date(analytics.generated_at).toLocaleString()}
              </Typography>
            </Box>
          </Box>
          <Box display="flex" gap={1}>
            <Button
              startIcon={<RefreshIcon />}
              variant="outlined"
              onClick={handleRefresh}
              disabled={refreshing}
            >
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </Button>
            <IconButton onClick={(e) => setAnchorEl(e.currentTarget)}>
              <MoreVertIcon />
            </IconButton>
          </Box>
        </Box>
      </Paper>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
          <Tab label="Overview" />
          <Tab label="Sentiment" />
          <Tab label="Keywords" />
          <Tab label="Timeline" />
          <Tab label="Participants" />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      <TabPanel value={tabValue} index={0}>
        <AnalyticsCharts analytics={analytics} />
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Sentiment Analysis Details
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Detailed sentiment analysis visualization coming soon...
          </Typography>
        </Paper>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Keyword Analysis Details
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Detailed keyword analysis and word cloud coming soon...
          </Typography>
        </Paper>
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Timeline Analysis Details
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Detailed timeline and activity patterns coming soon...
          </Typography>
        </Paper>
      </TabPanel>

      <TabPanel value={tabValue} index={4}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Participant Analysis Details
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Detailed participant statistics and comparisons coming soon...
          </Typography>
        </Paper>
      </TabPanel>

      {/* Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={() => setAnchorEl(null)}
      >
        <MenuItem onClick={handleExport}>
          <DownloadIcon fontSize="small" sx={{ mr: 1 }} />
          Export Analytics
        </MenuItem>
        <MenuItem onClick={handleShare}>
          <ShareIcon fontSize="small" sx={{ mr: 1 }} />
          Share Analytics
        </MenuItem>
      </Menu>
    </Container>
  );
};

export default AnalyticsPage;