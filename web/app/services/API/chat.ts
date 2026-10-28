const API_URL = "http://localhost:8000/api"

type SaveHandle = {
  createWritable: () => Promise<{
    write: (data: Blob) => Promise<void>
    close: () => Promise<void>
  }>
  remove?: () => Promise<void>
}

type WindowComSavePicker = Window & {
  showSaveFilePicker?: (options: {
    suggestedName?: string
    types?: { description: string; accept: Record<string, string[]> }[]
  }) => Promise<SaveHandle>
}

async function baixarBlob(id: number): Promise<Blob> {
  const res = await fetch(`${API_URL}/conversas/${id}/exportar-pdf/`, {
    credentials: "include",
  })
  if (!res.ok) throw new Error(`Erro ${res.status} ao exportar a conversa`)
  return res.blob()
}

export async function exportarConversaPDF(id: number) {
  const nome = `conversa-${id}.pdf`
  const picker = (window as WindowComSavePicker).showSaveFilePicker

  if (picker) {
    let handle: SaveHandle
    try {
      // precisa ser chamado direto no clique, antes de qualquer await demorado
      handle = await picker.call(window, {
        suggestedName: nome,
        types: [
          { description: "PDF", accept: { "application/pdf": [".pdf"] } },
        ],
      })
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return
      throw err
    }

    try {
      const blob = await baixarBlob(id)
      const writable = await handle.createWritable()
      await writable.write(blob)
      await writable.close()
    } catch (err) {
      await handle.remove?.().catch(() => {}) // não deixa um arquivo vazio no disco
      throw err
    }
    return
  }

  const blob = await baixarBlob(id)
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = nome
  a.click()
  URL.revokeObjectURL(url)
}
