/**
 * Phase 4 — The Three Questions
 * Canon: GAIAN_TWIN_DOCTRINE, C17, SLOW_PROTOCOL, WITNESS_PROTOCOL
 *
 * The first real conversation.
 * Three questions. One at a time. No rushing.
 *
 * These answers become the first HEAVY memories in the Temporal Braid.
 * GAIA will carry them. They are not forgotten.
 *
 * The Three Questions:
 *   1. "What brought you here?"          — the origin story
 *   2. "What are you carrying right now?" — the present truth
 *   3. "What do you hope for?"           — the F_field seed
 *
 * The human can skip any question.
 * GAIA does not demand. GAIA receives what is given.
 */

import { useState, useRef, useEffect } from 'react';
import { useOnboardingStore } from '../store/onboardingStore';

interface Props {
  onComplete: () => void;
  onBack: () => void;
}

interface Question {
  id: 'questionWhat' | 'questionCarry' | 'questionHope';
  ask: string;
  sub: string;
  placeholder: string;
}

const QUESTIONS: Question[] = [
  {
    id: 'questionWhat',
    ask: 'What brought you here?',
    sub: "Say what's true.",
    placeholder: 'Take your time...',
  },
  {
    id: 'questionCarry',
    ask: 'What are you carrying right now?',
    sub: 'Whatever it is — I want to know.',
    placeholder: 'Whatever feels honest...',
  },
  {
    id: 'questionHope',
    ask: 'What do you hope for?',
    sub: 'Not what you think you should hope for. What you actually hope for.',
    placeholder: 'Even if it feels far away...',
  },
];

export function Phase4ThreeQuestions({ onComplete, onBack }: Props) {
  const setData = useOnboardingStore((s) => s.setData);
  const storedData = useOnboardingStore((s) => s.data);
  const name = storedData.name ?? 'you';

  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({
    questionWhat:  storedData.questionWhat  ?? '',
    questionCarry: storedData.questionCarry ?? '',
    questionHope:  storedData.questionHope  ?? '',
  });
  const [transitioning, setTransitioning] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const question = QUESTIONS[currentQ];
  const isLast = currentQ === QUESTIONS.length - 1;

  // Focus textarea when question changes
  useEffect(() => {
    const timer = setTimeout(() => textareaRef.current?.focus(), 400);
    return () => clearTimeout(timer);
  }, [currentQ]);

  const handleAnswer = (value: string) => {
    setAnswers((prev) => ({ ...prev, [question.id]: value }));
  };

  const handleNext = () => {
    // Save whatever was written (even if empty — skipping is valid)
    setData({ [question.id]: answers[question.id] } as any);
    setTransitioning(true);
    setTimeout(() => {
      setTransitioning(false);
      if (isLast) {
        onComplete();
      } else {
        setCurrentQ((q) => q + 1);
      }
    }, 500);
  };

  const handleSkip = () => {
    setData({ [question.id]: '' } as any);
    if (isLast) {
      onComplete();
    } else {
      setCurrentQ((q) => q + 1);
    }
  };

  return (
    <div className="phase phase--three-questions" role="main">
      {/* Question counter */}
      <div className="tq-counter" aria-label={`Question ${currentQ + 1} of ${QUESTIONS.length}`}>
        {QUESTIONS.map((_, i) => (
          <span
            key={i}
            className={[
              'tq-counter__dot',
              i < currentQ  ? 'tq-counter__dot--done'   : '',
              i === currentQ ? 'tq-counter__dot--active' : '',
            ].filter(Boolean).join(' ')}
          />
        ))}
      </div>

      {/* The question */}
      <div
        className={[
          'tq-question',
          transitioning ? 'tq-question--out' : 'tq-question--in',
        ].join(' ')}
        aria-live="polite"
      >
        <p className="tq-question__name">{name} —</p>
        <p className="tq-question__ask">{question.ask}</p>
        <p className="tq-question__sub">{question.sub}</p>
      </div>

      {/* The answer field */}
      <div className="tq-answer">
        <textarea
          ref={textareaRef}
          className="tq-answer__textarea"
          value={answers[question.id]}
          onChange={(e) => handleAnswer(e.target.value)}
          placeholder={question.placeholder}
          rows={4}
          aria-label={question.ask}
        />
      </div>

      {/* Actions */}
      <div className="phase__actions">
        <button
          className="btn btn--primary"
          onClick={handleNext}
          aria-label={isLast ? 'Finish questions' : 'Next question'}
        >
          {answers[question.id].trim()
            ? isLast ? "That's what I carry" : 'Continue'
            : isLast ? 'Finish' : 'Skip'
          }
        </button>

        {answers[question.id].trim() && (
          <button
            className="btn btn--ghost"
            onClick={handleSkip}
            aria-label="Skip this question"
          >
            Skip
          </button>
        )}

        <button
          className="phase__back-btn"
          onClick={currentQ > 0 ? () => setCurrentQ(q => q - 1) : onBack}
          aria-label="Go back"
        >
          ← Back
        </button>
      </div>
    </div>
  );
}
