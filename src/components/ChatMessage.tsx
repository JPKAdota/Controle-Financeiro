"use client";

import { Bot, User } from "lucide-react";

interface ChatMessageProps {
    role: "user" | "assistant";
    content: string;
    isLoading?: boolean;
}

function renderMarkdown(text: string): string {
    // Renderização simples de markdown para HTML
    let html = text
        // Code blocks
        .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre class="bg-gray-900 text-green-400 rounded-lg p-3 my-2 overflow-x-auto text-sm"><code>$2</code></pre>')
        // Inline code
        .replace(/`([^`]+)`/g, '<code class="bg-gray-700 text-emerald-300 px-1.5 py-0.5 rounded text-sm">$1</code>')
        // Bold
        .replace(/\*\*([^*]+)\*\*/g, '<strong class="font-semibold text-white">$1</strong>')
        // Italic
        .replace(/\*([^*]+)\*/g, '<em>$1</em>')
        // Horizontal rule (disclaimer separator)
        .replace(/^---$/gm, '<hr class="border-gray-600 my-3" />')
        // Headers
        .replace(/^### (.+)$/gm, '<h3 class="text-base font-semibold mt-3 mb-1">$1</h3>')
        .replace(/^## (.+)$/gm, '<h2 class="text-lg font-bold mt-3 mb-1">$1</h2>')
        // Unordered lists
        .replace(/^[•\-] (.+)$/gm, '<li class="ml-4 list-disc">$1</li>')
        // Ordered lists
        .replace(/^\d+\. (.+)$/gm, '<li class="ml-4 list-decimal">$1</li>')
        // Line breaks
        .replace(/\n\n/g, '</p><p class="mb-2">')
        .replace(/\n/g, '<br/>');

    return `<p class="mb-2">${html}</p>`;
}

export default function ChatMessage({ role, content, isLoading }: ChatMessageProps) {
    const isUser = role === "user";

    return (
        <div
            className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"} animate-fade-in`}
        >
            {/* Avatar */}
            <div
                className={`flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center shadow-lg ${
                    isUser
                        ? "bg-gradient-to-br from-indigo-500 to-purple-600"
                        : "bg-gradient-to-br from-emerald-500 to-teal-600"
                }`}
            >
                {isUser ? (
                    <User className="w-5 h-5 text-white" />
                ) : (
                    <Bot className="w-5 h-5 text-white" />
                )}
            </div>

            {/* Bubble */}
            <div
                className={`relative max-w-[80%] px-4 py-3 rounded-2xl shadow-md ${
                    isUser
                        ? "bg-gradient-to-br from-indigo-600 to-indigo-700 text-white rounded-tr-md"
                        : "bg-gray-800 text-gray-100 rounded-tl-md border border-gray-700"
                }`}
            >
                {isLoading ? (
                    <div className="flex items-center gap-1.5 py-1 px-2">
                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0ms]"></span>
                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:150ms]"></span>
                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:300ms]"></span>
                    </div>
                ) : isUser ? (
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{content}</p>
                ) : (
                    <div
                        className="text-sm leading-relaxed prose prose-invert prose-sm max-w-none"
                        dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }}
                    />
                )}
            </div>
        </div>
    );
}
