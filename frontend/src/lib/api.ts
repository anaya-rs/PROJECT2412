const API_BASE_URL = 'http://localhost:5000/api';

export interface Lesson {
  id: number;
  title: string;
  description: string;
  startNodeId: string;
  nodes: any;
  transitions: any;
  metadata?: any;
  createdAt: string;
  updatedAt: string;
}

export interface AiJob {
  id: string;
  userId: number;
  status: 'queued' | 'running' | 'completed' | 'failed';
  progress: number;
  message?: string;
  lessonId?: number;
  inputTitle?: string;
  inputDescription?: string;
  fileName?: string;
  difficulty?: string;
  duration?: number;
  questionCount?: number;
  createdAt?: string;
  updatedAt?: string;
}

class ApiService {
  private getAuthHeaders() {
    const token = localStorage.getItem('authToken');
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    };
  }

  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: this.getAuthHeaders(),
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: data ? JSON.stringify(data) : undefined,
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  }

  async put<T>(endpoint: string, data: any): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  }

  async delete<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  }

  // Auth endpoints
  async login(username: string, password: string) {
    return this.post('/auth/login', { username, password });
  }

  // Lesson endpoints
  async getLessons(): Promise<Lesson[]> {
    return this.get<Lesson[]>('/lessons');
  }

  async getLesson(id: number): Promise<Lesson> {
    return this.get<Lesson>(`/lessons/${id}`);
  }

  async createLesson(lessonData: Partial<Lesson>): Promise<Lesson> {
    return this.post<Lesson>('/lessons', lessonData);
  }

  async deleteLesson(id: number): Promise<void> {
    return this.delete(`/lessons/${id}`);
  }

  // AI endpoints
  async generateLesson(text: string, options?: any) {
    return this.post<{success: boolean; lesson?: any; error?: string}>('/ai/generate-lesson', { text, ...options });
  }

  async startAiLessonJob(payload: {
    text: string;
    title?: string;
    description?: string;
    fileName?: string;
    difficulty?: string;
    duration?: number;
    questionCount?: number;
  }) {
    return this.post<{ jobId: string }>('/ai/jobs', payload);
  }

  async getAiLessonJob(jobId: string): Promise<AiJob> {
    return this.get<AiJob>(`/ai/jobs/${jobId}`);
  }

  // File upload
  async uploadFile(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      headers: {
        ...(localStorage.getItem('authToken') && { 
          Authorization: `Bearer ${localStorage.getItem('authToken')}` 
        }),
      },
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error(`Upload Error: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  }
}

export const apiService = new ApiService();
