import { motion } from 'framer-motion'
import { itemVariants, listVariants } from '../lib/motion'

interface Props {
  answer: string
  sources: string[]
}

export function AnswerCard({ answer, sources }: Props) {
  return (
    <motion.div
      className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
      initial={{ opacity: 0, y: 12 }}
      animate={{
        opacity: 1,
        y: 0,
        transition: { type: 'spring', stiffness: 300, damping: 28 },
      }}
    >
      <div className="flex gap-4">
        <div className="mt-0.5 w-1 shrink-0 self-stretch rounded-full bg-indigo-400" />
        <div className="flex-1">
          <p className="text-sm leading-relaxed text-slate-800">{answer}</p>
          {sources.length > 0 && (
            <motion.div
              className="mt-4 flex flex-wrap gap-2"
              variants={listVariants}
              initial="initial"
              animate="animate"
            >
              {sources.map((slug) => (
                <motion.a
                  key={slug}
                  href={`/doc/${slug}`}
                  className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600 transition-colors hover:border-indigo-300 hover:text-indigo-700"
                  variants={itemVariants}
                >
                  {slug}
                </motion.a>
              ))}
            </motion.div>
          )}
        </div>
      </div>
    </motion.div>
  )
}
