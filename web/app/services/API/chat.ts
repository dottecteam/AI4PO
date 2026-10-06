import { api } from "./api"

export async function exportarConversaPDF(id: number) {
  const blob = await api.getBlob(`/conversas/${id}/exportar-pdf/`)
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = `conversa-${id}.pdf`
  a.click()
  URL.revokeObjectURL(url)
}
