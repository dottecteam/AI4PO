import type { Metadata } from "next";
import Perfil from "./client";

export const metadata: Metadata = {
  title: "Meu perfil",
  description: "Seus dados na plataforma AI4PO."
};

export default function PerfilPage() {
  return <Perfil />;
}