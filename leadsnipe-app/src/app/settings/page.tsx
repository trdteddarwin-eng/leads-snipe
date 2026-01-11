'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import {
    User,
    Mail,
    Key,
    Bell,
    Shield,
    CheckCircle2,
} from 'lucide-react';

export default function SettingsPage() {
    const [activeTab, setActiveTab] = useState('profile');
    const [isSaving, setIsSaving] = useState(false);
    const [gmailStatus, setGmailStatus] = useState<{ connected: boolean; email?: string }>({ connected: false });

    const tabs = [
        { id: 'profile', name: 'Profile', icon: User },
        { id: 'integrations', name: 'Integrations', icon: Key },
        { id: 'notifications', name: 'Notifications', icon: Bell },
        { id: 'security', name: 'Security', icon: Shield },
    ];

    useEffect(() => {
        if (activeTab === 'integrations') {
            api.getGmailStatus().then(data => {
                setGmailStatus({ connected: data.gmail_connected, email: data.gmail_email });
            }).catch(console.error);
        }
    }, [activeTab]);

    const handleConnectGmail = async () => {
        try {
            const { auth_url } = await api.connectGmail();
            window.location.href = auth_url;
        } catch (e) {
            console.error(e);
        }
    };

    const handleSave = () => {
        setIsSaving(true);
        setTimeout(() => setIsSaving(false), 1500);
    };

    return (
        <div className="max-w-5xl mx-auto py-12 px-6 animate-fade-in space-y-12">
            <div className="border-b-[3px] border-black dark:border-white pb-8">
                <h1 className="text-4xl font-black uppercase tracking-tighter text-black dark:text-white">Settings_Config</h1>
                <p className="text-[10px] font-bold text-neutral-400 uppercase tracking-[0.2em] mt-2 font-mono">System_Preferences / Identity_Management</p>
            </div>

            <div className="flex flex-col md:flex-row gap-12">
                {/* Tabs Sidebar */}
                <aside className="w-full md:w-64 space-y-2">
                    {tabs.map((tab) => {
                        const Icon = tab.icon;
                        const isActive = activeTab === tab.id;
                        return (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`
                                    w-full flex items-center justify-between px-5 py-4 text-[10px] font-black uppercase tracking-widest transition-all font-mono border-2
                                    ${isActive
                                        ? 'bg-black text-white dark:bg-white dark:text-black border-black dark:border-white shadow-[4px_4px_0px_0px_rgba(0,0,0,0.1)]'
                                        : 'bg-white dark:bg-black text-neutral-400 border-neutral-100 dark:border-neutral-900 hover:border-black dark:hover:border-white hover:text-black dark:hover:text-white'
                                    }
                                `}
                            >
                                <div className="flex items-center gap-3">
                                    <Icon className="w-4 h-4" />
                                    <span>{tab.name}</span>
                                </div>
                                {isActive && <div className="w-1.5 h-1.5 bg-white dark:bg-black rounded-full" />}
                            </button>
                        );
                    })}
                </aside>

                {/* Content Area */}
                <div className="flex-1">
                    <div className="p-8 bg-white dark:bg-black border-2 border-black dark:border-white shadow-sm">
                        {activeTab === 'profile' && (
                            <div className="space-y-10">
                                <div className="space-y-8">
                                    <div className="flex items-center gap-8">
                                        <div className="w-24 h-24 bg-neutral-100 dark:bg-neutral-900 border-2 border-black dark:border-white flex items-center justify-center text-3xl font-black text-black dark:text-white">
                                            JD
                                        </div>
                                        <div>
                                            <button className="text-[10px] font-black uppercase tracking-widest bg-black text-white dark:bg-white dark:text-black px-6 py-3 hover:opacity-80 transition-all font-mono">
                                                Change_Avatar
                                            </button>
                                            <p className="text-[10px] font-bold text-neutral-400 uppercase tracking-tight mt-3 font-mono">ENCODING: JPG, PNG / MAX: 800KB</p>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                        <div className="space-y-3">
                                            <label className="text-[10px] font-black uppercase tracking-widest text-black dark:text-white font-mono">User_Identity</label>
                                            <input
                                                type="text"
                                                className="w-full bg-neutral-50 dark:bg-neutral-950 border-2 border-neutral-200 dark:border-neutral-800 px-5 py-4 text-sm font-bold text-black dark:text-white outline-none focus:border-black dark:focus:border-white transition-all uppercase font-mono"
                                                defaultValue="John Doe"
                                            />
                                        </div>
                                        <div className="space-y-3">
                                            <label className="text-[10px] font-black uppercase tracking-widest text-black dark:text-white font-mono">Protocol_Address</label>
                                            <input
                                                type="email"
                                                className="w-full bg-neutral-50 dark:bg-neutral-950 border-2 border-neutral-200 dark:border-neutral-800 px-5 py-4 text-sm font-bold text-black dark:text-white outline-none focus:border-black dark:focus:border-white transition-all font-mono"
                                                defaultValue="john@leadsnipe.ai"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeTab === 'integrations' && (
                            <div className="space-y-10">
                                <div className="border-b-2 border-neutral-100 dark:border-neutral-900 pb-6">
                                    <h3 className="text-xl font-black text-black dark:text-white uppercase tracking-tighter">External_Links</h3>
                                    <p className="text-[10px] font-bold text-neutral-400 mt-2 uppercase tracking-widest font-mono">Third_Party_Protocol / API_Hooks</p>
                                </div>

                                <div className="space-y-6">
                                    {/* Gmail Integration */}
                                    <div className="flex items-center justify-between p-8 border-2 border-neutral-100 dark:border-neutral-900 hover:border-black dark:hover:border-white transition-all group">
                                        <div className="flex items-center gap-6">
                                            <div className="w-12 h-12 bg-neutral-50 dark:bg-neutral-950 border-2 border-neutral-100 dark:border-neutral-900 group-hover:border-black dark:group-hover:border-white flex items-center justify-center text-black dark:text-white transition-all">
                                                <Mail className="w-6 h-6" />
                                            </div>
                                            <div>
                                                <p className="text-sm font-black uppercase tracking-widest text-black dark:text-white font-mono">
                                                    {gmailStatus.connected ? 'Workspace: ACTIVE' : 'Status: OFFLINE'}
                                                </p>
                                                <div className="flex items-center gap-3 mt-1.5">
                                                    <div className={`w-2 h-2 ${gmailStatus.connected ? 'bg-black dark:bg-white animate-pulse' : 'bg-neutral-200 dark:bg-neutral-800'}`}></div>
                                                    <span className="text-[10px] text-neutral-400 font-bold uppercase tracking-tight font-mono">
                                                        {gmailStatus.connected ? `${gmailStatus.email}` : 'UNCONNECTED'}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                        <button
                                            onClick={handleConnectGmail}
                                            className="text-[10px] font-black uppercase tracking-widest text-black dark:text-white border-2 border-black dark:border-white px-6 py-3 hover:bg-black hover:text-white dark:hover:bg-white dark:hover:text-black transition-all font-mono"
                                        >
                                            {gmailStatus.connected ? 'Refresh' : 'Connect'}
                                        </button>
                                    </div>

                                    {/* Anymailfinder API */}
                                    <div className="flex items-center justify-between p-8 border-2 border-neutral-100 dark:border-neutral-900 hover:border-black dark:hover:border-white transition-all group">
                                        <div className="flex items-center gap-6">
                                            <div className="w-12 h-12 bg-neutral-50 dark:bg-neutral-950 border-2 border-neutral-100 dark:border-neutral-900 group-hover:border-black dark:group-hover:border-white flex items-center justify-center text-black dark:text-white transition-all">
                                                <Key className="w-6 h-6" />
                                            </div>
                                            <div>
                                                <p className="text-sm font-black uppercase tracking-widest text-black dark:text-white font-mono">Verification_Protocol</p>
                                                <p className="text-[10px] text-neutral-400 font-bold mt-1.5 uppercase font-mono tracking-tight tracking-widest">Enrichment / Validation</p>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-4">
                                            <input
                                                type="password"
                                                className="bg-neutral-50 dark:bg-neutral-950 border-2 border-neutral-200 dark:border-neutral-800 px-4 py-3 text-xs w-40 font-bold text-black dark:text-white outline-none focus:border-black dark:focus:border-white transition-all font-mono"
                                                placeholder="API_KEY_NULL"
                                            />
                                            <button className="text-[10px] font-black uppercase tracking-widest text-black dark:text-white border-2 border-black dark:border-white px-6 py-3 hover:bg-black hover:text-white dark:hover:bg-white dark:hover:text-black transition-all font-mono">
                                                Authorize
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div className="mt-12 pt-8 border-t-2 border-neutral-100 dark:border-neutral-900 flex justify-end">
                            <button
                                onClick={handleSave}
                                disabled={isSaving}
                                className="bg-black dark:bg-white text-white dark:text-black font-black py-4 px-10 text-[10px] uppercase tracking-[0.2em] transition-all flex items-center gap-3 font-mono shadow-[6px_6px_0px_0px_rgba(0,0,0,0.1)] dark:shadow-[6px_6px_0px_0px_rgba(255,255,255,0.1)] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-none"
                            >
                                {isSaving ? (
                                    <>
                                        <div className="w-4 h-4 border-2 border-white dark:border-black border-t-transparent rounded-full animate-spin"></div>
                                        <span>Saving_State...</span>
                                    </>
                                ) : (
                                    <>
                                        <CheckCircle2 className="w-4 h-4" />
                                        <span>Commit_Changes</span>
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
