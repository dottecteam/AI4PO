import type { Metadata } from "next";
import Profissionais from "./client";

export const metadata: Metadata = {
  title: "Profissionais",
  description: "Profissionais, competências e projetos da plataforma AI4PO."
};

export default function ProfissionaisPage() {
  return <Profissionais />;
}
