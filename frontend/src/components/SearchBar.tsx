import { Search, ArrowRight } from "lucide-react";
import { useState } from "react";
import { motion } from "framer-motion";

interface SearchBarProps {
  onSearch: (query: string) => void;
  initialValue?: string;
  compact?: boolean;
}

const SearchBar = ({ onSearch, initialValue = "", compact = false }: SearchBarProps) => {
  const [query, setQuery] = useState(initialValue);
  const [focused, setFocused] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) onSearch(query.trim());
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <motion.div
        animate={focused ? { scale: compact ? 1 : 1.01 } : { scale: 1 }}
        transition={{ duration: 0.2 }}
        className={`glass-card relative flex items-center gap-3 rounded-xl transition-all duration-300 ${
          compact ? "px-4 py-2.5" : "px-5 py-4"
        } ${focused ? "glow-border-strong" : "glow-border"}`}
      >
        <Search className={`shrink-0 text-muted-foreground transition-colors ${focused ? "text-primary" : ""} ${compact ? "h-4 w-4" : "h-5 w-5"}`} />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder="Ask about any research topic…"
          className={`w-full bg-transparent font-light text-foreground placeholder:text-muted-foreground/60 focus:outline-none ${
            compact ? "text-sm" : "text-base md:text-lg"
          }`}
        />
        <button
          type="submit"
          className={`group shrink-0 rounded-lg gradient-btn font-medium text-primary-foreground transition-all hover:shadow-lg hover:shadow-primary/20 ${
            compact ? "px-3 py-1.5 text-xs" : "flex items-center gap-1.5 px-4 py-2 text-sm"
          }`}
        >
          Search
          {!compact && <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />}
        </button>
      </motion.div>
    </form>
  );
};

export default SearchBar;
