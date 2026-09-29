import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Dashboard",
  description: "Visão geral da sua área de trabalho na AI4PO.",
};

export default function Dashboard() {
  return (
    <div className="flex flex-col items-center justify-center h-screen">
      <h1 className="text-4xl font-bold text-white">Dashboard</h1>
      <p className="text-lg text-gray-400">Bem-vindo ao painel de controle!</p>
    </div>
  );
}