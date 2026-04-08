import { ReactNode, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { X } from 'lucide-react'

interface ModalProps {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
}

export function Modal({ open, onClose, title, children }: ModalProps) {
  useEffect(() => {
    if (open) document.body.style.overflow = 'hidden'
    else document.body.style.overflow = ''
    return () => { document.body.style.overflow = '' }
  }, [open])

  if (!open) return null

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-beige-50 rounded-xl3 shadow-hover border border-beige-200 w-full max-w-lg max-h-[90vh] flex flex-col animate-fade-in">
        <div className="flex items-center justify-between px-6 py-4 border-b border-beige-200">
          <h2 className="font-display text-lg text-forest-500">{title}</h2>
          <button onClick={onClose} className="text-neutral-400 hover:text-forest-500 transition-colors">
            <X size={20} />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-6 py-5">
          {children}
        </div>
      </div>
    </div>,
    document.body
  )
}
