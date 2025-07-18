import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import conversationService from '../../services/conversation.service';
import type { 
  Conversation, 
  ConversationDetail, 
  ConversationFilters,
  Message,
  MessageFilters,
  Participant
} from '../../types/conversation.types';
import type { PaginationParams, PaginationMeta } from '../../types/common.types';

interface ConversationState {
  conversations: Conversation[];
  currentConversation: ConversationDetail | null;
  messages: Message[];
  participants: Participant[];
  pagination: PaginationMeta | null;
  messagePagination: PaginationMeta | null;
  isLoading: boolean;
  isLoadingMessages: boolean;
  error: string | null;
  filters: ConversationFilters;
  messageFilters: MessageFilters;
}

const initialState: ConversationState = {
  conversations: [],
  currentConversation: null,
  messages: [],
  participants: [],
  pagination: null,
  messagePagination: null,
  isLoading: false,
  isLoadingMessages: false,
  error: null,
  filters: {},
  messageFilters: {},
};

// Async thunks
export const fetchConversations = createAsyncThunk(
  'conversation/fetchConversations',
  async (params: PaginationParams & ConversationFilters) => {
    const response = await conversationService.getConversations(params);
    return response;
  }
);

export const fetchConversation = createAsyncThunk(
  'conversation/fetchConversation',
  async (id: string) => {
    const response = await conversationService.getConversation(id);
    return response;
  }
);

export const deleteConversation = createAsyncThunk(
  'conversation/deleteConversation',
  async (id: string) => {
    await conversationService.deleteConversation(id);
    return id;
  }
);

export const importConversationFile = createAsyncThunk(
  'conversation/importFile',
  async (file: File) => {
    const response = await conversationService.importFromFile(file);
    return response;
  }
);

export const fetchMessages = createAsyncThunk(
  'conversation/fetchMessages',
  async ({ conversationId, params }: { 
    conversationId: string; 
    params: PaginationParams & MessageFilters 
  }) => {
    const response = await conversationService.getMessages(conversationId, params);
    return response;
  }
);

export const fetchParticipants = createAsyncThunk(
  'conversation/fetchParticipants',
  async (conversationId: string) => {
    const response = await conversationService.getParticipants(conversationId);
    return response;
  }
);

// Slice
const conversationSlice = createSlice({
  name: 'conversation',
  initialState,
  reducers: {
    setFilters: (state, action: PayloadAction<ConversationFilters>) => {
      state.filters = action.payload;
    },
    setMessageFilters: (state, action: PayloadAction<MessageFilters>) => {
      state.messageFilters = action.payload;
    },
    clearCurrentConversation: (state) => {
      state.currentConversation = null;
      state.messages = [];
      state.participants = [];
      state.messagePagination = null;
    },
    addMessage: (state, action: PayloadAction<Message>) => {
      state.messages.push(action.payload);
    },
    updateMessage: (state, action: PayloadAction<Message>) => {
      const index = state.messages.findIndex(m => m.id === action.payload.id);
      if (index !== -1) {
        state.messages[index] = action.payload;
      }
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
  },
  extraReducers: (builder) => {
    // Fetch conversations
    builder
      .addCase(fetchConversations.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchConversations.fulfilled, (state, action) => {
        state.isLoading = false;
        state.conversations = action.payload.items;
        state.pagination = action.payload.pagination;
      })
      .addCase(fetchConversations.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch conversations';
      });

    // Fetch single conversation
    builder
      .addCase(fetchConversation.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchConversation.fulfilled, (state, action) => {
        state.isLoading = false;
        state.currentConversation = action.payload;
      })
      .addCase(fetchConversation.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch conversation';
      });

    // Delete conversation
    builder
      .addCase(deleteConversation.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(deleteConversation.fulfilled, (state, action) => {
        state.isLoading = false;
        state.conversations = state.conversations.filter(c => c.id !== action.payload);
        if (state.currentConversation?.id === action.payload) {
          state.currentConversation = null;
        }
      })
      .addCase(deleteConversation.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to delete conversation';
      });

    // Import conversation
    builder
      .addCase(importConversationFile.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(importConversationFile.fulfilled, (state) => {
        state.isLoading = false;
        // Conversation will be added when fetching the list again
      })
      .addCase(importConversationFile.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to import conversation';
      });

    // Fetch messages
    builder
      .addCase(fetchMessages.pending, (state) => {
        state.isLoadingMessages = true;
        state.error = null;
      })
      .addCase(fetchMessages.fulfilled, (state, action) => {
        state.isLoadingMessages = false;
        state.messages = action.payload.items;
        state.messagePagination = action.payload.pagination;
      })
      .addCase(fetchMessages.rejected, (state, action) => {
        state.isLoadingMessages = false;
        state.error = action.error.message || 'Failed to fetch messages';
      });

    // Fetch participants
    builder
      .addCase(fetchParticipants.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(fetchParticipants.fulfilled, (state, action) => {
        state.isLoading = false;
        state.participants = action.payload;
      })
      .addCase(fetchParticipants.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch participants';
      });
  },
});

export const {
  setFilters,
  setMessageFilters,
  clearCurrentConversation,
  addMessage,
  updateMessage,
  setError,
} = conversationSlice.actions;

export default conversationSlice.reducer;