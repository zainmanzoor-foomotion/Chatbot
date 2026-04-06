import { useState, useRef } from 'react'
import Sidebar from './components/Sidebar'
import ChatArea from './components/ChatArea'
import ChatInput, { MODELS } from './components/ChatInput'
import type { Message } from './types'

function genId() {
  return crypto.randomUUID()
}

const initialId = genId()

export default function App() {
  const [threads, setThreads] = useState<Record<string, Message[]>>({ [initialId]: [] })
  const [currentThreadId, setCurrentThreadId] = useState<string>(initialId)
  const [isResponding, setIsResponding] = useState(false)
  const [isRegenerating, setIsRegenerating] = useState(false)
  const [toolStatus, setToolStatus] = useState<string | null>(null)
  const [streamingIndex, setStreamingIndex] = useState<number | null>(null)
  const [selectedModel, setSelectedModel] = useState(MODELS[0].id)
  const currentThreadIdRef = useRef(currentThreadId)
  currentThreadIdRef.current = currentThreadId
  const assistantIdxRef = useRef(0)

  function newChat() {
    const tid = genId()
    setThreads(prev => ({ ...prev, [tid]: [] }))
    setCurrentThreadId(tid)
  }

  function selectThread(tid: string) {
    if (!isResponding) setCurrentThreadId(tid)
  }

  async function streamAssistant(message: string, threadId: string, skipUserAppend = false, targetIndex?: number) {
    // Compute the assistant slot index BEFORE any state updates to avoid stale closure
    if (targetIndex !== undefined) {
      // Regenerate: write into the existing slot in-place
      assistantIdxRef.current = targetIndex
      setStreamingIndex(targetIndex)
      setThreads(prev => {
        const msgs = [...(prev[threadId] || [])]
        msgs[targetIndex] = { role: 'assistant', content: '' }
        return { ...prev, [threadId]: msgs }
      })
    } else {
      // Normal send: compute expected index from current state length
      const currentLen = (threads[threadId] || []).length
      assistantIdxRef.current = skipUserAppend ? currentLen : currentLen + 1
      setStreamingIndex(assistantIdxRef.current)
      if (!skipUserAppend) {
        setThreads(prev => ({
          ...prev,
          [threadId]: [...(prev[threadId] || []), { role: 'user', content: message }],
        }))
      }
      setThreads(prev => ({
        ...prev,
        [threadId]: [...(prev[threadId] || []), { role: 'assistant', content: '' }],
      }))
    }

    setIsResponding(true)
    setToolStatus(null)

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ thread_id: threadId, message, model: selectedModel }),
      })

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let fullContent = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          let data: any
          try { data = JSON.parse(line.slice(6)) } catch { continue }

          if (data.type === 'token') {
            fullContent += data.content
            const snapshot = fullContent
            setThreads(prev => {
              const msgs = [...(prev[threadId] || [])]
              const idx = assistantIdxRef.current < msgs.length ? assistantIdxRef.current : msgs.length - 1
              msgs[idx] = { ...msgs[idx], role: 'assistant', content: snapshot }
              return { ...prev, [threadId]: msgs }
            })
          } else if (data.type === 'image') {
            const imageUrl = `data:image/png;base64,${data.data}`
            setThreads(prev => {
              const msgs = [...(prev[threadId] || [])]
              const idx = assistantIdxRef.current < msgs.length ? assistantIdxRef.current : msgs.length - 1
              msgs[idx] = { ...msgs[idx], imageUrl }
              return { ...prev, [threadId]: msgs }
            })
          } else if (data.type === 'tool') {
            setToolStatus(`Using: ${(data.tools as string[]).join(', ')}`)
          } else if (data.type === 'error') {
            fullContent = data.content
            setThreads(prev => {
              const msgs = [...(prev[threadId] || [])]
              const idx = assistantIdxRef.current < msgs.length ? assistantIdxRef.current : msgs.length - 1
              msgs[idx] = { ...msgs[idx], role: 'assistant', content: data.content }
              return { ...prev, [threadId]: msgs }
            })
            if (data.new_thread_id) {
              setThreads(prev => ({ ...prev, [data.new_thread_id]: [] }))
              setCurrentThreadId(data.new_thread_id)
            }
          }
        }
      }
    } catch (err) {
      const msg = `⚠️ ${err}`
      setThreads(prev => {
        const msgs = [...(prev[threadId] || [])]
        const lastIdx = msgs.length - 1
        if (msgs[lastIdx]?.role === 'assistant') {
          msgs[lastIdx] = { role: 'assistant', content: msg }
        }
        return { ...prev, [threadId]: msgs }
      })
    } finally {
      setIsResponding(false)
      setIsRegenerating(false)
      setToolStatus(null)
      setStreamingIndex(null)
    }
  }

  function sendMessage(message: string) {
    streamAssistant(message, currentThreadId)
  }

  function regenerate(msgIndex: number) {
    if (isResponding) return
    const msgs = threads[currentThreadId]
    const userMsg = msgs[msgIndex - 1]
    if (!userMsg) return
    setIsRegenerating(true)
    // Pass msgIndex so the stream writes back into the same slot
    streamAssistant(userMsg.content, currentThreadId, true, msgIndex)
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden">
      <Sidebar
        threads={threads}
        currentThreadId={currentThreadId}
        isResponding={isResponding}
        onNewChat={newChat}
        onSelectThread={selectThread}
      />
      <div className="flex flex-col flex-1 min-w-0">
        <ChatArea
          messages={threads[currentThreadId] || []}
          isResponding={isResponding}
          isRegenerating={isRegenerating}
          toolStatus={toolStatus}
          streamingIndex={streamingIndex}
          onRegenerate={regenerate}
        />
        <ChatInput onSend={sendMessage} disabled={isResponding} model={selectedModel} onModelChange={setSelectedModel} />
      </div>
    </div>
  )
}
