import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Chip,
  useTheme,
} from '@mui/material';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';
import {
  SentimentSatisfied as PositiveIcon,
  SentimentDissatisfied as NegativeIcon,
  SentimentNeutral as NeutralIcon,
} from '@mui/icons-material';
import type { ConversationAnalytics } from '../../types/analytics.types';

interface AnalyticsChartsProps {
  analytics: ConversationAnalytics;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const AnalyticsCharts: React.FC<AnalyticsChartsProps> = ({ analytics }) => {
  const theme = useTheme();

  // Prepare data for charts
  const sentimentData = [
    { name: 'Positive', value: analytics.sentiment_analysis.overall_sentiment.positive * 100 },
    { name: 'Negative', value: analytics.sentiment_analysis.overall_sentiment.negative * 100 },
    { name: 'Neutral', value: analytics.sentiment_analysis.overall_sentiment.neutral * 100 },
  ];

  const messagesByHour = Object.entries(analytics.timeline_analysis.messages_by_hour).map(
    ([hour, count]) => ({
      hour: `${hour}:00`,
      messages: count,
    })
  );

  const messagesByDay = Object.entries(analytics.timeline_analysis.messages_by_day).map(
    ([day, count]) => ({
      day,
      messages: count,
    })
  );

  const topKeywords = analytics.keyword_analysis.top_keywords.slice(0, 10).map((kw: { keyword: string; count: number }) => ({
    word: kw.keyword,
    count: kw.count,
  }));

  const participantActivity = analytics.participant_analytics.map((p: any) => ({
    name: p.display_name || p.phone_number,
    messages: p.message_count,
    avgLength: Math.round(p.avg_message_length),
    sentiment: p.sentiment_score.compound,
  }));

  const mediaStats = Object.entries(analytics.media_stats).map(([type, count]) => ({
    type: type.charAt(0).toUpperCase() + type.slice(1),
    count,
  }));

  const getSentimentIcon = (sentiment: number) => {
    if (sentiment > 0.1) return <PositiveIcon color="success" />;
    if (sentiment < -0.1) return <NegativeIcon color="error" />;
    return <NeutralIcon color="warning" />;
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {/* Summary Cards */}
        <Box>
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 2 }}>
            <Box>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Total Messages
                  </Typography>
                  <Typography variant="h4">{analytics.total_messages}</Typography>
                  <Typography variant="body2" color="textSecondary">
                    {analytics.avg_messages_per_day.toFixed(1)} per day
                  </Typography>
                </CardContent>
              </Card>
            </Box>
            <Box>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Overall Sentiment
                  </Typography>
                  <Box display="flex" alignItems="center" gap={1}>
                    {getSentimentIcon(analytics.sentiment_analysis.overall_sentiment.compound)}
                    <Typography variant="h5">
                      {analytics.sentiment_analysis.overall_sentiment.compound > 0.1
                        ? 'Positive'
                        : analytics.sentiment_analysis.overall_sentiment.compound < -0.1
                        ? 'Negative'
                        : 'Neutral'}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Box>
            <Box>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Active Participants
                  </Typography>
                  <Typography variant="h4">{analytics.total_participants}</Typography>
                </CardContent>
              </Card>
            </Box>
            <Box>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Peak Activity
                  </Typography>
                  <Typography variant="h5">
                    {analytics.timeline_analysis.peak_hours[0]}:00
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    {analytics.timeline_analysis.peak_days[0]}
                  </Typography>
                </CardContent>
              </Card>
            </Box>
          </Box>
        </Box>

        {/* Charts Grid */}
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 3 }}>
          {/* Sentiment Analysis */}
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Sentiment Distribution
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={sentimentData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value?.toFixed(1) || 0}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {sentimentData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={
                        entry.name === 'Positive'
                          ? theme.palette.success.main
                          : entry.name === 'Negative'
                          ? theme.palette.error.main
                          : theme.palette.warning.main
                      }
                    />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>

          {/* Messages by Hour */}
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Messages by Hour
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={messagesByHour}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" />
                <YAxis />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="messages"
                  stroke={theme.palette.primary.main}
                  fill={theme.palette.primary.light}
                />
              </AreaChart>
            </ResponsiveContainer>
          </Paper>
        </Box>

        {/* Full Width Charts */}
        <Box>
          {/* Messages by Day */}
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Messages by Day of Week
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={messagesByDay}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="messages" fill={theme.palette.primary.main} />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Box>

        {/* Two Column Charts */}
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 3 }}>
          {/* Top Keywords */}
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Top Keywords
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={topKeywords} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="word" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill={theme.palette.secondary.main} />
              </BarChart>
            </ResponsiveContainer>
          </Paper>

          {/* Participant Activity */}
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Participant Activity
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={participantActivity}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="messages" fill={theme.palette.info.main} />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Box>

        {/* Media Types */}
        {Object.keys(analytics.media_stats).length > 0 && (
          <Box>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Media Types Shared
              </Typography>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={mediaStats}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ type, count }) => `${type}: ${count}`}
                    outerRadius={60}
                    fill="#8884d8"
                    dataKey="count"
                  >
                    {mediaStats.map((_entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </Paper>
          </Box>
        )}

        {/* Entity Analysis */}
        {analytics.entity_analysis.entities && (
          <Box>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Extracted Entities
              </Typography>
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 2 }}>
                {Object.entries(analytics.entity_analysis.entities).map(([type, entities]) => (
                  <Box key={type}>
                    <Typography variant="subtitle2" gutterBottom>
                      {type}
                    </Typography>
                    <Box display="flex" flexWrap="wrap" gap={1}>
                      {(entities as any[]).slice(0, 10).map((entity: any, index: number) => (
                        <Chip
                          key={index}
                          label={`${entity.text} (${entity.count})`}
                          size="small"
                          variant="outlined"
                        />
                      ))}
                    </Box>
                  </Box>
                ))}
              </Box>
            </Paper>
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default AnalyticsCharts;