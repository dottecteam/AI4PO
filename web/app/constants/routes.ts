interface RouteItem {
    label: string;
    href: string;
}

export const ROUTES = {
    AUTH: {
        LOGIN: { label: "Entrar", href: "/login" },
        REQUEST: { label: "Solicite acesso", href: "/solicite" },
    },

    APP: {
        PROJETOS: { label: "Projetos", href: "app/projetos/" },
        EPICOS: {label:"Epicos",href:"app/projetos<>"}
    },

    get appRoutesList(): RouteItem[] {
        return Object.values(this.APP);
    }
};

export const API_ENDPOINTS = {
    AUTH: {
        LOGIN: "/auth/login"
    },
    PROJETO: {
        EPICOS: "/api/epicos/",
        FEATURES: "/api/features/",
        PBIS: "/api/pbis/",
    },
};