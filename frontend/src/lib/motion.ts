import type { Variants } from 'framer-motion'

export const pageVariants: Variants = {
  initial: { opacity: 0, x: 16 },
  animate: {
    opacity: 1,
    x: 0,
    transition: { type: 'spring', stiffness: 300, damping: 30 },
  },
  exit: { opacity: 0, x: -16 },
}

export const listVariants: Variants = {
  animate: { transition: { staggerChildren: 0.05 } },
}

export const itemVariants: Variants = {
  initial: { opacity: 0, y: 8 },
  animate: {
    opacity: 1,
    y: 0,
    transition: { type: 'spring', stiffness: 400, damping: 28 },
  },
}

export const overlayVariants: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { duration: 0.15 } },
  exit: { opacity: 0, transition: { duration: 0.1 } },
}

export const paletteVariants: Variants = {
  initial: { opacity: 0, y: -16, scale: 0.97 },
  animate: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { type: 'spring', stiffness: 400, damping: 30 },
  },
  exit: { opacity: 0, y: -8, scale: 0.97, transition: { duration: 0.1 } },
}
