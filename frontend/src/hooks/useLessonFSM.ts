/**
 * React Lesson FSM Hook - Deterministic Execution
 * This replaces ad-hoc navigation logic.
 * 
 * FSM controls progression, UI components only render.
 */

import { useState, useCallback, useEffect } from "react";
import { LessonV2, AuthoredState, validateLessonV2, isContentState, isQuestionState } from "@/shared/lessonSchemaV2";

export interface FSMResult {
  feedback: "correct" | "wrong_retry" | "wrong_final" | "content_complete";
  advance: boolean;
  state?: AuthoredState;
}

export interface FSMState {
  current: AuthoredState | null;
  index: number;
  attempts: number;
  finished: boolean;
  progress: number;
  events: Array<{
    event_type: string;
    payload: Record<string, any>;
  }>;
}

export function useLessonFSM(rawLesson: unknown) {
  // Validate lesson structure
  const lesson = validateLessonV2(rawLesson);
  
  const [state, setState] = useState<FSMState>(() => ({
    current: lesson.states[0] || null,
    index: 0,
    attempts: 0,
    finished: false,
    progress: 0,
    events: [{
      event_type: "enter",
      payload: { state_id: lesson.states[0]?.id }
    }]
  }));

  // Reset FSM when lesson changes
  useEffect(() => {
    setState({
      current: lesson.states[0] || null,
      index: 0,
      attempts: 0,
      finished: false,
      progress: 0,
      events: [{
        event_type: "enter",
        payload: { state_id: lesson.states[0]?.id }
      }]
    });
  }, [lesson]);

  const logEvent = useCallback((eventType: string, payload: Record<string, any> = {}) => {
    setState(prev => ({
      ...prev,
      events: [...prev.events, { event_type: eventType, payload }]
    }));
  }, []);

  const submitAnswer = useCallback((isCorrect: boolean): FSMResult => {
    if (state.finished || !state.current || !isQuestionState(state.current)) {
      throw new Error("Cannot submit answer - no active question");
    }

    const current = state.current;
    
    // Log the answer event
    logEvent("answer", {
      state_id: current.id,
      correct: isCorrect,
      attempt: state.attempts + 1
    });

    if (isCorrect) {
      // Correct answer - advance immediately
      logEvent("advance", { reason: "correct" });
      const nextIndex = state.index + 1;
      const next = lesson.states[nextIndex] || null;
      
      setState(prev => ({
        ...prev,
        index: nextIndex,
        attempts: 0,
        current: next,
        finished: nextIndex >= lesson.states.length,
        progress: (nextIndex / lesson.states.length) * 100
      }));

      return {
        feedback: "correct",
        advance: true,
        state: current
      };
    }

    // Wrong answer logic
    if (state.attempts === 0) {
      // First wrong attempt - show explanation and retry
      logEvent("retry", { attempt: 1 });
      setState(prev => ({
        ...prev,
        attempts: prev.attempts + 1
      }));

      return {
        feedback: "wrong_retry",
        advance: false,
        state: current
      };
    }

    // Second wrong attempt - show explanation and force advance
    logEvent("advance", { reason: "wrong_final" });
    const nextIndex = state.index + 1;
    const next = lesson.states[nextIndex] || null;
    
    setState(prev => ({
      ...prev,
      index: nextIndex,
      attempts: 0,
      current: next,
      finished: nextIndex >= lesson.states.length,
      progress: (nextIndex / lesson.states.length) * 100
    }));

    return {
      feedback: "wrong_final",
      advance: true,
      state: current
    };
  }, [state, lesson.states, logEvent]);

  const advanceContent = useCallback((): FSMResult => {
    if (state.finished || !state.current || !isContentState(state.current)) {
      throw new Error("Cannot advance content - no active content state");
    }

    const current = state.current;
    
    // Log content advancement
    logEvent("advance", { reason: "content_complete" });
    const nextIndex = state.index + 1;
    const next = lesson.states[nextIndex] || null;
    
    setState(prev => ({
      ...prev,
      index: nextIndex,
      attempts: 0,
      current: next,
      finished: nextIndex >= lesson.states.length,
      progress: (nextIndex / lesson.states.length) * 100
    }));

    return {
      feedback: "content_complete",
      advance: true,
      state: current
    };
  }, [state, lesson.states, logEvent]);

  const reset = useCallback(() => {
    setState({
      current: lesson.states[0] || null,
      index: 0,
      attempts: 0,
      finished: false,
      progress: 0,
      events: [{
        event_type: "enter",
        payload: { state_id: lesson.states[0]?.id }
      }]
    });
  }, [lesson.states]);

  const goToState = useCallback((targetIndex: number) => {
    if (targetIndex < 0 || targetIndex >= lesson.states.length) {
      throw new Error("Invalid state index");
    }

    const target = lesson.states[targetIndex];
    
    setState(prev => ({
      ...prev,
      index: targetIndex,
      attempts: 0,
      current: target,
      finished: targetIndex >= lesson.states.length - 1,
      progress: (targetIndex / lesson.states.length) * 100
    }));
  }, [lesson.states]);

  return {
    // Current state
    lesson,
    current: state.current,
    finished: state.finished,
    progress: state.progress,
    index: state.index,
    attempts: state.attempts,
    
    // Actions
    submitAnswer,
    advanceContent,
    reset,
    goToState,
    
    // Analytics
    events: state.events,
    totalStates: lesson.states.length,
    
    // Utilities
    isQuestionState: state.current ? isQuestionState(state.current) : false,
    isContentState: state.current ? isContentState(state.current) : false,
  };
}

// ---------- Utility Functions ----------

export function calculateSessionStats(events: Array<{event_type: string, payload: Record<string, any>}>) {
  const answers = events.filter(e => e.event_type === "answer");
  const correctAnswers = answers.filter(e => e.payload.correct === true);
  const retries = events.filter(e => e.event_type === "retry");
  const completion = events.find(e => e.event_type === "complete");

  return {
    totalEvents: events.length,
    questionsAnswered: answers.length,
    correctAnswers: correctAnswers.length,
    accuracy: answers.length > 0 ? (correctAnswers.length / answers.length) * 100 : 0,
    totalRetries: retries.length,
    completed: !!completion,
    completionRate: completion ? 100 : 0
  };
}

export function validateFSMState(lesson: LessonV2): string[] {
  const errors: string[] = [];

  if (!lesson.states || lesson.states.length === 0) {
    errors.push("Lesson must have at least one state");
    return errors;
  }

  if (lesson.states[0].type !== "content") {
    errors.push("First state must be content");
  }

  // Check for consecutive questions
  for (let i = 0; i < lesson.states.length - 1; i++) {
    if (lesson.states[i].type === "question" && lesson.states[i + 1].type === "question") {
      errors.push(`Consecutive questions at states ${i} and ${i + 1}`);
    }
  }

  // Validate each question state
  lesson.states.forEach((state, index) => {
    if (state.type === "question") {
      const question = state as any;
      if (question.question_format === "mcq") {
        if (!question.options || question.options.length < 2) {
          errors.push(`MCQ question at state ${index} needs at least 2 options`);
        }
        if (typeof question.correct_answer !== "number" || 
            question.correct_answer < 0 || 
            question.correct_answer >= (question.options?.length || 0)) {
          errors.push(`MCQ question at state ${index} has invalid correct answer`);
        }
      }
    }
  });

  return errors;
}
