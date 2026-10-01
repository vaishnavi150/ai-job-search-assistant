import { useState } from 'react';
import ResumeTab from '../components/tabs/ResumeTab';
import JobMatchTab from '../components/tabs/JobMatchTab';
import InterviewTab from '../components/tabs/InterviewTab';
import MockInterviewTab from '../components/tabs/MockInterviewTab';
import ApplicationsTab from '../components/tabs/ApplicationsTab';
import ChatTab from '../components/tabs/ChatTab';

const TABS = [
  { id: 'resume', label: '📄 Resume', component: ResumeTab },
  { id: 'match', label: '🎯 Match & Tailor', component: JobMatchTab },
  { id: 'interview', label: '💬 Interview Qs', component: InterviewTab },
  { id: 'mock', label: '🎤 Mock Interview', component: MockInterviewTab },
  { id: 'applications', label: '📊 Applications', component: ApplicationsTab },
  { id: 'chat', label: '🤖 AI Chat', component: ChatTab },
];

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('resume');
  const ActiveComponent = TABS.find((t) => t.id === activeTab).component;

  return (
    <div className="dashboard">
      <nav className="tab-bar">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>
      <main className="tab-content">
        <ActiveComponent />
      </main>
    </div>
  );
}
