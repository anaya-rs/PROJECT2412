// File upload interface for lesson creation
export interface UploadedFile {
  name: string;
  size: number;
  type: string;
  content: string;
  wordCount: number;
  characterCount: number;
}

// Lesson configuration for creation
export interface LessonConfig {
  title: string;
  description: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  duration: number;
  includeVideos: boolean;
}
