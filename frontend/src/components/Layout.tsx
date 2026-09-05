import React, { useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Navbar } from './Navbar';
import { resetDemo } from '../services/simulator';

export const Layout: React.FC = () => {
  const [resetting, setResetting] = useState(false);
  const navigate = useNavigate();

  const handleResetDemo = async () => {
    if (!window.confirm('Reset demo state? This will clear all recovery runs and re-seed 100 fresh realistic cases in the database.')) {
      return;
    }
    try {
      setResetting(true);
      await resetDemo();
      alert('Demo data successfully reset! Navigating to dashboard.');
      navigate('/');
      window.location.reload();
    } catch (err: any) {
      alert(`Reset failed: ${err.message}`);
    } finally {
      setResetting(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-[#0B1528] text-slate-100">
      <Sidebar onResetDemo={handleResetDemo} resetting={resetting} />
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar />
        <main className="flex-1 p-8 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
