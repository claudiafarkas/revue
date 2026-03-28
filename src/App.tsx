import { Navigate, Route, Routes } from 'react-router-dom';
import { SiteFrame } from './components/SiteFrame';
import { HomePage } from './pages/HomePage';
import { JobPostingsPage } from './pages/JobPostingsPage';
import { ResumeUploadPage } from './pages/ResumeUploadPage';
import { ProcessingPage } from './pages/ProcessingPage';
import { ReportPage } from './pages/ReportPage';
import { NotFoundPage } from './pages/NotFoundPage';

function App() {
  return (
    <SiteFrame>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/postings" element={<JobPostingsPage />} />
        <Route path="/resume" element={<ResumeUploadPage />} />
        <Route path="/processing" element={<ProcessingPage />} />
        <Route path="/report" element={<ReportPage />} />
        <Route path="/home" element={<Navigate to="/" replace />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </SiteFrame>
  );
}

export default App;