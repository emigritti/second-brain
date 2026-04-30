import { motion } from 'framer-motion'
import { useRef, useState } from 'react'

interface Props {
  onFile: (file: File) => void
  isPending: boolean
}

export function DropZone({ onFile, isPending }: Props) {
  const [isDragging, setIsDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  function handleDrop(e: React.DragEvent) {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) onFile(file)
  }

  return (
    <motion.div
      className={`flex flex-col items-center justify-center gap-4 rounded-xl border-2 border-dashed px-8 py-16 transition-colors ${
        isDragging
          ? 'border-indigo-400 bg-indigo-50'
          : 'border-slate-300 bg-white'
      }`}
      animate={isDragging ? { scale: 1.01 } : { scale: 1 }}
      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
      onDragOver={(e) => {
        e.preventDefault()
        setIsDragging(true)
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-50">
        <svg
          className="h-6 w-6 text-indigo-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.5}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5"
          />
        </svg>
      </div>

      <div className="text-center">
        <p className="text-sm font-medium text-slate-700">
          Drag &amp; drop a file here
        </p>
        <p className="mt-1 text-xs text-slate-400">
          PDF, DOCX, XLSX, PPTX, HTML, EPUB, MP3 and more
        </p>
      </div>

      <label
        className="cursor-pointer rounded-lg bg-indigo-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-600"
      >
        Choose file
        <input
          ref={inputRef}
          type="file"
          className="sr-only"
          aria-label="Choose file"
          disabled={isPending}
          onChange={(e) => {
            const f = e.target.files?.[0]
            if (f) onFile(f)
          }}
        />
      </label>
    </motion.div>
  )
}
