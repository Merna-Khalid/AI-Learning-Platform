import axios from "axios";

export const fetchTopics = async (courseId) => {
  const res = await axios.get(`http://localhost:8000/topics/${courseId}`);
  return res.data;
};
