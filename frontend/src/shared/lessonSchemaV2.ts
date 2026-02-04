/**
 * Lesson Schema V2 - Frontend Zod Mirror
 * This must exactly match backend Pydantic models.
 * Frontend never guesses lesson shape again.
 */

import { z } from "zod";

// ---------- Base State ----------

export const BaseStateSchema = z.object({
  id: z.string().min(1),
  type: z.enum(["content", "question"]),
});

// ---------- Content State ----------

export const ContentStateSchema = z.object({
  id: z.string().min(1),
  type: z.literal("content"),
  text: z.string().min(20).max(900),
});

// ---------- Question State ----------

const QuestionStateBaseSchema = z.object({
  id: z.string().min(1),
  type: z.literal("question"),
  question_format: z.enum(["mcq", "short_answer"]),
  prompt: z.string().min(10).max(300),
  explanation: z.string().min(20).max(500),
  options: z.array(z.string()).min(2).optional(),
  correct_answer: z.union([z.number(), z.string()]),
});

export const QuestionStateSchema = QuestionStateBaseSchema.refine(
  (data) => {
    if (data.question_format === "mcq") {
      return (
        data.options !== undefined &&
        data.options.length >= 2 &&
        typeof data.correct_answer === "number" &&
        data.correct_answer >= 0 &&
        data.correct_answer < data.options.length
      );
    }
    if (data.question_format === "short_answer") {
      return typeof data.correct_answer === "string";
    }
    return false;
  },
  {
    message: "Question validation failed",
    path: ["correct_answer"],
  }
);

// ---------- Authored State Union ----------

export const LessonStateSchema = z.discriminatedUnion("type", [
  ContentStateSchema,
  QuestionStateBaseSchema,
]);

export type AuthoredState = z.infer<typeof LessonStateSchema>;
export type ContentState = z.infer<typeof ContentStateSchema>;
export type QuestionState = z.infer<typeof QuestionStateSchema>;

// ---------- Lesson ----------

export const LessonSchemaV2 = z.object({
  schema_version: z.literal("1.0"),
  title: z.string().min(5).max(120),
  estimated_duration_minutes: z.union([
    z.literal(5),
    z.literal(30),
    z.literal(60),
  ]),
  states: z
    .array(LessonStateSchema)
    .min(2)
    .refine(
      (states) =>
        !states.some(
          (s, i) =>
            s.type === "question" &&
            states[i + 1]?.type === "question"
        ),
      {
        message: "No consecutive questions allowed",
        path: ["states"],
      }
    )
    .refine(
      (states) => states[0].type === "content",
      {
        message: "First state must be content",
        path: ["states", 0],
      }
    ),
});

export type LessonV2 = z.infer<typeof LessonSchemaV2>;

// ---------- Migration Types ----------

export const MigrationRequestSchema = z.object({
  lesson_id: z.number(),
  target_duration: z.union([z.literal(5), z.literal(30), z.literal(60)]).default(30),
});

export const MigrationResultSchema = z.object({
  original_lesson_id: z.number(),
  new_lesson_id: z.number(),
  migrated_at: z.string(),
  schema_version: z.literal("1.0"),
});

export type MigrationRequest = z.infer<typeof MigrationRequestSchema>;
export type MigrationResult = z.infer<typeof MigrationResultSchema>;

// ---------- API Response Types ----------

export const GenerateLessonRequestSchema = z.object({
  title: z.string().min(1),
  description: z.string().optional(),
  content: z.string().min(100),
  duration_minutes: z.union([z.literal(5), z.literal(30), z.literal(60)]).default(30),
  difficulty: z.string().default("beginner"),
});

export const GenerateLessonResponseSchema = z.object({
  lesson_id: z.number(),
  title: z.string(),
  estimated_duration_minutes: z.number(),
  state_count: z.number(),
});

export const LessonResponseSchema = z.object({
  id: z.number(),
  title: z.string(),
  description: z.string(),
  schema_version: z.string(),
  estimated_duration_minutes: z.number().optional(),
  state_count: z.number().optional(),
  created_at: z.string(),
  updated_at: z.string(),
});

export type GenerateLessonRequest = z.infer<typeof GenerateLessonRequestSchema>;
export type GenerateLessonResponse = z.infer<typeof GenerateLessonResponseSchema>;
export type LessonResponse = z.infer<typeof LessonResponseSchema>;

// ---------- Analytics Event Types ----------

export const AnalyticsEventSchema = z.object({
  event_type: z.enum(["enter", "answer", "retry", "advance", "complete"]),
  payload: z.record(z.any()).optional(),
  state_id: z.string().optional(),
});

export type AnalyticsEvent = z.infer<typeof AnalyticsEventSchema>;

// ---------- Utility Functions ----------

export function validateLessonV2(data: unknown): LessonV2 {
  return LessonSchemaV2.parse(data);
}

export function isContentState(state: AuthoredState): state is ContentState {
  return state.type === "content";
}

export function isQuestionState(state: AuthoredState): state is QuestionState {
  return state.type === "question";
}

export function validateQuestionAnswer(
  state: QuestionState,
  answer: number | string
): { correct: boolean; error?: string } {
  if (state.question_format === "mcq") {
    if (typeof answer !== "number") {
      return { correct: false, error: "MCQ answer must be a number" };
    }
    if (answer < 0 || answer >= (state.options?.length || 0)) {
      return { correct: false, error: "Answer index out of bounds" };
    }
    return { correct: answer === state.correct_answer };
  }
  
  if (state.question_format === "short_answer") {
    if (typeof answer !== "string") {
      return { correct: false, error: "Short answer must be a string" };
    }
    // Simple string comparison - could be enhanced for fuzzy matching
    return { 
      correct: answer.trim().toLowerCase() === (state.correct_answer as string).trim().toLowerCase() 
    };
  }
  
  return { correct: false, error: "Unknown question format" };
}

export function getLessonDurationStats(lesson: LessonV2): {
  contentCount: number;
  questionCount: number;
  estimatedMinutes: number;
} {
  const contentCount = lesson.states.filter(isContentState).length;
  const questionCount = lesson.states.filter(isQuestionState).length;
  
  return {
    contentCount,
    questionCount,
    estimatedMinutes: lesson.estimated_duration_minutes,
  };
}
