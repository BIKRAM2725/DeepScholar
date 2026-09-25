const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

export interface Chat {
  id: string;
  user_id: string;
  created_at: string;
}

export interface Message {
  id: string;
  chat_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export type PaperMode = 'fast' | 'deep';
export type PaperStatus = 'generating' | 'ready' | 'failed';

export interface Paper {
  id: string;
  user_id: string;
  chat_id: string | null;
  topic: string;
  title: string | null;
  mode: PaperMode;
  status: PaperStatus;
  storage_path: string | null;
  file_url: string | null;
  sources_used: number | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaperFigure {
  caption: string;
  image_base64: string; // data: URL or raw base64
}

export interface GeneratePaperInput {
  topic: string;
  title?: string;
  authors?: string;
  notes?: string;
  steps?: string[];
  metrics?: Record<string, number>;
  figures?: PaperFigure[];
  mode?: PaperMode;
  chatId?: string;
}

// One event from the paper-generation stream. `paper` only arrives on "done".
export type PaperStreamEvent =
  | { type: 'started'; paperId: string }
  | { type: 'progress'; step: string; index: number; total: number }
  | { type: 'error'; message: string }
  | { type: 'done'; paper: Paper };

class ApiClient {
  private getAuthHeader(token: string | null): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }

  async syncUser(token: string) {
    const response = await fetch(`${API_URL}/auth/sync`, {
      method: 'POST',
      headers: this.getAuthHeader(token),
    });
    if (!response.ok) throw new Error('Failed to sync user');
    return response.json();
  }

  async logout(token: string) {
    const response = await fetch(`${API_URL}/auth/logout`, {
      method: 'POST',
      headers: this.getAuthHeader(token),
    });
    if (!response.ok) throw new Error('Failed to logout');
    return response.json();
  }

  async getChats(token: string): Promise<Chat[]> {
    const response = await fetch(`${API_URL}/chats`, {
      headers: this.getAuthHeader(token),
    });
    if (!response.ok) throw new Error('Failed to fetch chats');
    return response.json();
  }

  async createChat(token: string): Promise<Chat> {
    const response = await fetch(`${API_URL}/chats`, {
      method: 'POST',
      headers: this.getAuthHeader(token),
    });
    if (!response.ok) throw new Error('Failed to create chat');
    return response.json();
  }

  async deleteChat(token: string, chatId: string) {
    const response = await fetch(`${API_URL}/chats/${chatId}`, {
      method: 'DELETE',
      headers: this.getAuthHeader(token),
    });
    if (!response.ok) throw new Error('Failed to delete chat');
    return response.json();
  }

  async getMessages(token: string, chatId: string): Promise<Message[]> {
    const response = await fetch(`${API_URL}/chats/${chatId}/messages`, {
      headers: this.getAuthHeader(token),
    });
    if (!response.ok) throw new Error('Failed to fetch messages');
    return response.json();
  }

  async sendMessage(token: string, chatId: string, query: string, mode: 'query' | 'chatllm' = 'chatllm') {
    const response = await fetch(`${API_URL}/chats/${chatId}/messages`, {
      method: 'POST',
      headers: this.getAuthHeader(token),
      body: JSON.stringify({ query, mode }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Failed to send message' }));
      const errorMessage = errorData.details || errorData.error || 'Failed to send message';
      throw new Error(errorMessage);
    }

    return response.json();
  }

  async getPapers(token: string): Promise<Paper[]> {
    const response = await fetch(`${API_URL}/papers`, {
      headers: this.getAuthHeader(token),
    });
    if (!response.ok) throw new Error('Failed to fetch papers');
    return response.json();
  }

  async deletePaper(token: string, paperId: string) {
    const response = await fetch(`${API_URL}/papers/${paperId}`, {
      method: 'DELETE',
      headers: this.getAuthHeader(token),
    });
    if (!response.ok) throw new Error('Failed to delete paper');
    return response.json();
  }

  /**
   * Starts paper generation and streams progress via Server-Sent Events.
   * Uses fetch + a manual reader (not EventSource) because the request is a
   * POST with a JSON body and an auth header, which EventSource can't send.
   * Call `abort()` on the returned controller to cancel generation early.
   */
  generatePaperStream(
    token: string,
    input: GeneratePaperInput,
    onEvent: (event: PaperStreamEvent) => void,
    onError: (message: string) => void
  ): { abort: () => void } {
    const controller = new AbortController();

    (async () => {
      try {
        const response = await fetch(`${API_URL}/papers/generate`, {
          method: 'POST',
          headers: this.getAuthHeader(token),
          body: JSON.stringify(input),
          signal: controller.signal,
        });

        if (!response.ok || !response.body) {
          const data = await response.json().catch(() => ({}));
          onError(data.error || `The request failed (status ${response.status}).`);
          return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          let idx: number;
          while ((idx = buffer.indexOf('\n\n')) !== -1) {
            const raw = buffer.slice(0, idx);
            buffer = buffer.slice(idx + 2);
            const line = raw.split('\n').find((l) => l.startsWith('data: '));
            if (!line) continue;
            try {
              onEvent(JSON.parse(line.slice(6)) as PaperStreamEvent);
            } catch {
              // ignore a malformed frame; the stream continues
            }
          }
        }
      } catch (err) {
        if (controller.signal.aborted) return;
        onError(err instanceof Error ? err.message : 'Connection to the server was lost.');
      }
    })();

    return { abort: () => controller.abort() };
  }
}

export const api = new ApiClient();