import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import type { Message } from '../types'

type Props = {
  message: Message
  index: number
  isResponding: boolean
  isStreaming: boolean
  isRegenerating: boolean
  onRegenerate: (index: number) => void
}

export default function MessageBubble({ message, index, isResponding, isStreaming, isRegenerating, onRegenerate }: Props) {
  const [copied, setCopied] = useState(false)
  const [isSlow, setIsSlow] = useState(false)

  const isThinking = isStreaming && !message.content && !message.imageUrl

  useEffect(() => {
    if (!isThinking) { setIsSlow(false); return }
    const timer = setTimeout(() => setIsSlow(true), 5000)
    return () => clearTimeout(timer)
  }, [isThinking])

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
          {/* Inline thinking indicator — stays at the correct slot, no bottom bubble */}
          {isThinking && (
            <span className="text-xs text-[#6b7280] animate-pulse">
              {isSlow
                ? 'Taking longer than usual...'
                : isRegenerating ? 'Regenerating...' : 'Thinking...'}
            </span>
          )}

          {message.imageUrl && (
            <div className="mb-3">
              <img
                src={message.imageUrl}
                alt="Generated image"
                className="max-w-full max-h-[512px] rounded-lg border border-[#3f3f3f] object-contain"
              />
              {!isStreaming && (
                <a
                  href={message.imageUrl}
                  download="generated-image.png"
                  className="inline-flex items-center gap-1 mt-2 text-xs text-[#6b7280] hover:text-white transition-colors px-2 py-1 rounded-md hover:bg-[#2f2f2f]"
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="7 10 12 15 17 10" />
                    <line x1="12" y1="15" x2="12" y2="3" />
                  </svg>
                  Download
                </a>
              )}
            </div>
          )}
          {/* Hide text when an image was generated — the LLM text is just "Here's your image!" which is redundant */}
          {!message.imageUrl && (
            <div className="prose text-sm text-[#ececec] leading-relaxed">
              {message.content && (
                <ReactMarkdown components={{ img: () => null }}>{message.content}</ReactMarkdown>
              )}
            </div>
          )}

          {/* Action buttons — only show when not streaming this message */}
          {!isStreaming && (message.content || message.imageUrl) && (
            <div className="flex items-center gap-2 mt-2">
              {/* Copy — only for text-only responses, not when an image was generated */}
              {!message.imageUrl && message.content && (
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
              )}

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
