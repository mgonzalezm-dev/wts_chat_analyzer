export interface Conversation {
  id: string;
  title: string;
  source_type: 'file_upload' | 'whatsapp_api';
  message_count: number;
  participant_count: number;
  started_at: string | null;
  ended_at: string | null;
  imported_at: string;
  status: 'importing' | 'processing' | 'ready' | 'failed';
  metadata?: Record<string, any>;
}

export interface ConversationDetail extends Conversation {
  participants: Participant[];
  analytics_available: boolean;
}

export interface Participant {
  id: string;
  phone_number: string;
  display_name: string;
  is_business?: boolean;
  message_count: number;
  first_message_at: string;
  last_message_at: string;
  metadata?: Record<string, any>;
}

export interface Message {
  id: string;
  conversation_id: string;
  sender_id: string;
  content: string;
  message_type: 'text' | 'image' | 'video' | 'audio' | 'document' | 'location' | 'contact' | 'sticker';
  timestamp: string;
  is_deleted: boolean;
  is_edited: boolean;
  reply_to_id?: string;
  media_url?: string;
  metadata?: Record<string, any>;
}

export interface ConversationFilters {
  search?: string;
  date_from?: string;
  date_to?: string;
  status?: string;
}

export interface MessageFilters {
  search?: string;
  sender_id?: string;
  date_from?: string;
  date_to?: string;
  message_type?: string;
}

export interface ImportRequest {
  source: 'whatsapp_api';
  api_credentials: {
    phone_number: string;
    api_key: string;
  };
  date_range?: {
    from: string;
    to: string;
  };
}

export interface ExportRequest {
  format: 'pdf' | 'csv' | 'json';
  filters?: {
    date_from?: string;
    date_to?: string;
    participants?: string[];
  };
  options?: {
    include_media?: boolean;
    include_analytics?: boolean;
  };
}