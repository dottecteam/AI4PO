import type { Metadata } from "next";
import ChatBot from "./client"; 

export const metadata: Metadata = {
  title: "Assistente de IA",
  description: "Converse com a nossa IA da AI4PO."
};

export default function ChatBotPage() {
  return <ChatBot />;
}