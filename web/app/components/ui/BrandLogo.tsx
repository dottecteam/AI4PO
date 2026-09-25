import Image from "next/image";

interface BrandLogoProps {
  /** "large" exibe apenas a imagem grande. "small" exibe a imagem menor com os textos da marca. */
  variant?: "large" | "small";
  className?: string;
}

export function BrandLogo({ variant = "small", className = "" }: BrandLogoProps) {
  if (variant === "large") {
    return (
      <div className={className}>
        <Image
          src="/imageLogo.png"
          alt="Logo AI4PO"
          width={521}
          height={521}
          className="h-auto w-full object-contain"
          priority
        />
      </div>
    );
  }

  return (
    <div className={`flex flex-col items-center text-center ${className}`}>
      <Image
        src="/imageLogo.png"
        alt="AI4PO"
        width={56}
        height={56}
        className="mb-3"
      />
      <h1 className="text-2xl font-semibold text-white">AI4PO</h1>
      <p className="text-sm text-[#EF7541]">
        Gestão de Conhecimento e RAG Inteligente
      </p>
    </div>
  );
}