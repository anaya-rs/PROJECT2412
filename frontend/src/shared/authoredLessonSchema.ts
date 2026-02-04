import { z } from 'zod';

const durationMinutesSchema = z.union([z.literal(5), z.literal(30), z.literal(60)]);

const authoredContentStateSchema = z.object({
  id: z.string().min(1),
  type: z.literal('content'),
  title: z.string().min(1).optional(),
  text: z.string().min(1),
});

const mcqQuestionSchema = z.object({
  question_format: z.literal('mcq'),
  question: z.string().min(1),
  options: z.array(z.string().min(1)).min(3).max(5),
  correct_answer: z.number().int().min(0),
  explanation: z.string().min(1),
});

const authoredQuestionStateSchema = z.object({
  id: z.string().min(1),
  type: z.literal('question'),
  ...mcqQuestionSchema.shape,
});

export const authoredStateSchema = z.discriminatedUnion('type', [
  authoredContentStateSchema,
  authoredQuestionStateSchema,
]);

export const authoredLessonSchema = z
  .object({
    lesson_metadata: z.object({
      title: z.string().min(1),
      description: z.string().optional(),
      estimated_duration_minutes: durationMinutesSchema,
      difficulty: z.union([z.literal('beginner'), z.literal('intermediate'), z.literal('advanced')]).optional(),
    }),
    states: z.array(authoredStateSchema).min(1),
  })
  .superRefine((val, ctx) => {
    const ids = val.states.map((s) => s.id);
    const unique = new Set(ids);
    if (unique.size !== ids.length) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'State ids must be unique',
        path: ['states'],
      });
    }

    for (let i = 0; i < val.states.length; i++) {
      const s = val.states[i];
      if (s.type === 'content') {
        const words = s.text.trim().split(/\s+/).filter(Boolean);
        if (words.length > 150) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: `Content block too long (${words.length} words). Max 150 words.`,
            path: ['states', i, 'text'],
          });
        }
      }

      if (s.type === 'question') {
        if (s.correct_answer < 0 || s.correct_answer >= s.options.length) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: `correct_answer index out of range (0..${s.options.length - 1})`,
            path: ['states', i, 'correct_answer'],
          });
        }
      }
    }

    const duration = val.lesson_metadata.estimated_duration_minutes;
    const ranges: Record<number, { min: number; max: number }> = {
      5: { min: 4, max: 5 },
      30: { min: 14, max: 18 },
      60: { min: 26, max: 33 },
    };

    const r = ranges[duration];
    if (val.states.length < r.min || val.states.length > r.max) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: `Invalid authored state count for ${duration} minutes: ${val.states.length} (expected ${r.min}..${r.max})`,
        path: ['states'],
      });
    }

    const questionCount = val.states.filter((s) => s.type === 'question').length;
    if (questionCount < 1) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Lesson must include at least 1 question state',
        path: ['states'],
      });
    }
  });

export type AuthoredContentState = z.infer<typeof authoredContentStateSchema>;
export type AuthoredQuestionState = z.infer<typeof authoredQuestionStateSchema>;
export type AuthoredState = z.infer<typeof authoredStateSchema>;
export type AuthoredLesson = z.infer<typeof authoredLessonSchema>;

export function safeParseAuthoredLesson(input: unknown) {
  return authoredLessonSchema.safeParse(input);
}
