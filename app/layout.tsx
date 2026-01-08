import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { TabsProviderWrapper } from '@/components/TabsProviderWrapper'

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
})

export const metadata: Metadata = {
  title: 'Quantis v2',
  description: 'Application web Quantis v2',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="fr" className={inter.variable}>
      <body className={inter.className}>
        <TabsProviderWrapper>{children}</TabsProviderWrapper>
      </body>
    </html>
  )
}

