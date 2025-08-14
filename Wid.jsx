import React, { useState, useEffect } from "react";

function Wid() {
  const [open, setOpen] = useState(false);
  const [isClicked, setIsClicked] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [hasTyped, setHasTyped] = useState(false);

  const handleInputChange = (e) => {
    setInput(e.target.value);
    setHasTyped(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { sender: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question: input.trim() }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        const watsonError = {
          sender: "watson-nlu",
          text: `Watson NLU API error: ${errorData.error || "Unexpected issue"}`,
        };
        setMessages((prev) => [...prev, watsonError]);
        console.error("Watson API error:", errorData);
      } else {
        const data = await res.json();
        const watsonMessage = {
          sender: "watson-nlu",
          text: data.response || "No relevant keywords found.",
        };
        setMessages((prev) => [...prev, watsonMessage]);
      }
    } catch (error) {
      const errorMessage = {
        sender: "watson-nlu",
        text: "Oops! Couldn't reach Watson NLU backend.",
      };
      setMessages((prev) => [...prev, errorMessage]);
      console.error("Network error:", error);
    } finally {
      setInput("");
      setLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setHasTyped(false);
    setIsClicked(false);
  };

  useEffect(() => {
    const el = document.querySelector(".message-list");
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  return (
    <div className="widget">
      {open && (
        <div className="window">
          <div className="chat-header">
            ChatBot
            <button
              className={`but ${isClicked ? "clicked" : ""}`}
              onClick={() => {
                setIsClicked(true);
                clearChat();
              }}
            >
              <i className="bi bi-arrow-clockwise"></i> Clear Chat
            </button>
            <button className="close-btn" onClick={() => setOpen(false)}>
              ×
            </button>
          </div>
          <div className="chat-body">
            {!hasTyped && (
              <div>
                <img className="img"  />
                <p className="text">How can I assist you?</p>
              </div>
            )}
            <div className="message-list">
              {messages.map((msg, index) => (
                <div key={index} className={`message ${msg.sender}`}>
                  <div className="bubble">{msg.text}</div>
                </div>
              ))}
            </div>
            <form onSubmit={handleSubmit} className="input-form">
              <input
                type="text"
                placeholder="Type your question..."
                value={input}
                onChange={handleInputChange}
                required
                className="input-text"
              />
              <button type="submit" disabled={loading} className="submit">
                {loading ? "..." : <i className="bi bi-send-fill"></i>}
              </button>
            </form>
          </div>
        </div>
      )}
      <button className="chat-button" onClick={() => setOpen(!open)}>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          fill="currentColor"
          className="bi bi-chat-dots-fill"
          viewBox="0 0 16 16"
        >
          <path d="M16 8c0 3.866-3.582 7-8 7a9 9 0 0 1-2.347-.306c-.584.296-1.925.864-4.181 1.234-.2.032-.352-.176-.273-.362.354-.836.674-1.95.77-2.966C.744 11.37 0 9.76 0 8c0-3.866 3.582-7 8-7s8 3.134 8 7M5 8a1 1 0 1 0-2 0 1 1 0 0 0 2 0m4 0a1 1 0 1 0-2 0 1 1 0 0 0 2 0m3 1a1 1 0 1 0 0-2 1 1 0 0 0 0 2" />
        </svg>
      </button>
    </div>
  );
}

export default Wid;
