import { createFileRoute } from '@tanstack/react-router'
import { AnimatePresence, motion } from 'framer-motion'
import { useState } from 'react'
import { useUpload } from '../api/useUpload'
import { useSettings } from '../api/useSettings'
import { DropZone } from '../components/DropZone'
import { pageVariants } from '../lib/motion'

function ApprovalModal({
  file,
  onApprove,
  onSkip,
  onCancel,
  visionEnabled,
  taggerIsAnthropic,
  linkerIsAnthropic,
}: {
  file: File
  onApprove: () => void
  onSkip: () => void
  onCancel: () => void
  visionEnabled: boolean
  taggerIsAnthropic: boolean
  linkerIsAnthropic: boolean
}) {
  const isPdf = file.name.toLowerCase().endsWith('.pdf')
  const showVision = visionEnabled && isPdf

  return (
    <motion.div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onCancel}
    >
      <motion.div
        className="mx-4 w-full max-w-md rounded-lg border border-slate-700 bg-slate-900 p-6 shadow-xl"
        initial={{ opacity: 0, scale: 0.95, y: 8 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 8 }}
        transition={{ duration: 0.15 }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="mb-1 text-sm font-semibold uppercase tracking-widest text-indigo-400">
          Approvazione API
        </h2>
        <p className="mb-4 text-xs text-slate-400">
          <span className="font-mono text-slate-300">{file.name}</span>
        </p>

        <p className="mb-3 text-sm text-slate-300">
          Questo documento richiederà chiamate all&apos;API Anthropic:
        </p>

        <ul className="mb-6 space-y-1.5 text-sm">
          {showVision && (
            <li className="flex items-center gap-2 text-emerald-400">
              <span className="text-slate-500">•</span>
              Descrizione immagini (Vision)
            </li>
          )}
          {taggerIsAnthropic && (
            <li className="flex items-center gap-2 text-emerald-400">
              <span className="text-slate-500">•</span>
              Generazione tag automatici
            </li>
          )}
          {linkerIsAnthropic && (
            <li className="flex items-center gap-2 text-emerald-400">
              <span className="text-slate-500">•</span>
              Generazione wikilink
            </li>
          )}
          {!showVision && !taggerIsAnthropic && !linkerIsAnthropic && (
            <li className="text-slate-500 italic">Nessuna chiamata API rilevata.</li>
          )}
        </ul>

        <div className="flex gap-3 justify-end">
          <button
            className="rounded border border-slate-700 bg-slate-800 px-4 py-2 text-sm text-slate-300 transition-colors hover:bg-slate-700 hover:text-white"
            onClick={onSkip}
          >
            Salta API
          </button>
          <button
            className="rounded border border-indigo-500 bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-indigo-500"
            onClick={onApprove}
          >
            Approva →
          </button>
        </div>
      </motion.div>
    </motion.div>
  )
}

export function UploadPage() {
  const upload = useUpload()
  const settings = useSettings()
  const [pendingFile, setPendingFile] = useState<File | null>(null)

  function handleFile(file: File) {
    if (settings.data?.anthropic_require_approval) {
      setPendingFile(file)
    } else {
      upload.mutate({ file, skipApi: false })
    }
  }

  function handleApprove() {
    if (!pendingFile) return
    upload.mutate({ file: pendingFile, skipApi: false })
    setPendingFile(null)
  }

  function handleSkip() {
    if (!pendingFile) return
    upload.mutate({ file: pendingFile, skipApi: true })
    setPendingFile(null)
  }

  function handleCancel() {
    setPendingFile(null)
  }

  const settingsData = settings.data
  const visionEnabled = settingsData?.vision_enabled ?? true
  const taggerIsAnthropic = settingsData ? settingsData.tagger.backend === 'anthropic' : true
  const linkerIsAnthropic = settingsData ? settingsData.linker.backend === 'anthropic' : true

  return (
    <>
      <AnimatePresence>
        {pendingFile && (
          <ApprovalModal
            file={pendingFile}
            onApprove={handleApprove}
            onSkip={handleSkip}
            onCancel={handleCancel}
            visionEnabled={visionEnabled}
            taggerIsAnthropic={taggerIsAnthropic}
            linkerIsAnthropic={linkerIsAnthropic}
          />
        )}
      </AnimatePresence>

      <motion.div
        className="mx-auto max-w-xl"
        variants={pageVariants}
        initial="initial"
        animate="animate"
        exit="exit"
      >
        <h1 className="mb-8 text-2xl font-bold tracking-tight text-slate-900">
          Upload Document
        </h1>

        <DropZone
          onFile={handleFile}
          isPending={upload.isPending}
        />

        <AnimatePresence>
          {upload.isPending && (
            <motion.div
              className="mt-4 overflow-hidden rounded-lg bg-slate-100"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <motion.div
                className="h-1.5 bg-indigo-500"
                initial={{ width: '0%' }}
                animate={{ width: '90%' }}
                transition={{ duration: 2, ease: 'easeOut' }}
              />
            </motion.div>
          )}

          {upload.isSuccess && (
            <motion.p
              className="mt-4 rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-700"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
            >
              Ingestion started for <strong>{upload.data.filename}</strong>.
            </motion.p>
          )}

          {upload.isError && (
            <motion.p
              className="mt-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
            >
              {upload.error.message}
            </motion.p>
          )}
        </AnimatePresence>
      </motion.div>
    </>
  )
}

export const Route = createFileRoute('/upload')({ component: UploadPage })
