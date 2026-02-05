import {
    LineChart,
    BarChart2,
    PieChart,
    Settings,
    Bell,
    Newspaper,
    BookOpen,
    Search,
    FlaskConical
} from "lucide-react";
import Link from 'next/link';

export default function Sidebar() {
    const navItems = [
        { name: 'Ana Sayfa', href: '/', icon: <LineChart size={20} /> },
        { name: 'Analiz', href: '/analysis', icon: <BarChart2 size={20} /> },
        { name: 'AI Tahminler', href: '/predictions', icon: <span className="text-cyan-400 font-bold text-xs">AI</span> },
        { name: 'Piyasa Derinliği', href: '/market-depth', icon: <BookOpen size={20} /> },
        { name: 'Hisse Tarama', href: '/market', icon: <Search size={20} /> },
        { name: 'Geriye Dönük Test', href: '/backtest', icon: <FlaskConical size={20} /> },
        { name: 'Portföy', href: '/portfolio', icon: <PieChart size={20} /> },
        { name: 'Ayarlar', href: '/settings', icon: <Settings size={20} /> },
    ];

    return (
        <div className="h-screen w-20 flex flex-col items-center bg-[var(--color-dash-surface)] border-r border-[var(--color-dash-border)] py-6 z-50">
            <div className="mb-10 text-cyan-400 font-bold text-2xl tracking-tighter">
                A<span className="text-white">I</span>T
            </div>

            <nav className="flex flex-col gap-6 w-full items-center">
                {navItems.map((item) => (
                    <Link
                        key={item.name}
                        href={item.href}
                        className="group relative flex items-center justify-center p-3 rounded-xl hover:bg-gray-800 transition-colors"
                    >
                        <div className="text-gray-400 group-hover:text-cyan-400 transition-colors duration-200">
                            {item.icon}
                        </div>
                        {/* Tooltip */}
                        <span className="absolute left-16 bg-gray-900 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50 pointer-events-none">
                            {item.name}
                        </span>
                    </Link>
                ))}
            </nav>

            <div className="mt-auto mb-4">
                <button className="p-3 text-gray-500 hover:text-red-400 transition-colors">
                    <Bell size={20} />
                </button>
            </div>
        </div>
    );
}
