type LogoProps = {
    altura: number
    largura: number
}

function Logo({ altura, largura }: LogoProps) {
    return (
        <img src="/logo.png" style={{width: `${largura}px`, height: `${altura}px` }} />
    )
}

export default Logo
