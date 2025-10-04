import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000/api", // match FastAPI prefix
});

export default api;
