import { User, Minus, Plus } from 'lucide-react';
import { Popover, PopoverContent, PopoverTrigger } from '../../ui/popover';

interface TravelerSelectorProps {
    adults: number;
    children: number;
    onAdultsChange: (n: number) => void;
    onChildrenChange: (n: number) => void;
}

export default function TravelerSelector({ adults, children, onAdultsChange, onChildrenChange }: TravelerSelectorProps) {
    return (
        <Popover>
            <PopoverTrigger asChild>
                <div className="flex items-center gap-4 p-4 lg:p-5 bg-white/70 border border-divider hover:border-primary-outline/50 hover:bg-white transition-all duration-300 w-full cursor-pointer rounded-2xl shadow-sm h-full">
                    <div className="bg-primary-50 w-10 h-10 rounded-full shrink-0 flex items-center justify-center">
                        <User className="w-5 h-5 text-primary-light" />
                    </div>
                    <div className="flex flex-col items-start min-w-0 text-left">
                        <span className="text-xs text-content-light mb-0.5 whitespace-nowrap">Travelers</span>
                        <span className="font-semibold text-content text-sm truncate w-full">
                            {adults} Adult{adults > 1 ? 's' : ''}{children > 0 ? `, ${children} Child${children > 1 ? 'ren' : ''}` : ''}
                        </span>
                    </div>
                </div>
            </PopoverTrigger>
            <PopoverContent className="w-64 p-4 rounded-2xl" align="center" onOpenAutoFocus={(e) => e.preventDefault()}>
                <div className="flex flex-col gap-4">
                    <div className="flex items-center justify-between">
                        <div className="flex flex-col">
                            <span className="font-medium text-sm">Adults</span>
                            <span className="text-xs text-content-muted">Age 12+</span>
                        </div>
                        <div className="flex items-center gap-3">
                            <button className="w-8 h-8 rounded-full border border-divider flex items-center justify-center hover:bg-surface-muted transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed" onClick={() => onAdultsChange(Math.max(1, adults - 1))} disabled={adults <= 1}>
                                <Minus className="w-4 h-4" />
                            </button>
                            <span className="w-4 text-center font-medium">{adults}</span>
                            <button className="w-8 h-8 rounded-full border border-divider flex items-center justify-center hover:bg-surface-muted transition-colors cursor-pointer" onClick={() => onAdultsChange(adults + 1)}>
                                <Plus className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                    <div className="flex items-center justify-between">
                        <div className="flex flex-col">
                            <span className="font-medium text-sm">Children</span>
                            <span className="text-xs text-content-muted">Age 2-11</span>
                        </div>
                        <div className="flex items-center gap-3">
                            <button className="w-8 h-8 rounded-full border border-divider flex items-center justify-center hover:bg-surface-muted transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed" onClick={() => onChildrenChange(Math.max(0, children - 1))} disabled={children <= 0}>
                                <Minus className="w-4 h-4" />
                            </button>
                            <span className="w-4 text-center font-medium">{children}</span>
                            <button className="w-8 h-8 rounded-full border border-divider flex items-center justify-center hover:bg-surface-muted transition-colors cursor-pointer" onClick={() => onChildrenChange(children + 1)}>
                                <Plus className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                </div>
            </PopoverContent>
        </Popover>
    );
}
