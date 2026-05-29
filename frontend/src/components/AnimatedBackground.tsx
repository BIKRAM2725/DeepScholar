const AnimatedBackground = () => (
  <div className="fixed inset-0 -z-10 overflow-hidden">
    <div className="absolute inset-0 bg-grid opacity-30" />
    <div className="blob blob-delay-4 absolute -left-32 -top-32 h-96 w-96 rounded-full bg-primary/10 blur-3xl" />
    <div className="blob blob-delay-2 absolute -right-32 top-1/3 h-80 w-80 rounded-full bg-[hsl(262,83%,58%,0.08)] blur-3xl" />
    <div className="blob absolute -bottom-32 left-1/3 h-72 w-72 rounded-full bg-primary/5 blur-3xl" />
  </div>
);

export default AnimatedBackground;
