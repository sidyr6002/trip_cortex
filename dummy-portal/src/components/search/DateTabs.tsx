import { ChevronLeft, ChevronRight, Calendar } from 'lucide-react';
import { cn } from "../../lib/utils";

const DATES = [
    { day: 'Wed, 16 Aug', price: 'US$ 62.00', active: false },
    { day: 'Thu, 17 Aug', price: 'US$ 62.00', active: false },
    { day: 'Fri, 18 Aug', price: 'US$ 62.00', active: false },
    { day: 'Sat, 19 Aug', price: 'US$ 62.00', active: false },
    { day: 'Sun, 20 Aug', price: 'US$ 62.00', active: true },
    { day: 'Mon, 21 Aug', price: 'US$ 62.00', active: false },
    { day: 'Tue, 22 Aug', price: 'US$ 62.00', active: false },
];

export default function DateTabs() {
    return (
        <div className="flex items-center gap-2 bg-white rounded-2xl p-2 shadow-sm border border-divider-light w-full mb-6 overflow-x-auto overflow-y-hidden" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
            <style dangerouslySetInnerHTML={{
                __html: `
                .date-tabs-container::-webkit-scrollbar {
                    display: none;
                }
            `}} />
            <button className="w-10 h-10 shrink-0 rounded-full border border-divider-light flex flex-col items-center justify-center hover:bg-surface-muted transition-colors ml-2 cursor-pointer">
                <ChevronLeft className="w-4 h-4 text-content-muted" />
            </button>
            <div className="flex-1 flex items-center justify-between min-w-max gap-2 px-2 date-tabs-container">
                {DATES.map((d, i) => (
                    <button
                        key={i}
                        className={cn(
                            "flex flex-col items-center justify-center py-2 px-4 rounded-xl transition-colors shrink-0 cursor-pointer",
                            d.active ? "bg-primary-50 border border-primary-100" : "hover:bg-surface-muted border border-transparent"
                        )}
                    >
                        <span className={cn("text-sm mb-1 font-medium", d.active ? "text-content" : "text-content-muted")}>{d.day}</span>
                        <span className={cn("text-xs font-semibold", d.active ? "text-primary" : "text-content-light")}>{d.price}</span>
                    </button>
                ))}
            </div>
            <button className="w-10 h-10 shrink-0 rounded-full border border-divider-light flex items-center justify-center hover:bg-surface-muted transition-colors mr-2 cursor-pointer">
                <ChevronRight className="w-4 h-4 text-content-muted" />
            </button>
            <button className="w-10 h-10 shrink-0 rounded-full border border-divider-light text-primary flex items-center justify-center hover:bg-primary-50 transition-colors mr-2 shadow-sm cursor-pointer">
                <Calendar className="w-4 h-4" />
            </button>
        </div>
    );
}
