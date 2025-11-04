import axios from 'axios';
import { ChatRequest, ChatInitResponse, ChatReadyResponse, StreamMessage } from '@/lib/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1` : "http://localhost:8001/api/v1";

// Get auth headers
function getAuthHeaders() {
    const token = localStorage.getItem('auth_token');
    const headers: any = {
        "Content-Type": "application/json"
    };
    
    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }
    
    return headers;
}

// Configure axios interceptors for authentication
axios.interceptors.request.use((config) => {
    const token = localStorage.getItem('auth_token');
    if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

axios.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('auth_token');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export class ChatApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Step 1: Initialize chat session
   */
  async initiateChatStream(request: ChatRequest): Promise<ChatInitResponse> {
    try {
      const response = await axios.post<ChatInitResponse>(`${this.baseUrl}/chat_assistant/ask/stream`, request);
      return response.data;
    } catch (error) {
      // Always try fallback for any error (network, server, etc.)
      try {
        return await this.fallbackToNonStreaming(request);
      } catch (fallbackError) {
        // Return a mock response to prevent the app from crashing
        return {
          task_id: 'error-' + Date.now(),
          stream_channel: 'error-channel',
          message: 'Sorry, I\'m having trouble connecting right now. Please try again in a moment.',
          status: 'error',
          user_context: {
            location: request.location,
            learning_path_id: request.learning_path_id || null,
            module_id: request.module_id || null,
            quiz_id: request.quiz_id || null,
            session_id: 'error-session'
          },
          estimated_completion_time: 0
        };
      }
    }
  }

  /**
   * Fallback to non-streaming chat when Redis/Celery are not available
   */
  private async fallbackToNonStreaming(request: ChatRequest): Promise<ChatInitResponse> {
    try {
      const response = await axios.post<any>(`${this.baseUrl}/chat_assistant/ask`, request);
      
      // Create a mock streaming response for compatibility
      return {
        task_id: 'fallback-' + Date.now(),
        stream_channel: 'fallback-channel',
        message: 'Using non-streaming fallback mode',
        status: 'fallback',
        user_context: {
          location: request.location,
          learning_path_id: request.learning_path_id || null,
          module_id: request.module_id || null,
          quiz_id: request.quiz_id || null,
          session_id: 'fallback-session'
        },
        estimated_completion_time: 5
      };
    } catch (fallbackError) {
      throw fallbackError;
    }
  }

  /**
   * Step 2: Signal frontend ready
   */
  async signalFrontendReady(streamChannel: string): Promise<ChatReadyResponse> {
    try {
      const response = await axios.post<ChatReadyResponse>(`${this.baseUrl}/chat_assistant/ready/${encodeURIComponent(streamChannel)}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Step 3: Start streaming messages (handles SSE format)
   */
  async *streamChatResponse(streamChannel: string): AsyncGenerator<StreamMessage, void, unknown> {
    // Handle fallback mode
    if (streamChannel === 'fallback-channel') {
      yield {
        type: 'status',
        data: { message: 'Using fallback mode - response will be immediate' },
        timestamp: Date.now()
      };
      return;
    }
    
          // Handle error mode
      if (streamChannel === 'error-channel') {
        yield {
          type: 'error',
          data: { message: 'Sorry, I\'m having trouble connecting right now. Please try again in a moment.' },
          timestamp: Date.now()
        };
        return;
      }

    try {
      const headers = getAuthHeaders();
      headers.Accept = "text/event-stream";
      headers.Cache = "no-cache";

      const response = await fetch(`${this.baseUrl}/chat_assistant/stream/${encodeURIComponent(streamChannel)}`, {
        headers
      });
      
      if (!response.ok) {
        if (response.status === 401) {
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
          throw new Error('Authentication required');
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error('No response body');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      try {
        while (true) {
          const { value, done } = await reader.read();
          
          if (done) {
            // Process any remaining data in buffer
            if (buffer.trim()) {
              try {
                const message = JSON.parse(buffer.trim());
                yield message;
              } catch (parseError) {
              }
            }
            break;
          }

          // Decode the chunk and add to buffer
          const chunk = decoder.decode(value, { stream: true });
          buffer += chunk;

          // Process complete lines (SSE format: data: {...}\n\n)
          const lines = buffer.split('\n\n');
          buffer = lines.pop() || ''; // Keep incomplete line in buffer

          for (const line of lines) {
            if (line.trim()) {
              // Remove "data: " prefix if present
              const data = line.replace(/^data:\s*/, '').trim();
              
              if (data && data !== '[DONE]') {
                try {
                  const message = JSON.parse(data);
                  yield message;
                } catch (parseError) {
                }
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    } catch (error) {
      throw error;
    }
  }

  /**
   * Complete chat workflow helper
   */
  async startChat(request: ChatRequest): Promise<{
    initResponse: ChatInitResponse;
    readyResponse: ChatReadyResponse;
    messageStream: AsyncGenerator<StreamMessage, void, unknown>;
  }> {
    try {
      // Step 1: Initialize chat session
      const initResponse = await this.initiateChatStream(request);

      // Handle fallback mode
      if (initResponse.status === 'fallback') {
        const mockReadyResponse: ChatReadyResponse = {
          status: 'ok',
          message: 'Fallback mode - no streaming required',
          ready_key: 'fallback-ready'
        };
        
        const mockMessageStream = this.streamChatResponse(initResponse.stream_channel);
        
        return {
          initResponse,
          readyResponse: mockReadyResponse,
          messageStream: mockMessageStream
        };
      }
      
      // Handle error mode
      if (initResponse.status === 'error') {
        const errorReadyResponse: ChatReadyResponse = {
          status: 'error',
          message: 'Chat service error',
          ready_key: 'error-ready'
        };
        
        const errorMessageStream = this.streamChatResponse(initResponse.stream_channel);
        
        return {
          initResponse,
          readyResponse: errorReadyResponse,
          messageStream: errorMessageStream
        };
      }
      
      // Step 2: Signal frontend ready
      const readyResponse = await this.signalFrontendReady(initResponse.stream_channel);

      // Step 3: Start streaming
      const messageStream = this.streamChatResponse(initResponse.stream_channel);

      return {
        initResponse,
        readyResponse,
        messageStream
      };
    } catch (error) {
      throw error;
    }
  }

  /**
   * Simplified chat streaming method for direct use
   */
  async *chatWithStream(request: ChatRequest): AsyncGenerator<StreamMessage, void, unknown> {
    try {
      const { initResponse, messageStream } = await this.startChat(request);
      
      // Handle fallback mode
      if (initResponse.status === 'fallback') {
        try {
          // Get the actual response from the non-streaming endpoint
          const response = await axios.post<any>(`${this.baseUrl}/chat_assistant/ask`, request);
          const chatResponse = response.data;
          
          // Yield the response as if it were streamed
          yield {
            type: 'content',
            data: chatResponse.response,
            timestamp: Date.now()
          };
          
          yield {
            type: 'complete',
            data: { 
              message: 'Chat response completed',
              context_type: chatResponse.context_type,
              confidence: chatResponse.confidence
            },
            timestamp: Date.now()
          };
        } catch (fallbackError) {
          yield {
            type: 'error',
            data: { 
              message: 'Sorry, I\'m having trouble connecting right now. Please try again in a moment.'
            },
            timestamp: Date.now()
          };
        }
        
        return;
      }
      
      // Handle error mode
      if (initResponse.status === 'error') {
        yield {
          type: 'error',
          data: { 
            message: initResponse.message || 'Sorry, I\'m having trouble connecting right now. Please try again in a moment.'
          },
          timestamp: Date.now()
        };
        return;
      }
      
      // Normal streaming mode
      for await (const message of messageStream) {
        yield message;
      }
    } catch (error) {
      yield {
        type: 'error',
        data: { 
          message: 'Sorry, I\'m having trouble connecting right now. Please try again in a moment.'
        },
        timestamp: Date.now()
      };
    }
  }
}

// Create a default instance for easy importing
const chatApi = new ChatApiService();

// Export the instance
export { chatApi };
export default chatApi;