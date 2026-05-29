import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "@clerk/clerk-react";
import { useEffect, useState } from "react";
import LoadingSteps from "@/components/LoadingSteps";
import Navbar from "@/components/Navbar";
import AnimatedBackground from "@/components/AnimatedBackground";
import { api } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface LoadingPageProps {
  darkMode: boolean;
  onToggleDark: () => void;
}

const LoadingPage = ({ darkMode, onToggleDark }: LoadingPageProps) => {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const query = params.get("q") || "";
  const chatId = params.get("chatId") || "";
  const { getToken } = useAuth();
  const { toast } = useToast();
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    const sendQuery = async () => {
      if (!query || !chatId || isProcessing) return;

      setIsProcessing(true);
      try {
        const token = await getToken();
        if (!token) {
          navigate("/");
          return;
        }

        console.log("[LoadingPage] Sending query:", query);
        const result = await api.sendMessage(token, chatId, query, "query");
        console.log("[LoadingPage] Received result:", result);
        console.log("[LoadingPage] Result type:", typeof result);
        console.log("[LoadingPage] Result.response:", result.response);
        console.log("[LoadingPage] Result.response type:", typeof result.response);
        
        // Extract the response text - ensure it's a string
        let responseText = "";
        
        if (result.response) {
          if (typeof result.response === 'string') {
            responseText = result.response;
          } else if (typeof result.response === 'object') {
            // If it's an object, stringify it
            responseText = JSON.stringify(result.response);
            console.warn("[LoadingPage] Response was an object, stringified:", responseText.substring(0, 100));
          } else {
            responseText = String(result.response);
          }
        } else if (result.answer) {
          responseText = typeof result.answer === 'string' ? result.answer : String(result.answer);
        } else {
          console.error("[LoadingPage] No response or answer field found in result");
          responseText = "Error: No response received from server";
        }
        
        console.log("[LoadingPage] Final response text type:", typeof responseText);
        console.log("[LoadingPage] Final response text length:", responseText.length);
        console.log("[LoadingPage] Response text preview:", responseText.substring(0, Math.min(100, responseText.length)));
        
        setTimeout(() => {
          navigate(`/results?q=${encodeURIComponent(query)}&chatId=${chatId}&response=${encodeURIComponent(responseText)}`);
        }, 2000);
      } catch (error) {
        console.error("Failed to send message:", error);
        const errorMessage = error instanceof Error ? error.message : "Failed to process your query";
        
        toast({
          title: "Error",
          description: errorMessage,
          variant: "destructive",
          duration: 5000,
        });
        
        // Wait a bit before redirecting so user can see the error
        setTimeout(() => {
          navigate("/search");
        }, 3000);
      }
    };

    sendQuery();
  }, [query, chatId, getToken, navigate, toast, isProcessing]);

  return (
    <div className="relative min-h-screen">
      <AnimatedBackground />
      <Navbar darkMode={darkMode} onToggleDark={onToggleDark} />
      <LoadingSteps onComplete={() => {}} />
    </div>
  );
};

export default LoadingPage;
