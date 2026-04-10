/**
 * Chat test panel — lets dev test their skill.md by chatting with AI.
 * In v1 this is a UI placeholder that shows the skill content and simulates
 * what the AI would "know" when the app is activated.
 */

"use client";

import { useState } from "react";

interface ChatTestPanelProps {
  appId: string;
  skillContent: string | null;
}

interface Message {
  role: "user" | "assistant" | "system";
  content: string;
}

export function ChatTestPanel({ appId, skillContent }: ChatTestPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isConnected, setIsConnected] = useState(false);

  function handleTest() {
    if (!skillContent) return;
    setIsConnected(true);
    setMessages([
      {
        role: "system",
        content: `[skill.md loaded for ${appId}]\n\nAI đã được inject prompt từ skill.md. Trong production, AI sẽ hiểu các capabilities sau:\n\n${skillContent.slice(0, 500)}${skillContent.length > 500 ? "..." : ""}`,
      },
    ]);
  }

  function handleSend() {
    if (!input.trim()) return;

    const userMsg: Message = { role: "user", content: input };
    const botMsg: Message = {
      role: "assistant",
      content: `[Sandbox] Đã nhận câu hỏi: "${input}"\n\nTrong production, AI sẽ trả lời dựa trên skill.md của app ${appId}. Hiện tại đang ở chế độ sandbox — kết nối với Lumina Core AI để test thật.`,
    };

    setMessages((prev) => [...prev, userMsg, botMsg]);
    setInput("");
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${isConnected ? "bg-green-500" : "bg-gray-300"}`}
          />
          <span className="text-sm font-medium text-gray-700">Chat Test</span>
        </div>
        <button
          onClick={handleTest}
          disabled={!skillContent}
          className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isConnected ? "Reload Skill" : "Test"}
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && (
          <div className="text-center text-sm text-gray-400 mt-8">
            Nhấn "Test" để inject skill.md và bắt đầu chat
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`text-sm rounded-lg px-3 py-2 max-w-[85%] ${
              msg.role === "user"
                ? "ml-auto bg-blue-600 text-white"
                : msg.role === "system"
                  ? "bg-yellow-50 border border-yellow-200 text-yellow-800"
                  : "bg-gray-100 text-gray-800"
            }`}
          >
            <pre className="whitespace-pre-wrap font-sans">{msg.content}</pre>
          </div>
        ))}
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-3">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={isConnected ? "Nhập tin nhắn..." : "Nhấn Test trước..."}
            disabled={!isConnected}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
          />
          <button
            type="submit"
            disabled={!isConnected || !input.trim()}
            className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            Gửi
          </button>
        </form>
      </div>
    </div>
  );
}
