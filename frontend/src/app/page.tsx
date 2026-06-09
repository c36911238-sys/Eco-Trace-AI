import Link from 'next/link';
import { Leaf, ArrowRight } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-zinc-950 flex flex-col items-center justify-center p-4">
      <main className="max-w-3xl text-center space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-1000">
        <div className="flex justify-center mb-6">
          <div className="p-4 bg-green-100 dark:bg-green-900/30 rounded-full">
            <Leaf className="w-16 h-16 text-green-600 dark:text-green-400" />
          </div>
        </div>
        
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-gray-900 dark:text-white">
          EcoTrace <span className="bg-gradient-to-r from-green-500 to-emerald-600 bg-clip-text text-transparent">AI+</span>
        </h1>
        
        <p className="text-xl md:text-2xl text-muted-foreground font-medium max-w-2xl mx-auto">
          From Awareness to Action. The intelligent carbon tracking platform powered by Explainable AI and Digital Twins.
        </p>
        
        <div className="flex items-center justify-center gap-4 pt-8">
          <Link 
            href="/dashboard" 
            className="group flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-8 py-4 rounded-full font-bold text-lg shadow-lg hover:shadow-xl transition-all focus:ring-4 focus:ring-green-500/50 outline-none"
          >
            Enter Dashboard
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>
      </main>

      <footer className="absolute bottom-8 text-center text-sm text-muted-foreground">
        Empowering intelligent climate action. Accessible • Secure • Explainable.
      </footer>
    </div>
  );
}
