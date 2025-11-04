import React, { useState, useEffect } from 'react';
import { useChatLocationUpdater } from '@/context/ChatContext';
import ActiveQuizTaking from './ActiveQuizTaking';
import QuizView from './QuizView';

export interface QuizFlowProps {
  learningPathId: number;
  moduleId: number;
  quizId: number;
}

export const QuizFlowManager: React.FC<QuizFlowProps> = ({
  learningPathId,
  moduleId,
  quizId
}) => {
  const [isQuizActive, setIsQuizActive] = useState(false);
  const [quizAttemptId, setQuizAttemptId] = useState<number | undefined>();

  // ⬇️ folosim API-ul actual din ChatContext
  const { setQuizContext, setQuizAttemptContext } = useChatLocationUpdater();

  useEffect(() => {
    if (isQuizActive && quizAttemptId) {
      // utilizatorul dă efectiv quizul (context restricționat)
      setQuizAttemptContext(learningPathId, moduleId, quizId, quizAttemptId);
    } else {
      // doar vizualizează info despre quiz (context “quiz”)
      setQuizContext(learningPathId, moduleId, quizId);
    }
  }, [
    isQuizActive,
    quizAttemptId,
    learningPathId,
    moduleId,
    quizId,
    setQuizAttemptContext,
    setQuizContext
  ]);

  const startQuiz = () => {
    setIsQuizActive(true);
    setQuizAttemptId(123); // TODO: setează aici ID-ul real al attempt-ului după start
  };

  const finishQuiz = () => {
    setIsQuizActive(false);
    setQuizAttemptId(undefined);
  };

  return (
    <div>
      {isQuizActive && quizAttemptId ? (
        <ActiveQuizTaking
          learningPathId={learningPathId}
          moduleId={moduleId}
          quizId={quizId}
          quizAttemptId={quizAttemptId}
        />
      ) : (
        <QuizView
          learningPathId={learningPathId}
          moduleId={moduleId}
          quizId={quizId}
        />
      )}

      <div style={{ marginTop: 24 }}>
        {isQuizActive ? (
          <button onClick={finishQuiz}>Finish Quiz</button>
        ) : (
          <button onClick={startQuiz}>Start Quiz</button>
        )}
      </div>
    </div>
  );
};

export default QuizFlowManager;