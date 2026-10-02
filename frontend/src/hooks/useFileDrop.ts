import { useEffect, useState } from 'react'

export function useFileDrop(onFile: (file: File) => void) {
  const [active, setActive] = useState(false)

  useEffect(() => {
    let depth = 0
    const hasFiles = (event: DragEvent) =>
      Array.from(event.dataTransfer?.types ?? []).includes('Files')

    const onEnter = (event: DragEvent) => {
      if (!hasFiles(event)) return
      depth += 1
      setActive(true)
    }
    const onOver = (event: DragEvent) => {
      if (hasFiles(event)) event.preventDefault()
    }
    const onLeave = () => {
      depth -= 1
      if (depth <= 0) {
        depth = 0
        setActive(false)
      }
    }
    const onDrop = (event: DragEvent) => {
      event.preventDefault()
      depth = 0
      setActive(false)
      const file = event.dataTransfer?.files?.[0]
      if (file) onFile(file)
    }

    window.addEventListener('dragenter', onEnter)
    window.addEventListener('dragover', onOver)
    window.addEventListener('dragleave', onLeave)
    window.addEventListener('drop', onDrop)
    return () => {
      window.removeEventListener('dragenter', onEnter)
      window.removeEventListener('dragover', onOver)
      window.removeEventListener('dragleave', onLeave)
      window.removeEventListener('drop', onDrop)
    }
  }, [onFile])

  return active
}
