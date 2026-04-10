import { Navigate, Route, Routes } from "react-router-dom";
import { LoadingState } from "components/LoadingState";
import { useAuth, AuthProvider } from "hooks/useAuth";
import { AppShell } from "layouts/AppShell";
import { AgentsPage } from "pages/AgentsPage";
import { AuditLogsPage } from "pages/AuditLogsPage";
import { BotControlPage } from "pages/BotControlPage";
import { DashboardPage } from "pages/DashboardPage";
import { ForcePasswordChangePage } from "pages/ForcePasswordChangePage";
import { GroupDetailPage } from "pages/GroupDetailPage";
import { GroupsPage } from "pages/GroupsPage";
import { KnowledgeBasePage } from "pages/KnowledgeBasePage";
import { LoginPage } from "pages/LoginPage";
import { NotFoundPage } from "pages/NotFoundPage";
import { SettingsPage } from "pages/SettingsPage";

function AppRouter() {
  const { session, loading } = useAuth();

  if (loading) {
    return <LoadingState label="Sessiya tekshirilmoqda..." />;
  }

  const isAuthenticated = Boolean(session?.authenticated);
  const mustChangePassword = Boolean(session?.must_change_password);

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  if (mustChangePassword) {
    return <ForcePasswordChangePage />;
  }

  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/groups" element={<GroupsPage />} />
        <Route path="/groups/:groupId" element={<GroupDetailPage />} />
        <Route path="/agents" element={<AgentsPage />} />
        <Route path="/knowledge-base" element={<KnowledgeBasePage />} />
        <Route path="/bot-control" element={<BotControlPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/audit-logs" element={<AuditLogsPage />} />
      </Route>
      <Route path="/login" element={<Navigate to="/" replace />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  );
}
