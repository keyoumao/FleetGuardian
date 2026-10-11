import { BrowserRouter, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import { FleetProvider } from "./data/store";
import AgentDetail from "./pages/AgentDetail";
import Agents from "./pages/Agents";
import HarnessDetail from "./pages/HarnessDetail";
import Harnesses from "./pages/Harnesses";
import Incidents from "./pages/Incidents";
import RepresentationAudit from "./pages/RepresentationAudit";
import LiveMonitor from "./pages/LiveMonitor";
import Overview from "./pages/Overview";
import Policies from "./pages/Policies";

export default function App() {
  return (
    <FleetProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<RepresentationAudit />} />
            <Route path="monitor" element={<LiveMonitor />} />
            <Route path="runtime" element={<Overview />} />
            <Route path="agents" element={<Agents />} />
            <Route path="agents/:id" element={<AgentDetail />} />
            <Route path="incidents" element={<Incidents />} />
            <Route path="policies" element={<Policies />} />
            <Route path="harnesses" element={<Harnesses />} />
            <Route path="harnesses/:id" element={<HarnessDetail />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </FleetProvider>
  );
}
