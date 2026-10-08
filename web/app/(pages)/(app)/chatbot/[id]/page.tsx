import type { Metadata } from "next";
import ChatBot from "../client";

export const metadata: Metadata = {
  title: "Assistente de IA",
  description: "Converse com a nossa IA da AI4PO."
};

export default async function ChatBotConversaPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <ChatBot conversaIdInicial={Number(id)} />;
}