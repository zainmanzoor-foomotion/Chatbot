import { useEffect, useRef } from 'react'
import MessageBubble from './MessageBubble'
import type { Message } from '../types'

type Props = {
  messages: Message[]
  isResponding: boolean
  isRegenerating: boolean
  toolStatus: string | null
  streamingIndex: number | null
  onRegenerate: (index: number) => void
}

export default function ChatArea({ messages, isResponding, isRegenerating, toolStatus, streamingIndex, onRegenerate }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const isAtBottom = useRef(true)

  // Track whether user has scrolled up
  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    const onScroll = () => {
      isAtBottom.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80
    }
    el.addEventListener('scroll', onScroll, { passive: true })
    return () => el.removeEventListener('scroll', onScroll)
  }, [])

  // During active streaming always scroll to bottom; otherwise only if already at bottom
  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    if (isResponding || isAtBottom.current) {
      el.scrollTop = el.scrollHeight
    }
  }, [messages, isResponding])

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-full bg-[#10a37f] flex items-center justify-center text-white font-bold text-lg mx-auto">
            AI
          </div>
          <h1 className="text-2xl font-semibold text-white">AI Chatbot</h1>
          <p className="text-[#6b7280] text-sm">Ask me anything</p>
        </div>
      </div>
    )
  }

  return (
    <div ref={scrollRef} className="flex-1 overflow-y-auto py-6">
      <div className="max-w-3xl mx-auto px-4">
        {messages.map((msg, i) => {
          // Skip empty assistant placeholder — "Thinking/Regenerating" indicator covers this state
          if (msg.role === 'assistant' && msg.content === '' && i === streamingIndex) return null
          return (
            <MessageBubble
              key={i}
              message={msg}
              index={i}
              isResponding={isResponding}
              isStreaming={i === streamingIndex}
              onRegenerate={onRegenerate}
            />
          )
        })}

        {/* Tool status */}
        {toolStatus && (
          <div className="flex items-center gap-2 text-xs text-[#6b7280] mb-4 ml-10">
            <span className="w-1.5 h-1.5 rounded-full bg-[#10a37f] animate-pulse" />
            {toolStatus}
          </div>
        )}

        {/* Thinking / Regenerating indicator */}
        {isResponding && streamingIndex !== null && messages[streamingIndex]?.content === '' && !toolStatus && (
          <div className="flex items-center gap-3 mb-4">
            <div className="shrink-0 w-7 h-7 rounded-full bg-[#10a37f] flex items-center justify-center text-white text-xs font-bold">
              AI
            </div>
            <span className="text-xs text-[#6b7280] animate-pulse">
              {isRegenerating ? 'Regenerating...' : 'Thinking...'}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
