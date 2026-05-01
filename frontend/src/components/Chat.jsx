import { useState, useRef, useEffect } from "react";
import axios from "axios";

const WELCOME_MESSAGE = {
  role: "assistant",
  content:
    "Hi! I'm the iPractest assistant. I can help you with information about our IELTS preparation platform, practice tests, band score tracking, and general IELTS tips. How can I help you today?",
};

export default function Chat() {
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const buildHistory = (msgs) =>
    msgs
      .filter((m) => m.role !== "system")
      .map((m) => ({ role: m.role, content: m.content }));

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg = { role: "user", content: text };
    const updated = [...messages, userMsg];
    setMessages(updated);
    setInput("");
    setLoading(true);

    try {
      const { data } = await axios.post("/api/chat", {
        message: text,
        history: buildHistory(messages),
      });
      setMessages([...updated, { role: "assistant", content: data.response }]);
    } catch {
      setMessages([
        ...updated,
        {
          role: "assistant",
          content: "Sorry, I encountered an error. Please try again.",
        },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="chat-wrapper">
      <div className="chat-header">
        <div className="chat-header-logo">
          <span className="logo-icon">i</span>
          <span className="logo-text">Practest</span>
        </div>
        <p className="chat-header-sub">IELTS Preparation Assistant</p>
      </div>

      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message-row ${msg.role}`}>
            {msg.role === "assistant" && (
              <div className="avatar">
                <span>IP</span>
              </div>
            )}
            <div className={`bubble ${msg.role}`}>
              <p>{msg.content}</p>
            </div>
          </div>
        ))}

        {loading && (
          <div className="message-row assistant">
            <div className="avatar">
              <span>IP</span>
            </div>
            <div className="bubble assistant typing">
              <span className="dot" />
              <span className="dot" />
              <span className="dot" />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="chat-input-area">
        <textarea
          ref={inputRef}
          className="chat-input"
          rows={1}
          placeholder="Ask me anything about iPractest or IELTS..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <button
          className="send-btn"
          onClick={sendMessage}
          disabled={loading || !input.trim()}
        >
          <SendIcon />
        </button>
      </div>
    </div>
  );
}

function SendIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  );
}
