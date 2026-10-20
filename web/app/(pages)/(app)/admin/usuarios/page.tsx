import type { Metadata } from "next";
import UsuariosAdmin from "./client";

export const metadata: Metadata = {
  title: "Administração",
  description: "Gerencie os logins dos POs da AI4PO."
};

export default function UsuariosAdminPage() {
  return <UsuariosAdmin />;
}