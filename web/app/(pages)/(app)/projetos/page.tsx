import type { Metadata } from "next";
import Projetos from "./client"; 

export const metadata: Metadata = {
  title: "Projetos",
  description: "Visão geral dos projetos e base de conhecimentos da AI4PO."
};

export default function ProjetosPage() {
  return <Projetos />;
}