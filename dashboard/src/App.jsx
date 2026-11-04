import React, { useState, useEffect, useRef } from 'react';
import {
  Shield,
  ShieldAlert,
  Bot,
  Terminal,
  Activity,
  Users,
  Hash,
  Crown,
  Settings,
  RefreshCw,
  Bell,
  Search,
  MessageSquare,
  Sparkles,
  Volume2,
  Lock,
  CheckCircle2,
  Sliders,
  ChevronRight,
  ExternalLink,
  Copy,
  Check,
  Server,
  Cpu,
  Radio,
  Zap,
  Flame,
  Award,
  Layers,
  HelpCircle,
  X
} from 'lucide-react';

const INITIAL_MODULES = [
  {
    id: 'automod',
    name: 'Auto Moderation',
    category: 'Security',
    desc: 'Anti-spam, bad words, mass mention and invites filter protection.',
    status: 'ACTIVE',
    enabled: true,
    icon: Shield,
    color: 'emerald'
  },
  {
    id: 'tickets',
    name: 'Ticket System',
    category: 'Utility',
    desc: 'Interactive helpdesk with buttons, transcripts and staff claiming.',
    status: 'CONFIGURED',
    enabled: true,
    icon: MessageSquare,
    color: 'cyan'
  },
  {
    id: 'anti_nuke',
    name: 'Anti-Nuke Shield',
    category: 'Security',
    desc: 'Strict limits on channel/role deletion, mass kick and bot bans.',
    status: 'ACTIVE',
    enabled: true,
    icon: ShieldAlert,
    color: 'red'
  },
  {
    id: 'j2c',
    name: 'Join to Create',
    category: 'Utility',
    desc: 'Automated dynamic temporary voice channels with owner controls.',
    status: 'CONFIGURED',
    enabled: true,
    icon: Volume2,
    color: 'amber'
  },
  {
    id: 'chat_ia',
    name: 'AI Neural Assistant',
    category: 'Engagement',
    desc: 'Gemini conversational agent powered by neural natural speech.',
    status: 'ACTIVE',
    enabled: true,
    icon: Sparkles,
    color: 'purple'
  },
  {
    id: 'vip',
    name: 'VIP System Manager',
    category: 'Utility',
    desc: 'Automatic tier roles, VIP private call creation and custom embed colors.',
    status: 'ACTIVE',
    enabled: true,
    icon: Crown,
    color: 'amber'
  },
  {
    id: 'leveling',
    name: 'Leveling & XP',
    category: 'Engagement',
    desc: 'Gamify your community with chat/voice XP, rank cards and rewards.',
    status: 'ACTIVE',
    enabled: true,
    icon: Award,
    color: 'emerald'
  },
  {
    id: 'event_logs',
    name: 'Audit Event Logging',
    category: 'Security',
    desc: 'Real-time comprehensive logs for messages, moderation and roles.',
    status: 'ACTIVE',
    enabled: true,
    icon: Layers,
    color: 'cyan'
  }
];

const INITIAL_LOGS = [
  { time: '15:14:27 PM', tag: 'INIT', text: 'Dashboard connected to Cypher neural websocket pool...', level: 'cyan' },
  { time: '15:14:27 PM', tag: 'INFO', text: 'Fetching guild configs from primary edge database...', level: 'emerald' },
  { time: '15:14:28 PM', tag: 'DONE', text: 'Cache synchronised successfully across Vercel Global Edge.', level: 'emerald' },
  { time: '15:14:32 PM', tag: 'SECURITY', text: 'Trust Factor evaluated: 100% integrity (Admin privileges OK)', level: 'emerald' },
  { time: '15:15:01 PM', tag: 'AUTOMOD', text: 'Anti-Spam bucket initialized for guild EXE Community', level: 'amber' }
];

