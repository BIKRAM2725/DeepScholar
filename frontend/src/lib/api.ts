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
}

export const api = new ApiClient();
