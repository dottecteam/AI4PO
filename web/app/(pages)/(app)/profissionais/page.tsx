import type { Metadata } from "next";
import Profissionais from "./client";

export const metadata: Metadata = {
  title: "Profissionais",
  description: "Busque profissionais por competência e cadastre novos."
};

export default function ProfissionaisPage() {
  return <Profissionais />;
}