export default function App() {
  const [activeTab, setActiveTab] = useState('OVERVIEW');
  const [modules, setModules] = useState(INITIAL_MODULES);
  const [logs, setLogs] = useState(INITIAL_LOGS);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [copied, setCopied] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedModule, setSelectedModule] = useState(null);
  const [stats, setStats] = useState({
    members: 118,
    roles: 37,
    channels: 20,
    ping: 12,
    uptime: '99.98%'
  });
  const consoleBottomRef = useRef(null);

  // Auto-scroll console
  useEffect(() => {
    consoleBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // Periodic new live log simulation (real cyberpunk feel)
  useEffect(() => {
    const interval = setInterval(() => {
      const tags = [
        { tag: 'WEBSOCKET', text: 'Keep-alive ping ack from edge runner (11ms latency)', level: 'cyan' },
        { tag: 'AUDIT', text: 'Routine integrity scan: No anomalous permission escalation', level: 'emerald' },
        { tag: 'EVENT', text: 'Discord gateway heartbeat acknowledged: seq_id #49021', level: 'cyan' },
        { tag: 'NEURAL', text: 'Gemini cache ready for contextual voice & chat prompts', level: 'purple' }
      ];
      const randomLog = tags[Math.floor(Math.random() * tags.length)];
      const now = new Date().toLocaleTimeString('en-US', { hour12: true });

      setLogs((prev) => [
        ...prev.slice(-40),
        { time: `${now} PM`, tag: randomLog.tag, text: randomLog.text, level: randomLog.level }
      ]);
    }, 14000);

    return () => clearInterval(interval);
  }, []);

  const handleToggleModule = (id) => {
    setModules((prev) =>
      prev.map((mod) => {
        if (mod.id === id) {
          const nextState = !mod.enabled;
          const now = new Date().toLocaleTimeString('en-US', { hour12: true });
          setLogs((l) => [
            ...l,
            {
              time: `${now} PM`,
              tag: 'CONFIG',
              text: `Module [${mod.name}] toggled to ${nextState ? 'ENABLED' : 'DISABLED'} by Admin`,
              level: nextState ? 'emerald' : 'red'
            }
          ]);
          return {
            ...mod,
            enabled: nextState,
            status: nextState ? 'ACTIVE' : 'DISABLED'
          };
        }
        return mod;
      })
    );
  };

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => {
      setIsRefreshing(false);
      const now = new Date().toLocaleTimeString('en-US', { hour12: true });
      setLogs((l) => [
        ...l,
        { time: `${now} PM`, tag: 'SYNC', text: 'Manual sync completed: Guild state re-hashed.', level: 'emerald' }
      ]);
    }, 800);
  };

  const copyGuildId = () => {
    navigator.clipboard.writeText('1b94813872210b314f12');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const clearLogs = () => {
    setLogs([{ time: '00:00:00', tag: 'CLEARED', text: 'Console stream buffer cleared.', level: 'cyan' }]);
  };

  const filteredModules = modules.filter(
    (m) =>
      m.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.desc.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.category.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#070709] text-slate-200">
      {/* ─── SIDEBAR ────────────────────────────────────── */}
      <aside className="w-64 flex-shrink-0 flex flex-col border-r border-[#1e1e24] bg-[#0c0d12]">
        {/* Logo / Brand */}
        <div className="p-5 flex items-center gap-3 border-b border-[#1a1b22]">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-red-600 to-rose-950 p-[1px] shadow-lg shadow-red-950/40">
            <div className="w-full h-full bg-[#0d0e14] rounded-xl flex items-center justify-center">
              <span className="font-black text-xl tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-red-500 to-rose-400">
                Z
              </span>
            </div>
            <div className="absolute -inset-0.5 rounded-xl bg-red-600/30 blur-sm -z-10" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-extrabold text-base tracking-wider text-white">CYPHER</span>
              <span className="text-xs px-1.5 py-0.5 rounded font-black bg-red-600/20 text-red-400 border border-red-500/30">
                CV2
              </span>
            </div>
            <p className="text-[10px] text-zinc-500 tracking-widest uppercase font-semibold">NEURAL DASHBOARD</p>
          </div>
        </div>

        {/* Navigation */}
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
          {/* Main */}
          <div>
            <button
              onClick={() => setActiveTab('OVERVIEW')}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-semibold transition-all ${
                activeTab === 'OVERVIEW'
                  ? 'bg-red-600/15 text-red-400 border border-red-500/40 shadow-sm shadow-red-950/50'
                  : 'text-zinc-400 hover:text-white hover:bg-zinc-900/60'
              }`}
            >
              <Activity className="w-4 h-4 text-red-500" />
              <span>Overview</span>
            </button>
          </div>

          {/* Security Group */}
          <div>
            <p className="px-3 text-[11px] font-bold tracking-wider text-zinc-500 uppercase mb-2">Security</p>
            <div className="space-y-1">
              {[
                { id: 'ANTI-NUKE', label: 'Anti-Nuke', icon: ShieldAlert },
                { id: 'AUTOMOD', label: 'Automod', icon: Shield },
                { id: 'VERIFICATION', label: 'Verification', icon: Lock }
              ].map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition ${
                    activeTab === item.id
                      ? 'bg-red-600/15 text-red-400 border border-red-500/30'
                      : 'text-zinc-400 hover:text-white hover:bg-zinc-900/40'
                  }`}
                >
                  <item.icon className="w-3.5 h-3.5" />
                  <span>{item.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Engagement Group */}
          <div>
            <p className="px-3 text-[11px] font-bold tracking-wider text-zinc-500 uppercase mb-2">Engagement</p>
            <div className="space-y-1">
              {[
                { id: 'WELCOME', label: 'Welcome', icon: Users },
                { id: 'LEVELING', label: 'Leveling & XP', icon: Award },
                { id: 'AUTO_ROLE', label: 'Auto Role', icon: Sliders },
                { id: 'AUTO_REACT', label: 'Auto React', icon: Flame },
                { id: 'REACTION_ROLES', label: 'Reaction Roles', icon: Layers }
              ].map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition ${
                    activeTab === item.id
                      ? 'bg-red-600/15 text-red-400 border border-red-500/30'
                      : 'text-zinc-400 hover:text-white hover:bg-zinc-900/40'
                  }`}
                >
                  <item.icon className="w-3.5 h-3.5" />
                  <span>{item.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Utility Group */}
          <div>
            <p className="px-3 text-[11px] font-bold tracking-wider text-zinc-500 uppercase mb-2">Utility</p>
            <div className="space-y-1">
              {[
                { id: 'TICKETS', label: 'Tickets', icon: MessageSquare },
                { id: 'J2C', label: 'Join to Create', icon: Volume2 },
                { id: 'VIP', label: 'VIP System', icon: Crown },
                { id: 'CHAT_IA', label: 'AI Assistant', icon: Sparkles }
              ].map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition ${
                    activeTab === item.id
                      ? 'bg-red-600/15 text-red-400 border border-red-500/30'
                      : 'text-zinc-400 hover:text-white hover:bg-zinc-900/40'
                  }`}
                >
                  <item.icon className="w-3.5 h-3.5" />
                  <span>{item.label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* User Footer Profile */}
        <div className="p-3 border-t border-[#1a1b22] bg-[#090a0e]">
          <div className="flex items-center justify-between p-2 rounded-lg bg-zinc-900/50 border border-zinc-800/80">
            <div className="flex items-center gap-2.5">
              <div className="relative">
                <div className="w-8 h-8 rounded-full bg-red-600/20 border border-red-500/40 flex items-center justify-center font-bold text-red-400 text-xs">
                  DP
                </div>
                <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-emerald-500 border-2 border-[#090a0e]" />
              </div>
              <div>
                <p className="text-xs font-bold text-white leading-none">douglas.dev</p>
                <span className="text-[10px] font-semibold text-emerald-400 uppercase tracking-wider">ACTIVE OWNER</span>
              </div>
            </div>
            <button className="text-zinc-400 hover:text-red-400 transition p-1 rounded hover:bg-zinc-800" title="Configurações">
              <Settings className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* ─── MAIN CONTENT ─────────────────────────────────── */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Header Bar */}
        <header className="h-16 border-b border-[#1e1e24] bg-[#0c0d12]/90 backdrop-blur px-8 flex items-center justify-between z-10">
          <div className="flex items-center gap-4 w-96">
            <div className="relative w-full">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
              <input
                type="text"
                placeholder="Query neural network or command..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-1.5 text-xs bg-[#12131a] rounded-lg border border-zinc-800 text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-red-500/60 transition"
              />
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Global Edge Badge */}
            <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900/80 border border-zinc-800 text-xs">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span className="text-zinc-400 font-mono text-[11px]">Vercel Edge: 12ms</span>
            </div>

            {/* Notifications */}
            <button className="p-2 rounded-lg bg-zinc-900/60 border border-zinc-800 text-zinc-400 hover:text-white transition relative">
              <Bell className="w-4 h-4" />
              <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-red-500 rounded-full" />
            </button>

            {/* Profile Pill */}
            <div className="flex items-center gap-2 pl-2 border-l border-zinc-800">
              <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-red-600 to-rose-400 flex items-center justify-center text-xs font-black text-white shadow-sm">
                C
              </div>
              <span className="text-xs font-semibold text-zinc-300">ray.dev</span>
            </div>
          </div>
        </header>

        {/* Scrollable View */}
        <main className="flex-1 overflow-y-auto px-8 py-6 space-y-6">
          {/* Back to all servers link */}
          <div className="flex items-center gap-2 text-xs text-zinc-400 hover:text-red-400 cursor-pointer transition w-fit">
            <span>&larr;</span>
            <span>Back to all servers</span>
          </div>

          {/* ─── SERVER HEADER CARD (Exact Cypher/Zyrox style) ─── */}
          <div className="relative rounded-2xl bg-[#0f1017] border border-[#222430] p-6 shadow-2xl overflow-hidden">
            {/* Ambient Background Glow */}
            <div className="absolute top-0 right-0 w-96 h-96 bg-red-600/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />

            <div className="relative flex flex-col lg:flex-row lg:items-center justify-between gap-6">
              {/* Left Guild Info */}
              <div className="flex items-center gap-5">
                <div className="relative w-20 h-20 rounded-2xl bg-gradient-to-br from-[#1a1b26] to-[#0a0a0f] border border-zinc-700/60 p-1 shadow-inner flex items-center justify-center">
                  <div className="w-full h-full rounded-xl bg-[#12131c] flex items-center justify-center font-black text-2xl text-white tracking-widest border border-zinc-800">
                    EXE
                  </div>
                  {/* Status Indicator */}
                  <span className="absolute bottom-1 right-1 w-3.5 h-3.5 rounded-full bg-emerald-500 border-2 border-[#0f1017] shadow-sm shadow-emerald-500/50" />
                </div>

                <div className="space-y-1">
                  <div className="flex items-center gap-3">
                    <h1 className="text-2xl font-black text-white tracking-tight">EXE</h1>
                    <button
                      onClick={copyGuildId}
                      className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-[11px] font-mono text-zinc-400 hover:text-zinc-200 transition"
                      title="Copiar Guild ID"
                    >
                      <span>ID: 1b94813872210b314f12</span>
                      {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                    </button>
                  </div>
                  <p className="text-xs text-zinc-400 font-medium">Server Owner Dashboard</p>

                  {/* Counters */}
                  <div className="flex items-center gap-3 pt-2">
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-zinc-900/80 border border-zinc-800/80">
                      <Users className="w-3.5 h-3.5 text-zinc-400" />
                      <div>
                        <p className="text-[9px] uppercase font-bold text-zinc-500 leading-none">Members</p>
                        <p className="text-xs font-bold text-white leading-none mt-0.5">{stats.members}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-zinc-900/80 border border-zinc-800/80">
                      <Shield className="w-3.5 h-3.5 text-zinc-400" />
                      <div>
                        <p className="text-[9px] uppercase font-bold text-zinc-500 leading-none">Roles</p>
                        <p className="text-xs font-bold text-white leading-none mt-0.5">{stats.roles}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-zinc-900/80 border border-zinc-800/80">
                      <Hash className="w-3.5 h-3.5 text-zinc-400" />
                      <div>
                        <p className="text-[9px] uppercase font-bold text-zinc-500 leading-none">Channels</p>
                        <p className="text-xs font-bold text-white leading-none mt-0.5">{stats.channels}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-3">
                <button
                  onClick={handleRefresh}
                  className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white font-semibold text-xs tracking-wide shadow-lg shadow-red-950/60 transition active:scale-95"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
                  <span>Refresh</span>
                </button>

                <button className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-zinc-900 hover:bg-zinc-800 text-zinc-200 border border-zinc-800 font-semibold text-xs transition">
                  <Settings className="w-3.5 h-3.5 text-zinc-400" />
                  <span>Server Settings</span>
                </button>
              </div>
            </div>
          </div>

          {/* ─── QUICK NAVIGATION TABS (Pills) ────────────────── */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
            {[
              'OVERVIEW',
              'ANTI-NUKE',
              'AUTOMOD',
              'TICKETS',
              'VERIFICATION',
              'WELCOME',
              'INVITES',
              'AUTO ROLE',
              'REACTION ROLES',
              'JOIN TO CREATE'
            ].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider transition whitespace-nowrap ${
                  activeTab === tab
                    ? 'bg-gradient-to-r from-red-600 to-rose-600 text-white shadow-md shadow-red-950/40'
                    : 'bg-[#111218] text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900 border border-zinc-800/60'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* ─── DASHBOARD GRID (Modules + Stats + Terminal) ─── */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* LEFT 2 COLUMNS: ACTIVE MODULES */}
            <div className="lg:col-span-2 space-y-6">
              {/* Header */}
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-extrabold text-white">Active Modules</h2>
                  <p className="text-xs text-zinc-500">Enable or configure modules with real-time sync</p>
                </div>
                <span className="text-xs font-mono font-bold text-red-400 bg-red-950/40 px-2.5 py-1 rounded-md border border-red-800/40">
                  {modules.filter((m) => m.enabled).length}/{modules.length} ONLINE
                </span>
              </div>

              {/* Module Cards Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredModules.map((mod) => {
                  const Icon = mod.icon;
                  return (
                    <div
                      key={mod.id}
                      className={`relative rounded-xl p-4 transition-all border ${
                        mod.enabled
                          ? 'bg-[#0f1118] border-zinc-800 hover:border-red-500/40 shadow-sm'
                          : 'bg-[#0b0c10] border-zinc-900 opacity-60'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <div
                            className={`w-9 h-9 rounded-xl flex items-center justify-center ${
                              mod.enabled
                                ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                                : 'bg-zinc-900 text-zinc-600 border border-zinc-800'
                            }`}
                          >
                            <Icon className="w-4 h-4" />
                          </div>
                          <div>
                            <h3 className="text-sm font-bold text-white">{mod.name}</h3>
                            <span
                              className={`inline-block text-[9px] font-black uppercase tracking-wider px-2 py-0.5 rounded ${
                                mod.status === 'ACTIVE'
                                  ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/40'
                                  : mod.status === 'CONFIGURED'
                                  ? 'bg-cyan-950/60 text-cyan-400 border border-cyan-800/40'
                                  : 'bg-zinc-900 text-zinc-500 border border-zinc-800'
                              }`}
                            >
                              {mod.status}
                            </span>
                          </div>
                        </div>

                        {/* Toggle switch */}
                        <button
                          onClick={() => handleToggleModule(mod.id)}
                          className={`relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                            mod.enabled ? 'bg-red-600' : 'bg-zinc-800'
                          }`}
                        >
                          <span
                            className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                              mod.enabled ? 'translate-x-4' : 'translate-x-0'
                            }`}
                          />
                        </button>
                      </div>

                      <p className="text-xs text-zinc-400 mt-3 line-clamp-2 leading-relaxed">{mod.desc}</p>

                      <div className="mt-4 pt-3 border-t border-zinc-800/60 flex items-center justify-between text-xs">
                        <button
                          onClick={() => setSelectedModule(mod)}
                          className="text-zinc-400 hover:text-white flex items-center gap-1 font-semibold transition"
                        >
                          <span>Manage Settings</span>
                          <ChevronRight className="w-3.5 h-3.5" />
                        </button>
                        <span className="text-[10px] text-zinc-500 font-mono uppercase">{mod.category}</span>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* ─── SYSTEM CONSOLE (Terminal Cyberpunk) ─── */}
              <div className="rounded-xl bg-[#090a0f] border border-zinc-800 overflow-hidden shadow-2xl">
                {/* Console Header */}
                <div className="px-4 py-3 bg-[#0d0e14] border-b border-zinc-800/80 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Terminal className="w-4 h-4 text-red-500" />
                    <span className="font-mono text-xs text-zinc-300 font-bold">
                      System Console <span className="text-zinc-600 font-normal">| [&gt;_ guild_event_stream_184633872236634372]</span>
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="flex items-center gap-1 text-[10px] font-mono text-emerald-400 uppercase bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800/30">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                      Live Stream
                    </span>
                    <button
                      onClick={clearLogs}
                      className="text-[11px] text-zinc-400 hover:text-zinc-200 transition font-mono px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800"
                    >
                      Clear
                    </button>
                  </div>
                </div>

                {/* Console Body */}
                <div className="p-4 font-mono text-[11px] h-48 overflow-y-auto space-y-1.5 bg-[#07070a] text-zinc-300 select-text">
                  {logs.map((log, index) => (
                    <div key={index} className="flex items-start gap-2 leading-relaxed">
                      <span className="text-zinc-600 flex-shrink-0">{log.time}</span>
                      <span
                        className={`font-bold flex-shrink-0 px-1 rounded text-[10px] ${
                          log.level === 'emerald'
                            ? 'text-emerald-400 bg-emerald-950/40'
                            : log.level === 'cyan'
                            ? 'text-cyan-400 bg-cyan-950/40'
                            : log.level === 'amber'
                            ? 'text-amber-400 bg-amber-950/40'
                            : log.level === 'purple'
                            ? 'text-purple-400 bg-purple-950/40'
                            : 'text-red-400 bg-red-950/40'
                        }`}
                      >
                        [{log.tag}]
                      </span>
                      <span className="text-zinc-300 break-all">{log.text}</span>
                    </div>
                  ))}
                  <div ref={consoleBottomRef} />
                </div>
              </div>
            </div>

            {/* RIGHT COLUMN: DATABASE STATUS & TRUST FACTOR */}
            <div className="space-y-6">
              {/* 1. Database & Edge Status */}
              <div className="rounded-xl bg-[#0f1017] border border-zinc-800 p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-white">Database Status</h3>
                  <Server className="w-4 h-4 text-red-500" />
                </div>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  All guild data is encrypted and replicated across our high-performance edge network.
                </p>

                {/* Metrics */}
                <div className="space-y-3 pt-2">
                  <div className="flex items-center justify-between py-2 border-b border-zinc-800/60 text-xs">
                    <span className="text-zinc-400 flex items-center gap-2">
                      <Zap className="w-3.5 h-3.5 text-zinc-500" />
                      Uptime
                    </span>
                    <span className="font-mono font-bold text-white">{stats.uptime}</span>
                  </div>

                  <div className="flex items-center justify-between py-2 border-b border-zinc-800/60 text-xs">
                    <span className="text-zinc-400 flex items-center gap-2">
                      <Radio className="w-3.5 h-3.5 text-zinc-500" />
                      Sync Delay
                    </span>
                    <span className="font-mono font-bold text-emerald-400">{stats.ping}ms</span>
                  </div>

                  <div className="flex items-center justify-between py-2 text-xs">
                    <span className="text-zinc-400 flex items-center gap-2">
                      <Cpu className="w-3.5 h-3.5 text-zinc-500" />
                      Region
                    </span>
                    <span className="font-mono font-bold text-white">Global Edges</span>
                  </div>
                </div>
              </div>

              {/* 2. Security Context / Trust Factor */}
              <div className="rounded-xl bg-[#0f1017] border border-zinc-800 p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-white">Security Context</h3>
                  <Shield className="w-4 h-4 text-emerald-400" />
                </div>

                <div className="flex items-center gap-4 py-2">
                  {/* Gauge */}
                  <div className="relative w-16 h-16 flex-shrink-0 flex items-center justify-center">
                    <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
                      <path
                        className="text-zinc-800"
                        strokeWidth="3.5"
                        stroke="currentColor"
                        fill="none"
                        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                      />
                      <path
                        className="text-emerald-500"
                        strokeDasharray="100, 100"
                        strokeWidth="3.5"
                        strokeLinecap="round"
                        stroke="currentColor"
                        fill="none"
                        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                      />
                    </svg>
                    <span className="absolute font-mono font-black text-xs text-white">100%</span>
                  </div>

                  <div>
                    <h4 className="text-sm font-bold text-white">Trust Factor</h4>
                    <p className="text-[11px] text-zinc-400 mt-0.5 leading-relaxed">
                      Bot is fully authenticated with administrator privileges and zero detected vulnerabilities.
                    </p>
                  </div>
                </div>
              </div>

              {/* 3. Quick Bot Invite Card */}
              <div className="rounded-xl bg-gradient-to-br from-red-950/40 to-zinc-900 border border-red-900/40 p-5 space-y-3">
                <div className="flex items-center gap-2 text-red-400 font-bold text-xs uppercase tracking-wider">
                  <Bot className="w-4 h-4" />
                  <span>Cypher Bot Instance</span>
                </div>
                <h4 className="text-sm font-extrabold text-white">Need to reinvite or authorize extra scopes?</h4>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  Generate an OAuth2 administrator URL with Components V2 enabled.
                </p>
                <a
                  href="https://discord.com/oauth2/authorize?client_id=1409893963498848419&permissions=8&scope=bot%20applications.commands"
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white font-semibold text-xs transition shadow-md shadow-red-950/50"
                >
                  <span>Authorize Bot Scopes</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            </div>
          </div>
        </main>
      </div>

      {/* ─── MODAL DE CONFIGURAÇÃO DE MÓDULO ─────────────── */}
      {selectedModule && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#0f1118] border border-zinc-800 rounded-2xl w-full max-w-lg p-6 space-y-5 shadow-2xl relative animate-in fade-in zoom-in-95 duration-150">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-zinc-800 pb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-red-500/10 text-red-400 border border-red-500/20 flex items-center justify-center">
                  <selectedModule.icon className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-extrabold text-white">{selectedModule.name}</h3>
                  <p className="text-xs text-zinc-400">Configure parameters for guild EXE</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedModule(null)}
                className="p-1 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Fields */}
            <div className="space-y-4 text-xs">
              <div>
                <label className="block text-zinc-400 font-semibold mb-1">Status do Módulo</label>
                <div className="flex items-center gap-3 p-3 rounded-lg bg-zinc-900 border border-zinc-800">
                  <span className="font-bold text-white flex-1">Habilitar no Servidor</span>
                  <button
                    onClick={() => handleToggleModule(selectedModule.id)}
                    className={`relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                      selectedModule.enabled ? 'bg-red-600' : 'bg-zinc-800'
                    }`}
                  >
                    <span
                      className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                        selectedModule.enabled ? 'translate-x-4' : 'translate-x-0'
                      }`}
                    />
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-zinc-400 font-semibold mb-1">Canal de Notificações / Logs</label>
                <select className="w-full bg-zinc-900 border border-zinc-800 rounded-lg p-2.5 text-zinc-200 focus:outline-none focus:border-red-500">
                  <option>#geral (ID: 1087395292)</option>
                  <option>#comandos (ID: 1087395293)</option>
                  <option>#logs-auditoria (ID: 1087395294)</option>
                </select>
              </div>

              <div>
                <label className="block text-zinc-400 font-semibold mb-1">Cargo com Permissão de Bypass</label>
                <select className="w-full bg-zinc-900 border border-zinc-800 rounded-lg p-2.5 text-zinc-200 focus:outline-none focus:border-red-500">
                  <option>👑 Dono / Administrador</option>
                  <option>⚡ Staff Geral</option>
                  <option>💎 Membros VIP</option>
                </select>
              </div>
            </div>

            {/* Footer Buttons */}
            <div className="flex items-center justify-end gap-3 pt-3 border-t border-zinc-800">
              <button
                onClick={() => setSelectedModule(null)}
                className="px-4 py-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-zinc-300 font-semibold text-xs transition"
              >
                Cancelar
              </button>
              <button
                onClick={() => {
                  const now = new Date().toLocaleTimeString('en-US', { hour12: true });
                  setLogs((l) => [
                    ...l,
                    { time: `${now} PM`, tag: 'SAVE', text: `Settings saved for ${selectedModule.name}`, level: 'emerald' }
                  ]);
                  setSelectedModule(null);
                }}
                className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white font-semibold text-xs transition shadow-md shadow-red-950/50"
              >
                Salvar Configurações
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
