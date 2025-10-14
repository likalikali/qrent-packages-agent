import { redirect } from 'next/navigation';

type SearchParams = {
  q?: string
  page?: string
}

export default async function SearchPage({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const params = await searchParams;

  // Redirect to the locale-specific search page with query parameters
  const searchQuery = new URLSearchParams();
  if (params.q) searchQuery.set('q', params.q);
  if (params.page) searchQuery.set('page', params.page);

  const queryString = searchQuery.toString();
  const redirectUrl = `/en/search${queryString ? `?${queryString}` : ''}`;

  redirect(redirectUrl);
}



