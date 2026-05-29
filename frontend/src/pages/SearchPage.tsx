import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useUser, useAuth } from "@clerk/clerk-react";
import { useEffect, useState } from "react";
import SearchBar from "@/components/SearchBar";
import Navbar from "@/components/Navbar";
import AnimatedBackground from "@/components/AnimatedBackground";
import { recentSearches } from "@/data/mockData";
import { Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface SearchPageProps {
  darkMode: boolean;
  onToggleDark: () => void;
}

const SearchPage = ({ darkMode, onToggleDark }: SearchPageProps) => {
  const navigate = useNavigate();
  const { isSignedIn, user } = useUser();
  const { getToken } = useAuth();
  const { toast } = useToast();
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);

  useEffect(() => {
    if (!isSignedIn) {
      navigate("/");
      return;
    }

    const syncUserAndCreateChat = async () => {
      try {
        const token = await getToken();
        if (token) {
          await api.syncUser(token);
          const chat = await api.createChat(token);
          setCurrentChatId(chat.id);
        }
      } catch (error) {
        console.error("Failed to sync user or create chat:", error);
        toast({
          title: "Error",
          description: "Failed to initialize chat session",
          variant: "destructive",
        });
      }
    };

    syncUserAndCreateChat();
  }, [isSignedIn, navigate, getToken, toast]);

  const handleSearch = async (query: string) => {
    if (!currentChatId) {
      toast({
        title: "Error",
        description: "Chat session not ready",
        variant: "destructive",
      });
      return;
    }

    navigate(`/loading?q=${encodeURIComponent(query)}&chatId=${currentChatId}`);
  };

  return (
    <div className="relative min-h-screen">
      <AnimatedBackground />
      <Navbar darkMode={darkMode} onToggleDark={onToggleDark} />
      <div className="flex min-h-[calc(100vh-3.5rem)] flex-col items-center justify-center px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="w-full max-w-2xl"
        >
          <div className="mb-2 flex items-center justify-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            <span className="text-xs font-medium uppercase tracking-widest text-primary">
              AI-Powered Research
            </span>
          </div>
          <h2 className="mb-2 text-center text-3xl font-bold tracking-tight text-foreground md:text-4xl">
            Explore <span className="gradient-text">Research</span>
          </h2>
          <p className="mb-8 text-center text-sm text-muted-foreground">
            Ask a question or enter a research topic to discover papers and insights.
          </p>
          <SearchBar onSearch={handleSearch} />
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="mt-6 flex flex-wrap justify-center gap-2"
          >
            {recentSearches.map((s) => (
              <button
                key={s}
                onClick={() => handleSearch(s)}
                className="glass-card rounded-lg px-3.5 py-2 text-xs text-muted-foreground transition-all hover:text-foreground hover-lift"
              >
                {s}
              </button>
            ))}
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
};

export default SearchPage;
