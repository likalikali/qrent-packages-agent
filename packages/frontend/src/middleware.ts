import createMiddleware from 'next-intl/middleware';
import { fallbackLocale, locales } from './i18n';

export default createMiddleware({
  // A list of all locales that are supported
  locales,

  // Used when no locale matches
  defaultLocale: fallbackLocale,

  // Always use locale prefix
  localePrefix: 'always',
});


export const config = {
  // Match only internationalized pathnames
  // Next.js doesn't support template literals in matcher, so we use hardcoded values
  matcher: ['/', '/(en|zh)/:path*'],
};
