'use client';

import { ReactNode, useState } from "react";

interface DropdownProps {
    label: string;
    children: ReactNode;
    onAdd?: () => void;
}

export default function DropdownSection({ label, children, onAdd }: DropdownProps) {
    const [open, setOpen] = useState(true);

    return (
        <div>
            <div className="flex justify-between items-center border-b border-white">
                <h2 className="text-xl text-white w-full hover:cursor-pointer" onClick={() => setOpen(!open)}>{label}</h2>
                <div className="flex">
                    {onAdd && (
                        <button
                            onClick={onAdd}
                            className="size-8 m-1 flex justify-center items-center hover:bg-black hover:opacity-70 hover:cursor-pointer rounded-full"
                        >
                            <svg
                                viewBox="0 0 24 24"
                                className="h-6 w-6 text-[#EF7541]"
                                fill="none"
                            >
                                <path
                                    d="M11.83 7.5v8.67M7.5 11.83h8.67M22.67 11.83a10.83 10.83 0 1 1-21.67 0 10.83 10.83 0 0 1 21.67 0Z"
                                    stroke="currentColor"
                                    strokeWidth="2"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                />
                            </svg>
                        </button>
                    )}
                </div>

                <button
                    onClick={() => setOpen(!open)}
                    className="size-8 m-1 flex justify-center items-center hover:bg-black hover:opacity-70 hover:cursor-pointer rounded-full"
                >
                    <svg
                        viewBox="0 0 16 10"
                        className={`w-4 h-2.5 text-[#EF7541] transition-transform ${open ? "rotate-180" : ""}`}
                        fill="none"
                    >
                        <path
                            d="M14.5 8L8 1.5L1.5 8"
                            stroke="currentColor"
                            strokeWidth="3"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        />
                    </svg>
                </button>

            </div>

            {open && (
                <div className="p-4">
                    {children}
                </div>
            )}
        </div>
    )
}