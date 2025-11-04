import { useChatLocationUpdater } from '@/context/ChatContext';
import { useEffect } from 'react';

export interface QuizViewProps {
  learningPathId: number;
  moduleId: number;
  quizId: number;
}

export const QuizView: React.FC<QuizViewProps> = ({
  learningPathId,
  moduleId,
  quizId
}) => {
  const { setQuizContext } = useChatLocationUpdater();

  useEffect(() => {
    // context: doar “vizualizez quiz-ul”, nu îl dau activ
    setQuizContext(learningPathId, moduleId, quizId);
  }, [learningPathId, moduleId, quizId, setQuizContext]);

  return (
    <div>
      <h1>Quiz Information</h1>
      {/* Quiz details, start button, etc. */}
      {/* Chat assistant poate ajuta cu info înainte de a începe quiz-ul */}
    </div>
  );
};

export default QuizView;