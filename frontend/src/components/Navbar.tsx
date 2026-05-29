import { BookOpen, Moon, Search, Sun, LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useClerk, useUser } from "@clerk/clerk-react";
import { useAuth } from "@clerk/clerk-react";
import { api } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface NavbarProps {
  darkMode: boolean;
  onToggleDark: () => void;
}

const Navbar = ({ darkMode, onToggleDark }: NavbarProps) => {
  const navigate = useNavigate();
  const { signOut } = useClerk();
  const { user } = useUser();
  const { getToken } = useAuth();
  const { toast } = useToast();

  const handleLogout = async () => {
    try {
      const token = await getToken();
      if (token) {
        await api.logout(token);
      }
      await signOut();
      navigate("/");
    } catch (error) {
      console.error("Logout error:", error);
      toast({
        title: "Error",
        description: "Failed to logout",
        variant: "destructive",
      });
    }
  };

  return (
    <nav className="glass sticky top-0 z-50">
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4 md:px-6">
        <button
          onClick={() => navigate("/search")}
          className="flex items-center gap-2.5 transition-opacity hover:opacity-80"
        >
          <div className="flex h-7 w-7 items-center justify-center rounded-lg gradient-btn">
            <BookOpen className="h-3.5 w-3.5 text-primary-foreground" />
          </div>
          <span className="text-sm font-semibold tracking-tight text-foreground">
            AI Research Assistant
          </span>
        </button>

        <div className="flex items-center gap-1">
          <button
            onClick={() => navigate("/search")}
            className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
            aria-label="Search"
          >
            <Search className="h-4 w-4" />
          </button>
          <button
            onClick={onToggleDark}
            className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
            aria-label="Toggle theme"
          >
            {darkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
          {user && (
            <div className="ml-1 flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-secondary text-xs font-medium text-foreground">
                {user.firstName?.[0] || user.emailAddresses[0]?.emailAddress[0]?.toUpperCase()}
              </div>
              <button
                onClick={handleLogout}
                className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                aria-label="Logout"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
