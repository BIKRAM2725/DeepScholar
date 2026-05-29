import { BookOpen } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { SignIn, useUser } from "@clerk/clerk-react";
import { useEffect } from "react";
import AnimatedBackground from "@/components/AnimatedBackground";

const Login = () => {
  const navigate = useNavigate();
  const { isSignedIn } = useUser();

  useEffect(() => {
    if (isSignedIn) {
      navigate("/search");
    }
  }, [isSignedIn, navigate]);

  return (
    <div className="relative flex min-h-screen items-center justify-center px-4">
      <AnimatedBackground />
      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="glass-card glow-border w-full max-w-sm rounded-2xl p-8"
      >
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl gradient-btn shadow-lg shadow-primary/20">
            <BookOpen className="h-6 w-6 text-primary-foreground" />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-foreground">
            AI Research Assistant
          </h1>
          <p className="mt-1.5 text-sm text-muted-foreground">
            Search, summarize, and discover academic papers.
          </p>
        </div>

        <SignIn 
          routing="path" 
          path="/"
          signUpUrl="/sign-up"
          afterSignInUrl="/search"
        />
      </motion.div>
    </div>
  );
};

export default Login;
