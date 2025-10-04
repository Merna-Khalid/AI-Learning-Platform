import api from "./index";

/**
 * Ask a question to the RAG system
 * @param {string} query - The user question
 * @param {number} [top_k=5] - How many docs to retrieve
 * @returns {Promise<string>} - The generated answer
 */
export const askQuestion = async (query, top_k = 5) => {
  const res = await api.post("/rag/ask", { query, top_k });
  return res.data.answer;
};

/**
 * Generate a quiz for a given topic
 * @param {string} topic - Topic name
 * @param {number} [num_questions=5] - Number of questions
 * @param {number} [top_k=10] - Retrieval size
 * @returns {Promise<Array>} - Array of quiz questions
 */
export const generateQuiz = async (topic, num_questions = 5, top_k = 10) => {
  const res = await api.post("/rag/quiz", { topic, num_questions, top_k });
  return res.data.questions;
};

/**
 * Explain an answer (feedback for student answer)
 * @param {object} payload - { question, student_answer, correct_answer, top_k }
 * @returns {Promise<string>} - The generated explanation
 */
export const explainAnswer = async (payload) => {
  const res = await api.post("/rag/explain", payload);
  return res.data.explanation;
};
