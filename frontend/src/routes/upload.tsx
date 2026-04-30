import { createFileRoute } from '@tanstack/react-router'
import { AnimatePresence, motion } from 'framer-motion'
import { useUpload } from '../api/useUpload'
import { DropZone } from '../components/DropZone'
import { pageVariants } from '../lib/motion'

export function UploadPage() {
  const upload = useUpload()

  return (
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
        onFile={(file) => upload.mutate(file)}
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
  )
}

export const Route = createFileRoute('/upload')({ component: UploadPage })
