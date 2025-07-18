import { describe, it, expect, vi } from 'vitest';
import { screen, within } from '@testing-library/react';
import AnalyticsCharts from '../AnalyticsCharts';
import { renderWithProviders, mockAnalytics } from '../../../test/utils';

// Mock recharts to avoid rendering issues in tests
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  PieChart: ({ children }: any) => <div data-testid="pie-chart">{children}</div>,
  RadarChart: ({ children }: any) => <div data-testid="radar-chart">{children}</div>,
  Line: () => null,
  Bar: () => null,
  Pie: () => null,
  Radar: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  Legend: () => null,
  Cell: () => null,
  PolarGrid: () => null,
  PolarAngleAxis: () => null,
  PolarRadiusAxis: () => null,
}));

describe('AnalyticsCharts', () => {
  const defaultAnalytics = mockAnalytics();

  it('renders all chart sections', () => {
    renderWithProviders(<AnalyticsCharts analytics={defaultAnalytics} />);
    
    expect(screen.getByText('Message Timeline')).toBeInTheDocument();
    expect(screen.getByText('Participant Activity')).toBeInTheDocument();
    expect(screen.getByText('Sentiment Analysis')).toBeInTheDocument();
    expect(screen.getByText('Message Types')).toBeInTheDocument();
    expect(screen.getByText('Top Keywords')).toBeInTheDocument();
    expect(screen.getByText('Activity Heatmap')).toBeInTheDocument();
  });

  it('displays message timeline chart', () => {
    renderWithProviders(<AnalyticsCharts analytics={defaultAnalytics} />);
    
    const timelineSection = screen.getByText('Message Timeline').closest('.MuiPaper-root');
    expect(within(timelineSection!).getByTestId('line-chart')).toBeInTheDocument();
  });

  it('displays participant stats correctly', () => {
    renderWithProviders(<AnalyticsCharts analytics={defaultAnalytics} />);
    
    const participantSection = screen.getByText('Participant Activity').closest('.MuiPaper-root');
    
    // Check if participant names are displayed
    expect(within(participantSection!).getByText('Alice')).toBeInTheDocument();
    expect(within(participantSection!).getByText('Bob')).toBeInTheDocument();
    
    // Check if message counts are displayed
    expect(within(participantSection!).getByText('50 messages')).toBeInTheDocument();
  });

  it('displays sentiment distribution', () => {
    renderWithProviders(<AnalyticsCharts analytics={defaultAnalytics} />);
    
    const sentimentSection = screen.getByText('Sentiment Analysis').closest('.MuiPaper-root');
    
    // Check overall sentiment
    expect(within(sentimentSection!).getByText('Overall: positive')).toBeInTheDocument();
    
    // Check pie chart is rendered
    expect(within(sentimentSection!).getByTestId('pie-chart')).toBeInTheDocument();
  });

  it('displays message type distribution', () => {
    renderWithProviders(<AnalyticsCharts analytics={defaultAnalytics} />);
    
    const messageTypesSection = screen.getByText('Message Types').closest('.MuiPaper-root');
    
    // Check if counts are displayed
    expect(within(messageTypesSection!).getByText('90')).toBeInTheDocument(); // text messages
    expect(within(messageTypesSection!).getByText('8')).toBeInTheDocument(); // media messages
    expect(within(messageTypesSection!).getByText('2')).toBeInTheDocument(); // system messages
  });

  it('displays top keywords', () => {
    renderWithProviders(<AnalyticsCharts analytics={defaultAnalytics} />);
    
    const keywordsSection = screen.getByText('Top Keywords').closest('.MuiPaper-root');
    
    // Check if keywords are displayed
    defaultAnalytics.top_keywords.forEach(keyword => {
      expect(within(keywordsSection!).getByText(keyword.keyword)).toBeInTheDocument();
    });
  });

  it('handles empty analytics data gracefully', () => {
    const emptyAnalytics = {
      ...defaultAnalytics,
      timeline_data: [],
      participant_stats: [],
      top_keywords: [],
    };
    
    renderWithProviders(<AnalyticsCharts analytics={emptyAnalytics} />);
    
    // Should still render without errors
    expect(screen.getByText('Message Timeline')).toBeInTheDocument();
  });

  it('formats dates correctly in timeline', () => {
    renderWithProviders(<AnalyticsCharts analytics={defaultAnalytics} />);
    
    // Timeline data should be formatted
    const timelineSection = screen.getByText('Message Timeline').closest('.MuiPaper-root');
    expect(timelineSection).toBeInTheDocument();
  });

  it('shows activity heatmap with hourly data', () => {
    renderWithProviders(<AnalyticsCharts analytics={defaultAnalytics} />);
    
    const heatmapSection = screen.getByText('Activity Heatmap').closest('.MuiPaper-root');
    
    // Should show participant names
    defaultAnalytics.participant_stats.forEach(participant => {
      expect(within(heatmapSection!).getByText(participant.name)).toBeInTheDocument();
    });
  });

  it('displays sentiment percentages', () => {
    const analytics = {
      ...defaultAnalytics,
      sentiment_analysis: {
        overall_sentiment: 'positive',
        sentiment_distribution: {
          positive: 0.6,
          neutral: 0.3,
          negative: 0.1,
        },
        sentiment_timeline: [],
      },
    };
    
    renderWithProviders(<AnalyticsCharts analytics={analytics} />);
    
    const sentimentSection = screen.getByText('Sentiment Analysis').closest('.MuiPaper-root');
    
    // Check percentages
    expect(within(sentimentSection!).getByText('60%')).toBeInTheDocument(); // positive
    expect(within(sentimentSection!).getByText('30%')).toBeInTheDocument(); // neutral
    expect(within(sentimentSection!).getByText('10%')).toBeInTheDocument(); // negative
  });

  it('shows keyword scores and frequencies', () => {
    renderWithProviders(<AnalyticsCharts analytics={defaultAnalytics} />);
    
    const keywordsSection = screen.getByText('Top Keywords').closest('.MuiPaper-root');
    
    defaultAnalytics.top_keywords.forEach(keyword => {
      // Check frequency is displayed
      expect(within(keywordsSection!).getByText(`${keyword.frequency}x`)).toBeInTheDocument();
    });
  });
});