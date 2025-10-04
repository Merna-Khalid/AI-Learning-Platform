import api from "./axios";

export const getProgress = async (courseId) => {
  const { data } = await api.get(`/progress/${courseId}`);
  return data;
};
