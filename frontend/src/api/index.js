import { useState } from "react";
import { askQuestion } from "../api/rag";

const AskAssistant = () => {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");

  const handleAsk = async () => {
    const response = await askQuestion(query);
    setAnswer(response);
  };

  return (
    <div>
      <input
        type="text"
        placeholder="Ask a question..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <button onClick={handleAsk}>Ask</button>
      {answer && <p>Answer: {answer}</p>}
    </div>
  );
};

export default AskAssistant;
