import { createFileRoute } from '@tanstack/react-router'
import { AnimatePresence, motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import {
  useSettings,
  useSaveSettings,
  useTestLocalAI,
  useTestOllama,
  type TaskConfig,
} from '../api/useSettings'
import { pageVariants } from '../lib/motion'

function BackendToggle({
  name,
  label,
  value,
  onChange,
}: {
  name: string
  label: string
  value: 'anthropic' | 'localai' | 'ollama'
  onChange: (v: 'anthropic' | 'localai' | 'ollama') => void
}) {
  return (
    <fieldset>
      <legend className="mb-1.5 block text-xs font-medium text-slate-600">
        Backend
      </legend>
      <div className="flex gap-4">
        {(['anthropic', 'localai', 'ollama'] as const).map((opt) => (
          <label key={opt} className="flex cursor-pointer items-center gap-1.5">
            <input
              type="radio"
              name={name}
              value={opt}
              checked={value === opt}
              onChange={() => onChange(opt)}
              aria-label={`${label} ${opt}`}
            />
            <span className="text-sm capitalize text-slate-700">{opt}</span>
          </label>
        ))}
      </div>
    </fieldset>
  )
}

function TaskSection({
  task,
  label,
  config,
  onChange,
}: {
  task: 'tagger' | 'linker'
  label: string
  config: TaskConfig
  onChange: (c: TaskConfig) => void
}) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5">
      <h3 className="mb-4 text-sm font-semibold text-slate-900">{label}</h3>
      <div className="flex flex-col gap-4">
        <BackendToggle
          name={`${task}_backend`}
          label={label}
          value={config.backend}
          onChange={(backend) => onChange({ ...config, backend })}
        />

        <AnimatePresence mode="wait">
          {config.backend === 'anthropic' ? (
            <motion.div
              key="anthropic"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <label
                className="block text-xs font-medium text-slate-600"
                htmlFor={`${task}_anthropic_model`}
              >
                Anthropic model
              </label>
              <input
                id={`${task}_anthropic_model`}
                className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-900 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
                value={config.anthropic_model}
                onChange={(e) =>
                  onChange({ ...config, anthropic_model: e.target.value })
                }
              />
            </motion.div>
          ) : config.backend === 'localai' ? (
            <motion.div
              key="localai"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <label
                className="block text-xs font-medium text-slate-600"
                htmlFor={`${task}_localai_model`}
              >
                LocalAI model
              </label>
              <input
                id={`${task}_localai_model`}
                aria-label={`${label} localai model`}
                className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-900 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
                value={config.localai_model}
                onChange={(e) =>
                  onChange({ ...config, localai_model: e.target.value })
                }
              />
            </motion.div>
          ) : (
            <motion.div
              key="ollama"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <label
                className="block text-xs font-medium text-slate-600"
                htmlFor={`${task}_ollama_model`}
              >
                Ollama model
              </label>
              <input
                id={`${task}_ollama_model`}
                aria-label={`${label} ollama model`}
                className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-900 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
                value={config.ollama_model}
                onChange={(e) =>
                  onChange({ ...config, ollama_model: e.target.value })
                }
              />
            </motion.div>
          )}
        </AnimatePresence>

        <div>
          <label
            className="block text-xs font-medium text-slate-600"
            htmlFor={`${task}_temp`}
          >
            Temperature
          </label>
          <input
            id={`${task}_temp`}
            type="number"
            min={0}
            max={1}
            step={0.05}
            className="mt-1 w-28 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-900 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
            value={config.temperature}
            onChange={(e) =>
              onChange({ ...config, temperature: parseFloat(e.target.value) })
            }
          />
        </div>
      </div>
    </section>
  )
}

