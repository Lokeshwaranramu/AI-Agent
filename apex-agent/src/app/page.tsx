'use client';

import { ChatInterface } from '@/components/ChatInterface';
import { Sidebar } from '@/components/Sidebar';

export default function Home() {
  const handleNewChat = async () => {
    await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reset: true }),
    });
    window.location.reload();
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar onNewChat={handleNewChat} />
      <main className="flex-1 flex flex-col min-w-0">
        <ChatInterface />
      </main>
    </div>
  );
}
