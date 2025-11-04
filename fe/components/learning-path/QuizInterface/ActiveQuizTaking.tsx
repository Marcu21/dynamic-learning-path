import { useChatLocationUpdater } from '@/context/ChatContext';
import { useEffect } from 'react';

export interface ActiveQuizTakingProps {
  learningPathId: number;
  moduleId: number;
  quizId: number;
  quizAttemptId: number;
}

export const ActiveQuizTaking: React.FC<ActiveQuizTakingProps> = ({ 
  learningPathId, 
  moduleId, 
  quizId, 
  quizAttemptId 
}) => {
  const { setQuizAttemptContext } = useChatLocationUpdater();

  useEffect(() => {
    setQuizAttemptContext(learningPathId, moduleId, quizId, quizAttemptId);
  }, [learningPathId, moduleId, quizId, quizAttemptId, setQuizAttemptContext]);

  return (
    <div>
      <h1>Quiz in Progress</h1>
      {/* Quiz taking interface */}
      {/* Chat assistant will be restricted */}
    </div>
  );
};

export default ActiveQuizTaking; 