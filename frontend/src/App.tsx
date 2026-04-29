import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import Splash from "./pages/Splash";
import RunsList from "./pages/RunsList";
import NewRun from "./pages/NewRun";
import TurnView from "./pages/TurnView";
import Atlas from "./pages/Atlas";
import Manual from "./pages/Manual";
import NotFound from "./pages/NotFound.tsx";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Splash />} />
          <Route path="/runs" element={<RunsList />} />
          <Route path="/runs/new" element={<NewRun />} />
          <Route path="/runs/:id" element={<TurnView />} />
          <Route path="/runs/:id/atlas" element={<Atlas />} />
          <Route path="/manual" element={<Manual />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
