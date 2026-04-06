export type Message = {
  role: 'user' | 'assistant'
  content: string
  imageUrl?: string
}

export type ThreadMeta = {
  id: string
  first_message: string
}
