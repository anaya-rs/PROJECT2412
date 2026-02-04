export interface Video {
  videoId: string;
  title: string;
  thumbnail?: string;
}

export interface ContentState {
  type: 'content';
  content: string;
  videos?: Video[];
  transitions: {
    next: string;
  };
}

export interface QuestionState {
  type: 'question';
  question: string;
  options: string[];
  correct: number;
  explanation?: string;
  transitions: {
    correct: string;
    incorrect: string;
  };
}

export interface FeedbackState {
  type: 'feedback';
  content: string;
  isCorrect: boolean;
  transitions: {
    next: string;
    retry?: string;
  };
}

export interface EndState {
  type: 'end';
  title: string;
  summary: string;
  score?: number;
}

export type LessonState = ContentState | QuestionState | FeedbackState | EndState;

export interface LessonFSM {
  states: Record<string, LessonState>;
  initialState: string;
}

export interface Lesson {
  id: string;
  title: string;
  description: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  duration: number; // minutes
  questionCount: number;
  includeVideos: boolean;
  fsm: LessonFSM;
  createdAt: string;
  updatedAt: string;
  completionRate?: number;
}

export interface LessonConfig {
  title: string;
  description: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  duration: number;
  questionCount: number;
  includeVideos: boolean;
}

export interface UploadedFile {
  name: string;
  size: number;
  type: string;
  content: string;
  wordCount: number;
  characterCount: number;
}
