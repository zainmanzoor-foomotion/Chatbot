import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import type { Message } from '../types'

type Props = {
  message: Message
  index: number
  isResponding: boolean
  isStreaming: boolean
  onRegenerate: (index: number) => void
}

export default function MessageBubble({ message, index, isResponding, isStreaming, onRegenerate }: Props) {
  const [copied, setCopied] = useState(false)

  function handleCopy() {
    navigator.clipboard.writeText(message.content).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  if (message.role === 'user') {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-[75%] bg-[#2f2f2f] rounded-2xl rounded-tr-sm px-4 py-3 text-sm text-white">
          {message.content}
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col mb-4">
      <div className="flex items-start gap-3">
        {/* Bot icon */}
        <div className="shrink-0 w-7 h-7 rounded-full bg-[#10a37f] flex items-center justify-center text-white text-xs font-bold mt-1">
          AI
        </div>
        <div className="flex-1 min-w-0">
          <div className="prose text-sm text-[#ececec] leading-relaxed">
            {message.content && (
              <ReactMarkdown>{message.content}</ReactMarkdown>
            )}
          </div>

          {/* Action buttons — only show when not streaming this message */}
          {!isStreaming && message.content && (
            <div className="flex items-center gap-2 mt-2">
              <button
                onClick={handleCopy}
                className="flex items-center gap-1 text-xs text-[#6b7280] hover:text-white transition-colors px-2 py-1 rounded-md hover:bg-[#2f2f2f]"
              >
                {copied ? (
                  <>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#4caf50" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                    <span className="text-[#4caf50]">Copied</span>
                  </>
                ) : (
                  <>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                    </svg>
                    Copy
                  </>
                )}
              </button>

              <button
                onClick={() => onRegenerate(index)}
                disabled={isResponding}
                className="flex items-center gap-1 text-xs text-[#6b7280] hover:text-white transition-colors px-2 py-1 rounded-md hover:bg-[#2f2f2f] disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="1 4 1 10 7 10" />
                  <path d="M3.51 15a9 9 0 1 0 .49-3.46" />
                </svg>
                Regenerate
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
