export interface Analytics {
  id: string;
  conversation_id: string;
  metric_type: 'sentiment' | 'keywords' | 'response_times' | 'activity_patterns' | 'entities';
  data: Record<string, any>;
  generated_at: string;
}

export interface DashboardStats {
  total_conversations: number;
  total_messages: number;
  total_participants: number;
  active_conversations: number;
  date_range: {
    from: string;
    to: string;
  };
}

export interface SentimentAnalysis {
  positive: number;
  negative: number;
  neutral: number;
  overall_score: number;
  timeline: Array<{
    date: string;
    positive: number;
    negative: number;
    neutral: number;
  }>;
}

export interface KeywordAnalysis {
  keywords: Array<{
    word: string;
    count: number;
    relevance: number;
  }>;
  word_cloud: Array<{
    text: string;
    value: number;
  }>;
}

export interface ResponseTimeAnalysis {
  average_response_time: number;
  median_response_time: number;
  by_participant: Array<{
    participant_id: string;
    participant_name: string;
    average_time: number;
    total_responses: number;
  }>;
  by_hour: Array<{
    hour: number;
    average_time: number;
  }>;
}

export interface ActivityPattern {
  by_hour: Array<{
    hour: number;
    message_count: number;
  }>;
  by_day: Array<{
    day: string;
    message_count: number;
  }>;
  by_participant: Array<{
    participant_id: string;
    participant_name: string;
    message_count: number;
    percentage: number;
  }>;
}

export interface Bookmark {
  id: string;
  conversation_id: string;
  message_id: string;
  title: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface Annotation {
  id: string;
  conversation_id: string;
  message_id: string;
  content: string;
  category: 'task' | 'decision' | 'important' | 'question' | 'other';
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface AISummaryRequest {
  conversation_id: string;
  options: {
    summary_type: 'executive' | 'detailed' | 'bullet_points';
    date_range?: {
      from: string;
      to: string;
    };
    focus_areas?: Array<'decisions' | 'action_items' | 'key_topics'>;
  };
}

export interface AISummary {
  id: string;
  conversation_id: string;
  summary_type: string;
  content: string;
  key_points: string[];
  action_items?: string[];
  decisions?: string[];
  generated_at: string;
}

export interface ConversationAnalytics {
  conversation_id: string;
  generated_at: string;
  processing_time_seconds: number;
  total_messages: number;
  total_participants: number;
  date_range: {
    start: string;
    end: string;
  };
  avg_messages_per_day: number;
  sentiment_analysis: {
    overall_sentiment: {
      positive: number;
      negative: number;
      neutral: number;
      compound: number;
    };
    sentiment_by_participant: Record<string, {
      positive: number;
      negative: number;
      neutral: number;
      compound: number;
    }>;
    sentiment_timeline: Array<{
      date: string;
      sentiment: number;
    }>;
    most_positive_messages: Array<{
      id: string;
      content: string;
      score: number;
    }>;
    most_negative_messages: Array<{
      id: string;
      content: string;
      score: number;
    }>;
  };
  keyword_analysis: {
    top_keywords: Array<{
      keyword: string;
      count: number;
      frequency: number;
    }>;
    keyword_trends: Array<{
      date: string;
      keywords: Record<string, number>;
    }>;
    keyword_by_participant: Record<string, Array<{
      keyword: string;
      count: number;
    }>>;
    word_cloud_data: Array<{
      text: string;
      value: number;
    }>;
  };
  entity_analysis: {
    entities: Record<string, Array<{
      text: string;
      count: number;
      confidence: number;
    }>>;
    entity_frequency: Record<string, number>;
    entity_timeline: Array<{
      date: string;
      entities: Record<string, number>;
    }>;
  };
  timeline_analysis: {
    messages_by_hour: Record<string, number>;
    messages_by_day: Record<string, number>;
    messages_by_month: Record<string, number>;
    activity_heatmap: Array<{
      day: string;
      hour: number;
      count: number;
    }>;
    peak_hours: number[];
    peak_days: string[];
    response_time_analysis: {
      avg_response_time: number;
      median_response_time: number;
      by_participant: Record<string, number>;
    };
  };
  participant_analytics: Array<{
    participant_id: string;
    phone_number: string;
    display_name?: string;
    message_count: number;
    avg_message_length: number;
    response_time_avg: number;
    active_hours: number[];
    emoji_usage: Record<string, number>;
    media_shared: Record<string, number>;
    sentiment_score: {
      positive: number;
      negative: number;
      neutral: number;
      compound: number;
    };
    top_keywords: Array<{
      keyword: string;
      count: number;
    }>;
  }>;
  media_stats: Record<string, number>;
  link_stats: {
    total_links: number;
    unique_domains: number;
    top_domains: Array<{
      domain: string;
      count: number;
    }>;
  };
}