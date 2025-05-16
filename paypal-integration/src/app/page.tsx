"use client";
import React, { useState } from "react";

const Home: React.FC = () => {
  const [message, setMessage] = useState("");
  const [chat, setChat] = useState<
    { sender: "user" | "agent"; text: string }[]
  >([]);

  const handleSendMessage = async () => {
    setChat((prevChat) => [...prevChat, { sender: "user", text: message }]);
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const data = await response.json();
    setChat((prevChat) => [
      ...prevChat,
      { sender: "agent", text: data.response },
    ]);
    setMessage("");
  };

  return (
    <div className="min-h-screen h-screen w-screen bg-gray-50 flex flex-col">
      <div className="flex-1 flex flex-col w-full max-w-2xl mx-auto bg-white rounded-none shadow-none p-0">
        <h1 className="text-2xl font-bold text-center text-blue-700 py-4 border-b">
          PayPal Chat Interface
        </h1>
        <div className="flex-1 overflow-y-auto px-4 py-2 space-y-2">
          {chat.map((c, index) => (
            <div
              key={index}
              className={`flex ${c.sender === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`px-4 py-2 rounded-lg max-w-[75%] text-sm shadow
                  ${
                    c.sender === "user"
                      ? "bg-blue-500 text-white rounded-br-none"
                      : "bg-gray-200 text-gray-900 rounded-bl-none"
                  }
                `}
              >
                <span className="block font-semibold mb-1">
                  {c.sender === "user" ? "You" : "Agent"}
                </span>
                {c.text}
              </div>
            </div>
          ))}
        </div>
        <div className="flex gap-2 p-4 border-t bg-white sticky bottom-0">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
            placeholder="Type your message..."
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSendMessage();
            }}
          />
          <button
            onClick={handleSendMessage}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 transition"
            disabled={!message.trim()}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

export default Home;
