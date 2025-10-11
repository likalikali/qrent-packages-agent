import BlogPostContent from '@/components/BlogPostContent';
import { getBlogPost, getBlogPosts } from '@/lib/blog';
import type { Metadata } from 'next';
import { notFound } from 'next/navigation';

// 错误分析：
// 1. page.tsx 报错 “Cannot find name 'script'”。
// 2. 这是因为 React/Next.js 组件中应使用 <Script /> 或普通 JSX 元素 <script />，而不是直接写 'script' 变量名。
// 3. 你代码中的 <script> 标签写法是合法的，但类型推断有误（或 tsx 类型推断情况），最推荐采用 next/script 组件来插入结构化数据，避免水合警告及后续报错。

import Script from 'next/script';

interface PageProps {
  params: Promise<{
    slug: string;
    locale: string;
  }>;
}

export async function generateStaticParams() {
  const posts = await getBlogPosts();
  return posts.map((post) => ({
    slug: post.slug,
  }));
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const post = await getBlogPost(slug);

  if (!post) {
    return {
      title: 'Post Not Found',
    };
  }

  return {
    title: `${post.titleEn} | QRent Blog`,
    description: post.excerpt,
    keywords: post.keywords,
    authors: [{ name: 'QRent Team' }],
    openGraph: {
      title: post.titleEn,
      description: post.excerpt,
      type: 'article',
      publishedTime: post.datePublished,
      authors: ['QRent Team'],
    },
    twitter: {
      card: 'summary_large_image',
      title: post.titleEn,
      description: post.excerpt,
    },
  };
}

export default async function BlogPostPage({ params }: PageProps) {
  const { slug } = await params;
  const post = await getBlogPost(slug);

  if (!post) {
    notFound();
  }

  return (
    <>
      <Script
        id="blog-post-schema"
        type="application/ld+json"
        strategy="afterInteractive"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(post.schema) }}
      />
      <BlogPostContent post={post} />
    </>
  );
}
