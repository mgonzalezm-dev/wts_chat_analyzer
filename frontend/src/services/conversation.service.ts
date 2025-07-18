import { api } from './api';
import type { 
  Conversation, 
  ConversationDetail, 
  ConversationFilters, 
  Message, 
  MessageFilters,
  Participant,
  ImportRequest,
  ExportRequest 
} from '../types/conversation.types';
import type { PaginatedResponse, PaginationParams } from '../types/common.types';

class ConversationService {
  async getConversations(
    params: PaginationParams & ConversationFilters
  ): Promise<PaginatedResponse<Conversation>> {
    const response = await api.get<{
      conversations: Conversation[];
      pagination: any;
    }>('/conversations', { params });
    
    return {
      items: response.data.data!.conversations,
      pagination: response.data.data!.pagination,
    };
  }

  async getConversation(id: string): Promise<ConversationDetail> {
    const response = await api.get<ConversationDetail>(`/conversations/${id}`);
    return response.data.data!;
  }

  async deleteConversation(id: string): Promise<void> {
    await api.delete(`/conversations/${id}`);
  }

  async importFromFile(file: File): Promise<{ conversation_id: string; status: string }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post<{
      conversation_id: string;
      status: string;
      message: string;
    }>('/conversations/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data.data!;
  }

  async importFromWhatsAppAPI(request: ImportRequest): Promise<{ conversation_id: string; status: string }> {
    const response = await api.post<{
      conversation_id: string;
      status: string;
      message: string;
    }>('/conversations/import', request);

    return response.data.data!;
  }

  async getMessages(
    conversationId: string,
    params: PaginationParams & MessageFilters
  ): Promise<PaginatedResponse<Message>> {
    const response = await api.get<{
      messages: Message[];
      pagination: any;
    }>(`/conversations/${conversationId}/messages`, { params });

    return {
      items: response.data.data!.messages,
      pagination: response.data.data!.pagination,
    };
  }

  async getParticipants(conversationId: string): Promise<Participant[]> {
    const response = await api.get<{ participants: Participant[] }>(
      `/conversations/${conversationId}/participants`
    );
    return response.data.data!.participants;
  }

  async exportConversation(
    conversationId: string,
    request: ExportRequest
  ): Promise<{ job_id: string; status: string }> {
    const response = await api.post<{
      job_id: string;
      status: string;
    }>(`/conversations/${conversationId}/export`, request);

    return response.data.data!;
  }

  async getExportStatus(jobId: string): Promise<{
    status: string;
    progress: number;
    download_url?: string;
  }> {
    const response = await api.get<{
      status: string;
      progress: number;
      download_url?: string;
    }>(`/exports/${jobId}`);

    return response.data.data!;
  }

  async searchMessages(params: {
    query: string;
    conversation_ids?: string[];
    date_range?: { from: string; to: string };
    participants?: string[];
    message_types?: string[];
    sentiment?: string;
    options?: {
      highlight?: boolean;
      context_lines?: number;
    };
  }): Promise<{
    results: Array<{
      conversation_id: string;
      message: Message;
      highlights?: string[];
      context?: Message[];
    }>;
    total: number;
  }> {
    const response = await api.post<any>('/search', params);
    return response.data.data!;
  }
}

export default new ConversationService();