const API_BASE_URL = '/api';

export interface Lesson {
  id: number;
  title: string;
  schema_version: string;
  estimated_duration_minutes: number;
  states: AuthoredState[];
  created_at: string;
  metadata?: Record<string, any>;
}

export interface AuthoredState {
  id: string;
  type: "content" | "question" | "end_notes";
  text?: string;
  question_type?: "single_choice" | "multiple_choice";
  prompt?: string;
  options?: string[];
  correct_answers?: number[];
  explanation?: string;
  summary?: string;
  key_takeaways?: string[];
}

export interface SessionState {
  state: AuthoredState | null;
  progress: number;
  attempts_left: number;
  completed: boolean;
  status?: 'retry' | 'reveal_answer' | 'success' | 'correct' | 'hint_revealed' | 'skipped';
  message?: string;
  correct_answer?: string | number;
  explanation_visible?: boolean;
  allow_next?: boolean;
  feedback?: string;
}

export interface SessionResponse {
  session_id: string;
  session_state: SessionState;
}

export interface ActionResult {
  session_id: string;
  result: SessionState;
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
  created_at?: string;  
  updated_at?: string; 
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
    // Add cache-busting timestamp for CORS debugging
    const url = `${API_BASE_URL}${endpoint}${endpoint.includes('?') ? '&' : '?'}_t=${Date.now()}`;
    
    const response = await fetch(url, {
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
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
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

  // Session endpoints
  async createSession(lessonId: number): Promise<SessionResponse> {
    return this.post<SessionResponse>(`/sessions?lesson_id=${lessonId}`);
  }

  async getSession(sessionId: string): Promise<SessionResponse> {
    return this.get<SessionResponse>(`/sessions/${sessionId}`);
  }

  async submitAnswer(sessionId: string, answer: any): Promise<ActionResult> {
    return this.post<ActionResult>(`/sessions/${sessionId}/answer`, answer);
  }

  async submitNext(sessionId: string, payload?: any): Promise<ActionResult> {
    return this.post<ActionResult>(`/sessions/${sessionId}/next`, payload || {});
  }

  async getHint(sessionId: string): Promise<ActionResult> {
    return this.post<ActionResult>(`/sessions/${sessionId}/hint`, {});
  }

  async skipQuestion(sessionId: string): Promise<ActionResult> {
    return this.post<ActionResult>(`/sessions/${sessionId}/skip`, {});
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
