import { useEffect, useState } from "react";

export default function useDebounce<T>(valor: T, atraso = 300): T {
    const [valorAtrasado, setValorAtrasado] = useState(valor);

    // Seta um temporizador, espera o usuário terminar de digitar para atualizar o valor
    useEffect(() => {
        const timer = setTimeout(() => setValorAtrasado(valor), atraso);
        return () => clearTimeout(timer);
    }, [valor, atraso]);

    return valorAtrasado;
}