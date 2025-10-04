import api from "./axios";

export const getQuiz = async (courseId) => {
  const { data } = await api.post(`/quizzes/generate`, { course_id: courseId });
  return data;
};

export const submitQuizAttempt = async (quizId, answers) => {
  const { data } = await api.post(`/attempts`, { quiz_id: quizId, answers });
  return data;
};
