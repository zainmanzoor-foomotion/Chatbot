import { useState, useRef, useEffect } from 'react'
import type { KeyboardEvent } from 'react'

export const MODELS = [
  { id: 'openai/gpt-oss-20b', label: 'GPT OSS 20B' },
  { id: 'qwen/qwen3-32b', label: 'Qwen3 32B' },
  { id: 'llama-3.3-70b-versatile', label: 'LLama 3.3 70B' }
]

type Props = {
  onSend: (message: string) => void
  disabled: boolean
  model: string
  onModelChange: (model: string) => void
}

export default function ChatInput({ onSend, disabled, model, onModelChange }: Props) {
  const [value, setValue] = useState('')
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const activeModel = MODELS.find(m => m.id === model) ?? MODELS[0]

  // Close on outside click
  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  function handleSend() {
    const msg = value.trim()
    if (!msg || disabled) return
    setValue('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
    onSend(msg)
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  function handleInput() {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`
  }

  return (
    <div className="p-4">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center gap-2 bg-[#2f2f2f] rounded-2xl px-4 py-3 border border-[#3a3a3a] focus-within:border-[#555]">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={e => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onInput={handleInput}
            disabled={disabled}
            placeholder="Type your message... (Shift+Enter for new line)"
            rows={1}
            className="flex-1 bg-transparent text-sm text-white placeholder-[#6b7280] resize-none outline-none leading-6 max-h-[200px] disabled:opacity-50"
          />

          {/* Custom model dropdown — opens upward */}
          <div ref={dropdownRef} className="relative shrink-0">

            {/* List — renders above the trigger */}
            {dropdownOpen && (
              <div className="absolute bottom-full mb-2 right-0 w-44 bg-[#1a1a1a] border border-[#3a3a3a] rounded-xl shadow-2xl overflow-hidden z-50">
                <p className="px-3 pt-2.5 pb-1.5 text-[10px] uppercase tracking-widest text-[#4b5563] border-b border-[#2f2f2f]">
                  Select Model
                </p>
                {MODELS.map(m => {
                  const isActive = m.id === model
                  return (
                    <button
                      key={m.id}
                      onClick={() => { onModelChange(m.id); setDropdownOpen(false) }}
                      className={`w-full flex items-center justify-between px-3 py-2.5 text-xs transition-colors hover:bg-[#2f2f2f] ${isActive ? 'text-white' : 'text-[#9ca3af]'}`}
                    >
                      <div className="flex items-center gap-2">
                        <span className={`w-1.5 h-1.5 rounded-full ${isActive ? 'bg-[#10a37f]' : 'bg-[#4b5563]'}`} />
                        {m.label}
                      </div>
                      {isActive && (
                        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#10a37f" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                      )}
                    </button>
                  )
                })}
              </div>
            )}

            {/* Trigger */}
            <button
              onClick={() => !disabled && setDropdownOpen(o => !o)}
              disabled={disabled}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs transition-colors disabled:opacity-40 disabled:cursor-not-allowed
                ${dropdownOpen
                  ? 'bg-[#3a3a3a] border-[#6b7280] text-white'
                  : 'bg-[#3a3a3a] border-[#4b5563] text-[#9ca3af] hover:border-[#6b7280] hover:text-white'
                }`}
            >
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="3" />
                <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
              </svg>
              {activeModel.label}
              <svg
                width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
                className={`transition-transform duration-200 ${dropdownOpen ? 'rotate-180' : ''}`}
              >
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </button>
          </div>

          {/* Send button */}
          <button
            onClick={handleSend}
            disabled={disabled || !value.trim()}
            className="shrink-0 w-8 h-8 rounded-lg bg-white flex items-center justify-center transition-opacity disabled:opacity-30 disabled:cursor-not-allowed hover:bg-gray-200"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#000" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
        <p className="text-center text-[10px] text-[#6b7280] mt-2">
          AI can make mistakes. Verify important information.
        </p>
      </div>
    </div>
  )
}
