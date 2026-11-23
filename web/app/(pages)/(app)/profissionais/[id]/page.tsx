import type { Metadata } from "next";
import PerfilProfissionalPagina from "./client";

export const metadata: Metadata = {
  title: "Perfil do profissional",
  description: "Projetos, papéis e competências do profissional."
};

export default function PerfilProfissionalPage() {
  return <PerfilProfissionalPagina />;
}
