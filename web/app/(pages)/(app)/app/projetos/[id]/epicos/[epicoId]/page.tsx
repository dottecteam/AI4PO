export default async function PaginaEpico({ params }: { params: Promise<{ id: string }> }) {
    const { id } = await params
  
    return (
        <main>
            <p>id: {id}</p>
            Lorem ipsum dolor sit amet consectetur adipisicing elit. Officia enim optio, dolorem quas harum quae doloremque saepe, illo cum voluptas, quibusdam corporis molestiae veniam animi dolor amet fuga! Error, quis. Lorem ipsum, dolor sit amet consectetur adipisicing elit. Laboriosam odio vitae minima! Excepturi quisquam neque ad nostrum tempora nihil quae quis officiis ipsam? Recusandae quas ab incidunt sint consectetur aut! Lorem ipsum dolor sit amet consectetur adipisicing elit. Consectetur hic tempora suscipit beatae sapiente consequatur cum id obcaecati fugit voluptatibus. Adipisci, officia. Ea harum voluptate iste omnis rerum dignissimos. Veritatis.
        </main>
    )
}