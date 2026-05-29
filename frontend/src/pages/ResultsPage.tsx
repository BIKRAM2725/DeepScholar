import { useNavigate, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuth } from "@clerk/clerk-react";
import { useState } from "react";
import Navbar from "@/components/Navbar";
import SearchBar from "@/components/SearchBar";
import SummaryBox from "@/components/SummaryBox";
import AnimatedBackground from "@/components/AnimatedBackground";
import { Search, ExternalLink, FileText } from "lucide-react";
import { api } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface ResultsPageProps {
  darkMode: boolean;
  onToggleDark: () => void;
}

interface Source {
  title: string;
  url: string;
  number: number;
}

const ResultsPage = ({ darkMode, onToggleDark }: ResultsPageProps) => {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const query = params.get("q") || "";
  const chatId = params.get("chatId") || "";
  const response = params.get("response") || "";
  const { getToken } = useAuth();
  const { toast } = useToast();
  const [currentChatId, setCurrentChatId] = useState(chatId);

  // Debug logging
  console.log("[ResultsPage] Query:", query);
  console.log("[ResultsPage] Raw response:", response);
  console.log("[ResultsPage] Response type:", typeof response);
  
  // Parse the response if it's a JSON string
  let actualResponse = response;
  if (response.startsWith('{"response":') || response.startsWith('{')) {
    try {
      const parsed = JSON.parse(response);
      actualResponse = parsed.response || parsed.answer || response;
      console.log("[ResultsPage] Parsed response:", actualResponse);
    } catch (e) {
      console.error("[ResultsPage] Failed to parse JSON:", e);
    }
  }
  
  // Replace escaped newlines with actual newlines
  actualResponse = actualResponse.replace(/\\n/g, '\n');
  
  console.log("[ResultsPage] Final response:", actualResponse.substring(0, 200));

  const handleSearch = async (q: string) => {
    try {
      const token = await getToken();
      if (!token) {
        navigate("/");
        return;
      }

      let newChatId = currentChatId;
      if (!newChatId) {
        const chat = await api.createChat(token);
        newChatId = chat.id;
        setCurrentChatId(newChatId);
      }

      navigate(`/loading?q=${encodeURIComponent(q)}&chatId=${newChatId}`);
    } catch (error) {
      console.error("Failed to create chat:", error);
      toast({
        title: "Error",
        description: "Failed to start new search",
        variant: "destructive",
      });
    }
  };

  // Parse response to extract summary, key points, and sources
  const parseResponse = (text: string) => {
    console.log("[ResultsPage] Parsing response, length:", text.length);
    
    if (!text || text === '[object Object]') {
      console.error("[ResultsPage] Invalid response text:", text);
      return {
        summary: "Error: Unable to parse response",
        keyPoints: [],
        sources: [],
        fullText: text
      };
    }
    
    const lines = text.split('\n');
    
    // Find where "Sources" section starts
    const sourcesIndex = lines.findIndex(line => line.trim() === 'Sources');
    console.log("[ResultsPage] Sources index:", sourcesIndex);
    
    // Extract main content (before Sources)
    const mainContent = sourcesIndex > 0 ? lines.slice(0, sourcesIndex) : lines;
    
    // Extract sources
    const sources: Source[] = [];
    if (sourcesIndex > 0) {
      const sourceLines = lines.slice(sourcesIndex + 1);
      sourceLines.forEach(line => {
        // Match pattern: [1] Title — URL
        const match = line.match(/\[(\d+)\]\s+(.+?)\s+—\s+(https?:\/\/[^\s]+)/);
        if (match) {
          sources.push({
            number: parseInt(match[1]),
            title: match[2].trim(),
            url: match[3].trim()
          });
        }
      });
    }
    console.log("[ResultsPage] Extracted sources:", sources.length);
    
    // Extract summary (first paragraph)
    const summaryLines = mainContent.filter(line => {
      const trimmed = line.trim();
      return trimmed && !trimmed.match(/^\d+\./);
    });
    const summary = summaryLines.slice(0, 2).join(' ').trim() || "No summary available";
    console.log("[ResultsPage] Summary:", summary.substring(0, 100));
    
    // Extract key points (numbered items)
    const keyPoints: string[] = [];
    mainContent.forEach(line => {
      const match = line.match(/^\d+\.\s+(.+)/);
      if (match) {
        keyPoints.push(match[1].trim());
      }
    });
    console.log("[ResultsPage] Key points:", keyPoints.length);
    
    return { summary, keyPoints, sources, fullText: text };
  };

  const { summary, keyPoints, sources, fullText } = parseResponse(actualResponse);

  return (
    <div className="relative min-h-screen">
      <AnimatedBackground />
      <Navbar darkMode={darkMode} onToggleDark={onToggleDark} />
      <div className="mx-auto max-w-3xl px-4 py-6 md:px-6">
        <div className="mb-8">
          <SearchBar onSearch={handleSearch} initialValue={query} compact />
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mb-6 flex items-center gap-3"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
            <Search className="h-4 w-4 text-primary" />
          </div>
          <h1 className="text-xl font-bold text-foreground md:text-2xl">
            {query}
          </h1>
        </motion.div>

        <SummaryBox summary={summary} keyPoints={keyPoints} />

        {sources.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="mt-6"
          >
            <div className="glass-card rounded-xl p-6">
              <div className="mb-4 flex items-center gap-2">
                <div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary/10">
                  <FileText className="h-3.5 w-3.5 text-primary" />
                </div>
                <h2 className="text-sm font-semibold text-foreground">
                  Research Sources
                </h2>
                <span className="rounded-md bg-secondary px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
                  {sources.length}
                </span>
              </div>
              <div className="space-y-3">
                {sources.map((source, i) => (
                  <motion.a
                    key={i}
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.4 + i * 0.05 }}
                    className="group flex items-start gap-3 rounded-lg border border-border bg-secondary/30 p-4 transition-all hover:border-primary/30 hover:bg-secondary/50 hover-lift"
                  >
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-primary/15 text-xs font-bold text-primary">
                      {source.number}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-foreground group-hover:text-primary transition-colors line-clamp-2">
                        {source.title}
                      </p>
                      <p className="mt-1 text-xs text-muted-foreground truncate">
                        {source.url}
                      </p>
                    </div>
                    <ExternalLink className="h-4 w-4 shrink-0 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                  </motion.a>
                ))}
              </div>
            </div>
          </motion.div>
        )}

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-6"
        >
          <div className="glass-card rounded-xl p-6">
            <h2 className="mb-4 text-sm font-semibold text-foreground">
              Full Response
            </h2>
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <div 
                className="text-muted-foreground whitespace-pre-wrap leading-relaxed"
                style={{ 
                  wordBreak: 'break-word',
                  overflowWrap: 'anywhere',
                  maxWidth: '100%'
                }}
              >
                {fullText}
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default ResultsPage;
