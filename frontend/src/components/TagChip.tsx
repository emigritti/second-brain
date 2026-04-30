const TAG_COLORS = [
  'bg-indigo-50 text-indigo-700 border-indigo-200',
  'bg-emerald-50 text-emerald-700 border-emerald-200',
  'bg-amber-50 text-amber-700 border-amber-200',
  'bg-rose-50 text-rose-700 border-rose-200',
  'bg-sky-50 text-sky-700 border-sky-200',
]

function colorForTag(tag: string) {
  let h = 0
  for (const c of tag) h = (h * 31 + c.charCodeAt(0)) & 0xff
  return TAG_COLORS[h % TAG_COLORS.length]
}

interface Props {
  tag: string
}

export function TagChip({ tag }: Props) {
  return (
    <span
      className={`inline-block rounded-full border px-2.5 py-0.5 text-xs font-medium ${colorForTag(tag)}`}
    >
      {tag}
    </span>
  )
}
