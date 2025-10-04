'use client'

import { useState } from 'react'
import BlogPostCard from '@/components/BlogPostCard'

// Stub blog posts data
const allBlogPosts = [
  {
    id: 1,
    title: 'Finding Your Perfect Student Rental: A Complete Guide',
    author: 'Sarah Johnson',
    date: 'Oct 1, 2024',
    preview: 'Starting your search for student housing can be overwhelming. Learn the essential steps to find a rental that fits your budget, lifestyle, and academic needs. From understanding lease terms to evaluating neighborhoods...',
    imageUrl: 'https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=800&q=80',
    slug: '#'
  },
  {
    id: 2,
    title: 'Understanding Rental Agreements: What Students Need to Know',
    author: 'Michael Chen',
    date: 'Sep 28, 2024',
    preview: 'Rental agreements can be complex and confusing for first-time renters. This guide breaks down the key terms, clauses, and legal protections you should understand before signing any lease document...',
    imageUrl: 'https://images.unsplash.com/photo-1554995207-c18c203602cb?w=800&q=80',
    slug: '#'
  },
  {
    id: 3,
    title: 'Top 10 Things to Check Before Moving Into Your Rental',
    author: 'Emily Rodriguez',
    date: 'Sep 25, 2024',
    preview: 'Moving into a new rental requires careful inspection to avoid future disputes. Discover the essential checklist of items to verify, from appliances and utilities to security deposits and documentation...',
    imageUrl: 'https://images.unsplash.com/photo-1582268611958-ebfd161ef9cf?w=800&q=80',
    slug: '#'
  },
  {
    id: 4,
    title: 'Budget-Friendly Tips for Furnishing Your Student Apartment',
    author: 'David Park',
    date: 'Sep 22, 2024',
    preview: 'Furnishing your first apartment on a student budget doesn\'t have to be stressful. Explore creative and affordable ways to make your space comfortable and functional without breaking the bank...',
    imageUrl: 'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800&q=80',
    slug: '#'
  },
  {
    id: 5,
    title: 'How to Negotiate Rent Like a Pro',
    author: 'Jessica Taylor',
    date: 'Sep 19, 2024',
    preview: 'Rent negotiation is an art that can save you hundreds of dollars. Learn proven strategies and techniques to confidently negotiate rental prices with landlords while maintaining a positive relationship...',
    imageUrl: 'https://images.unsplash.com/photo-1560520653-9e0e4c89eb11?w=800&q=80',
    slug: '#'
  },
  {
    id: 6,
    title: 'Best Neighborhoods for Students in Major Cities',
    author: 'Alex Thompson',
    date: 'Sep 16, 2024',
    preview: 'Location matters when choosing student housing. We analyze the most student-friendly neighborhoods across major cities, considering factors like proximity to campus, safety, nightlife, and affordability...',
    imageUrl: 'https://images.unsplash.com/photo-1449844908441-8829872d2607?w=800&q=80',
    slug: '#'
  },
  {
    id: 7,
    title: 'Roommate Etiquette: Making Shared Living Work',
    author: 'Olivia Martinez',
    date: 'Sep 13, 2024',
    preview: 'Living with roommates can be challenging but rewarding. Discover essential communication strategies, boundary-setting techniques, and conflict resolution tips to create a harmonious living environment...',
    imageUrl: 'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800&q=80',
    slug: '#'
  },
  {
    id: 8,
    title: 'Understanding Renters Insurance: Is It Worth It?',
    author: 'Ryan Williams',
    date: 'Sep 10, 2024',
    preview: 'Renters insurance is often overlooked by students, but it can provide crucial protection for your belongings. Learn what it covers, how much it costs, and whether you really need it...',
    imageUrl: 'https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=800&q=80',
    slug: '#'
  },
  {
    id: 9,
    title: 'Energy-Saving Tips to Lower Your Utility Bills',
    author: 'Sophie Anderson',
    date: 'Sep 7, 2024',
    preview: 'High utility bills can strain your student budget. Explore practical and effective ways to reduce energy consumption in your rental, from simple habit changes to smart technology solutions...',
    imageUrl: 'https://images.unsplash.com/photo-1473341304170-971dccb5ac1e?w=800&q=80',
    slug: '#'
  },
  {
    id: 10,
    title: 'Moving Out: How to Get Your Security Deposit Back',
    author: 'James Lee',
    date: 'Sep 4, 2024',
    preview: 'Getting your full security deposit back requires proper planning and documentation. Follow our comprehensive guide to ensure you leave your rental in perfect condition and avoid unnecessary deductions...',
    imageUrl: 'https://images.unsplash.com/photo-1609767500458-d2a133f61cab?w=800&q=80',
    slug: '#'
  },
  {
    id: 11,
    title: 'Dealing with Maintenance Issues: Your Rights as a Tenant',
    author: 'Amanda White',
    date: 'Sep 1, 2024',
    preview: 'Know your rights when it comes to rental property maintenance. Learn how to properly report issues, what landlords are required to fix, and how to handle emergency situations effectively...',
    imageUrl: 'https://images.unsplash.com/photo-1581578731548-c64695cc6952?w=800&q=80',
    slug: '#'
  },
  {
    id: 12,
    title: 'The Ultimate Apartment Hunting Checklist',
    author: 'Chris Brown',
    date: 'Aug 29, 2024',
    preview: 'Never miss important details during apartment viewings again. Our comprehensive checklist covers everything from structural issues to neighborhood amenities, ensuring you make informed decisions...',
    imageUrl: 'https://images.unsplash.com/photo-1484154218962-a197022b5858?w=800&q=80',
    slug: '#'
  }
]

export default function Blog() {
  const [displayedPosts, setDisplayedPosts] = useState(allBlogPosts.slice(0, 6))
  const [isLoading, setIsLoading] = useState(false)

  const loadMorePosts = async () => {
    setIsLoading(true)

    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 500))

    const currentCount = displayedPosts.length
    const nextPosts = allBlogPosts.slice(currentCount, currentCount + 4)

    setDisplayedPosts([...displayedPosts, ...nextPosts])
    setIsLoading(false)
  }

  const hasMorePosts = displayedPosts.length < allBlogPosts.length

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-slate-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {/* Hero Section */}
        <div className="max-w-3xl mb-12">
          <h1 className="text-4xl sm:text-5xl font-bold text-slate-900 mb-4">
            Learn how to boost your rental search
          </h1>
          <p className="text-lg text-slate-600 leading-relaxed">
            Discover strategies to get your ideal rental properties with QRent. From search optimization and property evaluation to lease negotiation and move-in preparation, explore our resources and take control of your rental journey.
          </p>
        </div>

        {/* Blog Posts Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
          {displayedPosts.map((post) => (
            <BlogPostCard
              key={post.id}
              title={post.title}
              author={post.author}
              date={post.date}
              preview={post.preview}
              imageUrl={post.imageUrl}
              slug={post.slug}
            />
          ))}
        </div>

        {/* See More Button */}
        {hasMorePosts && (
          <div className="flex justify-center">
            <button
              onClick={loadMorePosts}
              disabled={isLoading}
              className="px-8 py-3 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Loading...' : 'See More'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
