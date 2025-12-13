import { redirect } from "next/navigation";

export default async function HomePage({
  params,
}: {
  params: { locale: string };
}) {
  const { locale } = params;
  redirect(`/${locale}/dashboard`);
}
