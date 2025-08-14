import React, { useState, useEffect } from 'react';

const ChatWidget = () => {
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    // Expand widget on initial load
    setExpanded(true);

    // Optional: auto-collapse after a few seconds
    const timer = setTimeout(() => setExpanded(false), 4000);
     return () => clearTimeout(timer);
  }, []);

  const handleClick = () => {
    setExpanded(false);
  };

  return (
    <div
      className={`chat-widget ${expanded ? 'expanded' : 'collapsed'}`}
      onClick={handleClick}
    >
      {expanded && <div className="chat-message">I can help!</div>}
    </div>
  );
};

export default ChatWidget;
