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
  question_type: z.enum(["single_choice", "multiple_choice"]),
  prompt: z.string().min(10).max(300),
  explanation: z.string().min(20).max(500),
  options: z.array(z.string()).min(2).max(8),
  correct_answers: z.array(z.number()).min(1),
});

export const QuestionStateSchema = QuestionStateBaseSchema.refine(
  (data) => {
    // Validate correct answer indices are within bounds
    for (const idx of data.correct_answers) {
      if (idx < 0 || idx >= data.options.length) {
        return false;
      }
    }
    
    // Single choice must have exactly 1 correct answer
    if (data.question_type === "single_choice" && data.correct_answers.length !== 1) {
      return false;
    }
    
    // Multiple choice must have at least 1 correct answer
    if (data.question_type === "multiple_choice" && data.correct_answers.length < 1) {
      return false;
    }
    
    return true;
  },
  {
    message: "Question validation failed - check correct_answers array",
    path: ["correct_answers"],
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
  answer: number[] | number
): { correct: boolean; error?: string } {
  // Convert single number to array for uniform handling
  const userAnswers = Array.isArray(answer) ? answer : [answer];
  
  // Validate answer indices are within bounds
  for (const idx of userAnswers) {
    if (typeof idx !== "number") {
      return { correct: false, error: "Answer must be a number" };
    }
    if (idx < 0 || idx >= state.options.length) {
      return { correct: false, error: "Answer index out of bounds" };
    }
  }
  
  // Check correctness based on question type
  if (state.question_type === "single_choice") {
    // For single choice, user should provide exactly one answer
    if (userAnswers.length !== 1) {
      return { correct: false, error: "Single choice requires exactly one answer" };
    }
    return { correct: userAnswers[0] === state.correct_answers[0] };
  }
  
  if (state.question_type === "multiple_choice") {
    // For multiple choice, check if all user answers are in correct answers
    // and all correct answers are selected by user
    const correctSet = new Set(state.correct_answers);
    const userSet = new Set(userAnswers);
    
    // Check if sets are equal
    if (correctSet.size !== userSet.size) {
      return { correct: false };
    }
    
    for (const answer of userSet) {
      if (!correctSet.has(answer)) {
        return { correct: false };
      }
    }
    
    return { correct: true };
  }
  
  return { correct: false, error: "Unknown question type" };
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