function ConnectionSection({
  title,
  urlValue,
  onUrlChange,
  testMutation,
}: {
  title: string
  urlValue: string
  onUrlChange: (v: string) => void
  testMutation: ReturnType<typeof useTestLocalAI>
}) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5">
      <h3 className="mb-4 text-sm font-semibold text-slate-900">{title}</h3>
      <div className="flex gap-3">
        <input
          className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-900 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
          value={urlValue}
          onChange={(e) => onUrlChange(e.target.value)}
          placeholder="http://..."
        />
        <button
          onClick={() => testMutation.mutate(urlValue)}
          disabled={testMutation.isPending}
          className="rounded-lg border border-slate-200 px-4 py-2 text-sm text-slate-700 transition-colors hover:bg-slate-50 disabled:opacity-50"
        >
          {testMutation.isPending ? 'Testing...' : 'Test connection'}
        </button>
      </div>
      {testMutation.data && (
        <p
          className={`mt-2 text-xs ${testMutation.data.ok ? 'text-emerald-600' : 'text-red-600'}`}
        >
          {testMutation.data.ok
            ? `Connected — ${testMutation.data.models.join(', ')}`
            : testMutation.data.error}
        </p>
      )}
    </section>
  )
}

export function SettingsPage() {
  const { data } = useSettings()
  const save = useSaveSettings()
  const testLocalAI = useTestLocalAI()
  const testOllama = useTestOllama()

  const [localaiUrl, setLocalaiUrl] = useState('')
  const [ollamaUrl, setOllamaUrl] = useState('')
  const [tagger, setTagger] = useState<TaskConfig | null>(null)
  const [linker, setLinker] = useState<TaskConfig | null>(null)

  useEffect(() => {
    if (data) {
      setLocalaiUrl(data.localai_base_url)
      setOllamaUrl(data.ollama_base_url)
      setTagger(data.tagger)
      setLinker(data.linker)
    }
  }, [data])

  function handleSave() {
    if (!tagger || !linker) return
    const form = new FormData()
    form.set('localai_base_url', localaiUrl)
    form.set('ollama_base_url', ollamaUrl)
    form.set('tagger_backend', tagger.backend)
    form.set('tagger_anthropic_model', tagger.anthropic_model)
    form.set('tagger_localai_model', tagger.localai_model)
    form.set('tagger_ollama_model', tagger.ollama_model)
    form.set('tagger_temperature', String(tagger.temperature))
    form.set('linker_backend', linker.backend)
    form.set('linker_anthropic_model', linker.anthropic_model)
    form.set('linker_localai_model', linker.localai_model)
    form.set('linker_ollama_model', linker.ollama_model)
    form.set('linker_temperature', String(linker.temperature))
    save.mutate(form)
  }

  if (!tagger || !linker)
    return <p className="text-sm text-slate-400">Loading settings...</p>

  return (
    <motion.div
      className="mx-auto max-w-2xl"
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      <h1 className="mb-8 text-2xl font-bold tracking-tight text-slate-900">
        LLM Configuration
      </h1>

      <div className="flex flex-col gap-4">
        <ConnectionSection
          title="LocalAI Connection"
          urlValue={localaiUrl}
          onUrlChange={setLocalaiUrl}
          testMutation={testLocalAI}
        />
        <ConnectionSection
          title="Ollama Connection"
          urlValue={ollamaUrl}
          onUrlChange={setOllamaUrl}
          testMutation={testOllama}
        />

        <TaskSection
          task="tagger"
          label="Tagger"
          config={tagger}
          onChange={setTagger}
        />
        <TaskSection
          task="linker"
          label="Linker"
          config={linker}
          onChange={setLinker}
        />

        <div className="flex items-center gap-4">
          <button
            onClick={handleSave}
            disabled={save.isPending}
            className="rounded-xl bg-indigo-500 px-5 py-2.5 text-sm font-medium text-white shadow-sm transition-colors hover:bg-indigo-600 disabled:opacity-50"
            aria-label="Save configuration"
          >
            Save configuration
          </button>
          {save.isSuccess && (
            <p className="text-sm text-emerald-600">Saved.</p>
          )}
          {save.isError && (
            <p className="text-sm text-red-600">{save.error.message}</p>
          )}
        </div>
      </div>
    </motion.div>
  )
}

export const Route = createFileRoute('/settings')({ component: SettingsPage })
