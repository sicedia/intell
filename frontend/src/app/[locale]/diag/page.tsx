
export default async function DiagPage({ params }: { params: Promise<{ locale: string }> }) {
    const { locale } = await params;
    return (
        <div className="p-10 font-bold text-2xl">
            Diagnostics:
            <br />
            Locale: {locale}
            <br />
            Timestamp: {new Date().toISOString()}
        </div>
    );
}
