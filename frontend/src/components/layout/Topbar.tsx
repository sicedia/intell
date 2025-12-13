
"use client"

import React from 'react';
import { Menu, Search, Bell } from 'lucide-react';
import { Button } from "@/shared/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/shared/components/ui/sheet";
import { Sidebar } from './Sidebar';

export function Topbar() {
    const [open, setOpen] = React.useState(false);

    return (
        <header className="h-16 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-[40] flex items-center px-4 md:px-6">
            <div className="md:hidden mr-4">
                <Sheet open={open} onOpenChange={setOpen}>
                    <SheetTrigger asChild>
                        <Button variant="ghost" size="icon">
                            <Menu className="h-5 w-5" />
                            <span className="sr-only">Toggle menu</span>
                        </Button>
                    </SheetTrigger>
                    <SheetContent side="left" className="p-0 w-[240px]">
                        <Sidebar onClose={() => setOpen(false)} />
                    </SheetContent>
                </Sheet>
            </div>

            <div className="flex-1 flex justify-end md:justify-between items-center">
                <div className="hidden md:flex items-center text-muted-foreground bg-muted/40 rounded-md px-3 py-1.5 w-64 text-sm border focus-within:ring-1">
                    <Search className="h-4 w-4 mr-2" />
                    <input
                        type="text"
                        placeholder="Search resources..."
                        className="bg-transparent border-none outline-none w-full placeholder:text-muted-foreground/70"
                    />
                </div>

                <div className="flex items-center gap-2">
                    <Button variant="ghost" size="icon" className="text-muted-foreground">
                        <Bell className="h-5 w-5" />
                    </Button>
                </div>
            </div>
        </header>
    );
}
