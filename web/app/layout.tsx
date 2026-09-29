import type { Metadata } from "next";
import { Catamaran } from "next/font/google";
import "./globals.css";

const catamaran = Catamaran({
  subsets: ["latin"],
  variable: "--font-catamaran",
  display: 'swap',
});

export const metadata: Metadata = {
  title: {
    default: "AI4PO | Inteligência Artificial para Product Owners",
    template: "%s | AI4PO",
  },
  description: "Plataforma potencializada por IA para auxiliar Product Owners na gestão, criação de backlogs e condução de projetos de software com máxima eficiência.",
  keywords: [
    "Product Owner", 
    "PO", 
    "Inteligência Artificial", 
    "Gestão de Projetos", 
    "Scrum", 
    "Desenvolvimento de Software", 
    "Agile",
    "Backlog"
  ],
  authors: [{ name: "DotTec Team" }],
  openGraph: {
    title: "AI4PO | IA para Product Owners",
    description: "Eleve a gestão de projetos de software com o poder da Inteligência Artificial.",
    siteName: "AI4PO",
    locale: "pt_BR",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "AI4PO | IA para Product Owners",
    description: "Plataforma inteligente de auxílio na construção de projetos de software para POs.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="pt-BR"
      className={`${catamaran.variable} h-full antialiased font-sans`}
    >
      <body className="min-h-full flex flex-col bg-background text-foreground">
        {children}
      </body>
    </html>
  );
}