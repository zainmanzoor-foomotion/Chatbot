import type { Message } from '../types'

type Props = {
  threads: Record<string, Message[]>
  currentThreadId: string
  isResponding: boolean
  onNewChat: () => void
  onSelectThread: (id: string) => void
}

export default function Sidebar({ threads, currentThreadId, isResponding, onNewChat, onSelectThread }: Props) {
  const threadIds = Object.keys(threads).reverse()

  return (
    <div className="w-60 shrink-0 flex flex-col bg-[#171717] h-full">

      {/* Header */}
      <div className="px-3 pt-4 pb-2">
        <div className="flex items-center gap-2 px-2 mb-3">
          <div className="w-6 h-6 rounded-full bg-[#10a37f] flex items-center justify-center text-white text-[10px] font-bold">
            AI
          </div>
          <span className="text-white text-sm font-semibold">AI Chatbot</span>
        </div>

        <button
          onClick={onNewChat}
          disabled={isResponding}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-[#9ca3af] hover:bg-[#2f2f2f] hover:text-white transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          New Chat
        </button>
      </div>

      <div className="mx-3 border-t border-[#2f2f2f]" />

      {/* Thread list */}
      <div className="flex-1 overflow-y-auto py-2 px-2">
        {threadIds.length === 0 ? (
          <p className="text-xs text-[#4b5563] px-2 py-3">No chats yet</p>
        ) : (
          <>
            <p className="text-[10px] uppercase tracking-widest text-[#4b5563] px-2 mb-1">Recent</p>
            {threadIds.map(tid => {
              const msgs = threads[tid]
              const label = msgs.find(m => m.role === 'user')?.content.slice(0, 28) || `New Chat`
              const isActive = tid === currentThreadId

              return (
                <button
                  key={tid}
                  onClick={() => !isResponding && onSelectThread(tid)}
                  title={msgs.find(m => m.role === 'user')?.content || label}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm truncate transition-colors mb-0.5
                    ${isActive
                      ? 'bg-[#2f2f2f] text-white'
                      : 'text-[#9ca3af] hover:bg-[#212121] hover:text-white'
                    }
                    ${isResponding ? 'cursor-not-allowed' : 'cursor-pointer'}
                  `}
                >
                  {label}
                </button>
              )
            })}
          </>
        )}
      </div>

      {/* Footer */}
      <div className="mx-3 border-t border-[#2f2f2f]" />
      <div className="p-3">
        <div className="flex items-center gap-2 px-2 py-2 text-xs text-[#4b5563]">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          Powered by Groq + LangGraph
        </div>
      </div>
    </div>
  )
}
