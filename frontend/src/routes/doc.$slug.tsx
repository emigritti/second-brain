import { createFileRoute } from '@tanstack/react-router'
export const Route = createFileRoute('/doc/$slug')({ component: () => <div>Doc</div> })
