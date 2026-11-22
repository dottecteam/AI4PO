import type { Metadata } from "next";
import Competencias from "./client";

export const metadata: Metadata = {
  title: "Competências",
  description: "Gerencie as competências e veja quem melhor se encaixa em cada uma."
};

export default function CompetenciasPage() {
  return <Competencias />;
}
